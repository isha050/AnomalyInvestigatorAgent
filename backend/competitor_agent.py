import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai.types import Content, Part

from competitor_analysis import analyze_competitor_trend

# Step 2: Wrap function
def competitor_tool_func(date: str) -> dict:
    return analyze_competitor_trend(date)

competitor_tool = FunctionTool(func=competitor_tool_func)

# Step 3: Agent
competitor_agent = Agent(
    name="competitor_agent",
    model="gemini-2.5-flash", # changed from gemini-1.0-pro to prevent 404
    instruction="""
You are a marketing analyst specializing in market trends and competition.

If the query includes a date, you MUST use competitor_tool_func.

Rules:

* If a trend spike is detected → explain increased competition or demand.
* If no spike → clearly say external competition is NOT a significant factor.
* Do NOT say "data not available".
* Use tool output only.
* Provide your response strictly as a bulleted list (1-2 points). Do not write paragraphs or summaries.

You MUST evaluate your domain if a date is present.

If no issue is found:
→ say "Competitor trends are not a significant factor."

Do NOT return empty responses.
""",
    tools=[competitor_tool]
)

# Step 4: Runner + session
session_service = InMemorySessionService()

runner = Runner(
    agent=competitor_agent,
    session_service=session_service,
    app_name="competitor_app"
)

def main():
    asyncio.run(
        session_service.create_session(
            app_name="competitor_app",
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
            print("\nCompetitor Analysis:")
            print(event.content.parts[0].text)

if __name__ == "__main__":
    main()
