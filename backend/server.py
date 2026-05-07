import os
import httpx
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

LIFESIGHT_BASE = os.getenv("MMM_BASE_URL", "https://console-platform-stg.lifesight.io")

def _ls_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-moda-workspace": os.getenv("MMM_WORKSPACE", ""),
        "x-moda-apikey":    os.getenv("MMM_APIKEY", ""),
    }

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from coordinator_agent import coordinator
from scenario_model import fit_channel_models, simulate_scenario, predict_cvr, get_channel_spend_history
from mmm_client import get_mmm_contributions, format_mmm_for_agent
import asyncio
import json
import anyio
import traceback
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/mmm-status")
async def mmm_status():
    result = await anyio.to_thread.run_sync(get_mmm_contributions)
    if result is None:
        return {"status": "unavailable", "detail": "Check MMM env vars or API connectivity"}
    return {
        "status": "ok",
        "model_id": result["model_id"],
        "contributions": result["contributions"]
    }

session_service = InMemorySessionService()
runner = Runner(
    agent=coordinator,
    session_service=session_service,
    app_name="anomaly_system"
)

from data_loader import SPEND_DATA, CREATIVE_DATA, CVR_DATA, COMPETITOR_TREND_DATA

@app.get("/chart-data")
async def get_chart_data(channel: str = "Google"):
    def filter_by_channel(dataset, channel_name, value_key="spend"):
        seen_dates = set()
        result = []
        for row in dataset:
            if row.get("channel") == channel_name and row["date"] not in seen_dates:
                seen_dates.add(row["date"])
                result.append({"date": row["date"], "value": row[value_key]})
        result.sort(key=lambda x: x["date"])
        return result

    spend = filter_by_channel(SPEND_DATA, channel, "spend")
    ctr = filter_by_channel(CREATIVE_DATA, channel, "ctr")

    valid_dates = {item["date"] for item in spend}
    cvr = [{"date": date, "value": val} for date, val in sorted(CVR_DATA.items()) if date in valid_dates]
    competitor = [{"date": date, "value": val} for date, val in sorted(COMPETITOR_TREND_DATA.items()) if date in valid_dates]

    return {
        "spend": spend,
        "ctr": ctr,
        "cvr": cvr,
        "competitor": competitor
    }

@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    query = data.get("query")
    print(f"\n>>> ANALYZE called with query: {query}")

    async def event_generator():
        user_id = "user1"
        session_id = f"session_{abs(hash(query))}_{int(time.time()*1000)}"

        await session_service.create_session(
            app_name="anomaly_system",
            user_id=user_id,
            session_id=session_id
        )

        message = Content(role="user", parts=[Part(text=query)])

        def run_agents():
            results = []
            try:
                mmm_result = get_mmm_contributions()
                mmm_text = format_mmm_for_agent(mmm_result)

                memories = retrieve_similar(query, top_k=3)
                memory_text = format_memory_for_agent(memories)

                enriched_query = (
                    f"{query}\n\n"
                    f"--- ADDITIONAL CONTEXT FROM MMM MODEL ---\n"
                    f"{mmm_text}\n"
                    f"--- END MMM CONTEXT ---"
                )

                if memory_text:
                    enriched_query += f"\n\n{memory_text}"

                enriched_message = Content(role="user", parts=[Part(text=enriched_query)])

                print(">>> runner.run() starting...")
                synthesis_text = None

                for event in runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=enriched_message
                ):
                    print(f">>> EVENT received: is_final={event.is_final_response()}")
                    if event.is_final_response() and event.content and event.content.parts:
                        text = event.content.parts[0].text
                        if text:
                            agent_name = getattr(event, "author", "unknown")
                            print(f">>> RESULT agent={agent_name} text={text[:80]}")
                            results.append({"agent": agent_name, "text": text})
                            if agent_name == "synthesis_agent":
                                synthesis_text = text

                if synthesis_text:
                    import re
                    date_match = re.search(r"\d{4}-\d{2}-\d{2}", query)
                    channel_match = re.search(r"\b(Google|Meta|TikTok|Facebook)\b", query, re.IGNORECASE)
                    store_analysis(
                        query=query,
                        synthesis_text=synthesis_text,
                        date=date_match.group(0) if date_match else None,
                        channel=channel_match.group(0) if channel_match else None,
                        mmm_snapshot=mmm_text
                    )
                    send_investigation_alert(
                        query=query,
                        synthesis_text=synthesis_text,
                        date=date_match.group(0) if date_match else None,
                        channel=channel_match.group(0) if channel_match else None
                    )

                print(f">>> runner.run() done. {len(results)} results collected.")
            except Exception as e:
                print(f">>> AGENT ERROR: {e}")
                traceback.print_exc()
            return results

        results = await anyio.to_thread.run_sync(run_agents)
        print(f">>> Streaming {len(results)} results to client")

        for result in results:
            yield {
                "event": "message",
                "data": json.dumps(result)
            }

        yield {
            "event": "done",
            "data": json.dumps({"done": True})
        }

    return EventSourceResponse(event_generator())

