import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from coordinator_agent import coordinator
from scenario_model import fit_channel_models, simulate_scenario, predict_cvr, get_channel_spend_history
import asyncio
import json
import anyio
import traceback
import time
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_service = InMemorySessionService()
runner = Runner(
    agent=coordinator,
    session_service=session_service,
    app_name="anomaly_system"
)

from data_loader import SPEND_DATA, CREATIVE_DATA, CVR_DATA, COMPETITOR_TREND_DATA

@app.get("/chart-data")
async def get_chart_data():
    def filter_google(dataset, value_key="spend"):
        seen_dates = set()
        result = []
        for row in dataset:
            if row.get("channel") == "Google" and row["date"] not in seen_dates:
                seen_dates.add(row["date"])
                result.append({"date": row["date"], "value": row[value_key]})
        result.sort(key=lambda x: x["date"])
        return result

    return {
        "spend": filter_google(SPEND_DATA, "spend"),
        "ctr": filter_google(CREATIVE_DATA, "ctr"),
        "cvr": [{"date": date, "value": val} for date, val in sorted(CVR_DATA.items())],
        "competitor": [{"date": date, "value": val} for date, val in sorted(COMPETITOR_TREND_DATA.items())]
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
                print(">>> runner.run() starting...")
                for event in runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=message
                ):
                    print(f">>> EVENT received: is_final={event.is_final_response()}")
                    if event.is_final_response() and event.content and event.content.parts:
                        text = event.content.parts[0].text
                        if text:
                            agent_name = getattr(event, "author", "unknown")
                            print(f">>> RESULT agent={agent_name} text={text[:80]}")
                            results.append({"agent": agent_name, "text": text})
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
            import traceback
            traceback.print_exc()
            yield {"event": "message", "data": json.dumps({"agent": "drilldown_agent", "text": f"Error: {str(e)}"})}

        yield {"event": "done", "data": json.dumps({"done": True})}

    return EventSourceResponse(event_generator())

from datetime import datetime
from auto_detector import detect_all_anomalies
from fastapi.responses import JSONResponse

@app.get("/auto-detect")
async def auto_detect():
    try:
        result = detect_all_anomalies(30)
        return {
            "anomalies": result,
            "scan_date": datetime.today().strftime("%Y-%m-%d"),
            "total_dates_scanned": 30
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/scenario-models")
async def get_scenario_models():
    try:
        models, skipped_channels = fit_channel_models(SPEND_DATA, CVR_DATA)
        
        # Add history to each model
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
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)