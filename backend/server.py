import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from coordinator_agent import coordinator
import asyncio
import json
import anyio
import traceback

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
        session_id = f"session_{abs(hash(query))}"

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)