@app.post("/drilldown")
async def drilldown(request: Request):
    data = await request.json()
    query = data.get("query")
    history = data.get("history", [])
    context = data.get("context", "")
    print(f"\n>>> DRILLDOWN called with query: {query}, history length: {len(history)}")

    async def event_generator():
        try:
            from google import genai
            from google.genai import types

            client = genai.Client()

            system_prompt = (
                f"You are a marketing analyst. The user ran this root cause analysis:\n\n"
                f"{context}\n\n"
                f"Answer follow-up questions based on this analysis. Be concise. Use bullet points."
            )

            messages = []
            for item in history:
                role = item.get("role", "user")
                text = item.get("text", "")
                if role == "assistant":
                    role = "model"
                messages.append(
                    types.Content(role=role, parts=[types.Part(text=text)])
                )
            messages.append(
                types.Content(role="user", parts=[types.Part(text=query)])
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
            )

            answer = response.text
            yield {"event": "message", "data": json.dumps({"agent": "drilldown_agent", "text": answer})}

        except Exception as e:
            traceback.print_exc()
            yield {"event": "message", "data": json.dumps({"agent": "drilldown_agent", "text": f"Error: {str(e)}"})}

        yield {"event": "done", "data": json.dumps({"done": True})}

    return EventSourceResponse(event_generator())

from analysis_memory import store_analysis, retrieve_similar, format_memory_for_agent
from slack_notifier import send_anomaly_alert, send_investigation_alert
from auto_detector import detect_all_anomalies
from fastapi.responses import JSONResponse

