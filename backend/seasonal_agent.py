import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai.types import Content, Part

from seasonal_analysis import analyze_seasonality

# Step 2: Wrap function
def seasonal_tool_func(date: str) -> dict:
    return analyze_seasonality(date)

seasonal_tool = FunctionTool(func=seasonal_tool_func)

# Step 3: Agent
seasonal_agent = Agent(
    name="seasonal_agent",
    model="gemini-2.5-flash", # changed from gemini-1.0-pro to prevent 404
    instruction="""
You are a marketing analyst specializing in seasonality.

If the query includes a date, use seasonal_tool_func.

Rules:

* If a relevant event is detected → explain its possible impact.
* If no event → clearly say seasonality is NOT a significant factor.
* Do NOT say "data not available".
* Provide your response strictly as a bulleted list (1-2 points). Do not write paragraphs or summaries.
* Use tool output only.

If a date and channel are present, you MUST call the tool.
Do not refuse unless the tool returns an error.

You MUST evaluate your domain if a date is present.

If no issue is found:
→ say "Seasonality is not a significant factor."

Do NOT return empty responses.
""",
    tools=[seasonal_tool]
)

# Step 4: Runner + session (same as others)
session_service = InMemorySessionService()

runner = Runner(
    agent=seasonal_agent,
    session_service=session_service,
    app_name="seasonal_app"
)

def main():
    asyncio.run(
        session_service.create_session(
            app_name="seasonal_app",
            user_id="user1",
            session_id="s1"
        )
    )

    query = input("Enter your query: ")

    message = Content(
        role="user",
        parts=[Part(text=query)]
    )

    for event in runner.run(
        user_id="user1",
        session_id="s1",
        new_message=message
    ):
        if event.is_final_response():
            print("\nSeasonal Analysis:")
            print(event.content.parts[0].text)

if __name__ == "__main__":
    main()