@app.get("/auto-detect")
async def auto_detect():
    try:
        result = detect_all_anomalies(30)
        scan_date = datetime.today().strftime("%Y-%m-%d")
        await anyio.to_thread.run_sync(
            lambda: send_anomaly_alert(result, scan_date, 30)
        )
        return {
            "anomalies": result,
            "scan_date": scan_date,
            "total_dates_scanned": 30,
            "multi_channel_dates": [
                a["date"] for a in result
                if a.get("correlation_type") == "multi_channel_event"
            ],
            "channels_scanned": sorted(list(set(
                item["channel"] for item in SPEND_DATA
            )))
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/scenario-models")
async def get_scenario_models():
    try:
        models, skipped_channels = fit_channel_models(SPEND_DATA, CVR_DATA)

        for channel in models:
            models[channel]["history"] = get_channel_spend_history(SPEND_DATA, channel, 30)

        total_historical_spend = sum(item["spend"] for item in SPEND_DATA)
        dates = [item["date"] for item in SPEND_DATA]
        channels = sorted(list(set(item["channel"] for item in SPEND_DATA)))

        return {
            "channels": channels,
            "models": models,
            "skipped_channels": skipped_channels,
            "total_historical_spend": total_historical_spend,
            "date_range": {
                "start": min(dates) if dates else None,
                "end": max(dates) if dates else None
            }
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/simulate")
async def simulate(request: Request):
    try:
        data = await request.json()
        allocations = data.get("allocations", {})
        baseline_date_str = data.get("baseline_date")

        models, _ = fit_channel_models(SPEND_DATA, CVR_DATA)

        all_dates = sorted(list(set(item["date"] for item in SPEND_DATA)))
        if not all_dates:
            return JSONResponse(status_code=400, content={"error": "No spend data available"})

        if not baseline_date_str or baseline_date_str not in all_dates:
            baseline_date_str = all_dates[-1]

        baseline_dt = datetime.strptime(baseline_date_str, "%Y-%m-%d")
        start_dt = baseline_dt - timedelta(days=7)

        baseline_allocs = {}
        channels = set(item["channel"] for item in SPEND_DATA)
        for channel in channels:
            channel_spend_in_window = [
                item["spend"] for item in SPEND_DATA
                if item["channel"] == channel and
                start_dt <= datetime.strptime(item["date"], "%Y-%m-%d") < baseline_dt
            ]
            baseline_allocs[channel] = sum(channel_spend_in_window) / 7.0 if channel_spend_in_window else 0.0

        scenario_details, scenario_summary = simulate_scenario(models, allocations)
        baseline_details, baseline_summary = simulate_scenario(models, baseline_allocs)

        conversion_change_pct = 0.0
        if baseline_summary["total_conversions"] > 0:
            conversion_change_pct = ((scenario_summary["total_conversions"] - baseline_summary["total_conversions"]) /
                                     baseline_summary["total_conversions"]) * 100

        cpa_change_pct = 0.0
        if baseline_summary["blended_cpa"] > 0:
            cpa_change_pct = ((scenario_summary["blended_cpa"] - baseline_summary["blended_cpa"]) /
                              baseline_summary["blended_cpa"]) * 100

        recommendation = f"Scenario results in a {abs(cpa_change_pct):.1f}% {'improvement' if cpa_change_pct < 0 else 'increase'} in blended CPA."
        if conversion_change_pct > 0:
            recommendation += f" Total conversions are expected to increase by {conversion_change_pct:.1f}%."
        elif conversion_change_pct < 0:
            recommendation += f" Total conversions are expected to decrease by {abs(conversion_change_pct):.1f}%."

        delta_data = {
            "cpa_change_pct": cpa_change_pct,
            "conversion_change_pct": conversion_change_pct,
            "recommendation": recommendation
        }

        narration = None
        try:
            from google import genai
            from google.genai import types
            client = genai.Client()

            system_prompt = "You are a senior marketing analyst. Be concise, specific, and decisive. No hedging. Use bullet points."
            user_prompt = f"""
A user ran a budget scenario simulation. Here are the results:

SCENARIO ALLOCATION:
{json.dumps(scenario_details, indent=2)}

BASELINE (recent historical average):
{json.dumps(baseline_details, indent=2)}

DELTA:
- CPA change: {delta_data['cpa_change_pct']:+.1f}%
- Conversion change: {delta_data['conversion_change_pct']:+.1f}%

Write a 3-5 bullet analysis:
- Which channel benefits most from this allocation
- Which channel is being under or over-funded relative to its efficiency
- Whether this scenario is better or worse than baseline and by how much
- One specific recommended adjustment to improve the scenario further
"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[types.Content(role="user", parts=[types.Part(text=user_prompt)])],
                config=types.GenerateContentConfig(system_instruction=system_prompt)
            )
            narration = response.text
        except Exception as e:
            print(f"Narration generation failed: {e}")

        return {
            "scenario": scenario_details,
            "scenario_summary": scenario_summary,
            "baseline": baseline_details,
            "baseline_summary": baseline_summary,
            "delta": delta_data,
            "narration": narration
        }
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Causal DAG endpoints ──────────────────────────────────────────────────────

@app.get("/causal-dag-settings")
async def get_causal_dag_settings(dagType: str = "MMM"):
    url = f"{LIFESIGHT_BASE}/api/v1/account/settings/causal-dag"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, headers=_ls_headers(), params={"dagType": dagType})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching causal-dag-settings: {e}")
        return {
            "data": None,
            "success": False,
            "errors": [str(e)],
            "_fallback": True,
            "config": {
                "id": None,
                "models": [],
                "dagGenerationStrategy": "AUTO",
                "dagGenerationStatus": "PENDING",
                "dagGenerationFailureReason": None,
                "dagType": "MMM",
                "lastUpdatedAt": None,
            },
        }

@app.post("/causal-dag-settings")
async def post_causal_dag_settings(request: Request):
    url = f"{LIFESIGHT_BASE}/api/v1/account/settings/causal-dag"
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(url, headers=_ls_headers(), json=body)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error posting causal-dag-settings: {e}")
        return {"success": False, "errors": [str(e)], "_fallback": True}

@app.get("/causal-dag-graph")
async def get_causal_dag_graph(modelId: str = ""):
    url = f"{LIFESIGHT_BASE}/mmm/causal-dag"
    params = {"modelId": modelId} if modelId else {}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, headers=_ls_headers(), params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching causal-dag-graph: {e}")
        return {"data": None, "success": False, "errors": [str(e)]}


async def scheduled_scan():
    print("[scheduler] running scheduled anomaly scan")
    try:
        result = detect_all_anomalies(30)
        scan_date = datetime.today().strftime("%Y-%m-%d")
        send_anomaly_alert(result, scan_date, 30)
        print(f"[scheduler] scan complete, {len(result)} anomalies found")
    except Exception as e:
        print(f"[scheduler] scan failed: {e}")


@app.on_event("startup")
async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduled_scan,
        trigger="cron",
        hour=9,
        minute=0,
        timezone="Asia/Kolkata"
    )
    scheduler.start()
    print("[scheduler] started - daily scan at 09:00 IST")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)