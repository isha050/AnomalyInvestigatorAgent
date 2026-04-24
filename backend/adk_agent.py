import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai.types import Content, Part

from spend_analysis import analyze_spend
from data_loader import SPEND_DATA

# Step 2: Wrap your function as a tool
def spend_tool_func(channel: str, date: str) -> dict:
    return analyze_spend(SPEND_DATA, channel, date)

spend_tool = FunctionTool(func=spend_tool_func)

# Step 3: Create agent
agent = Agent(
    name="spend_agent",
    model="gemini-2.5-flash", # changed from gemini-1.0-pro as before to avoid 404
    instruction="""
You are a marketing analyst.
If the user asks about CPA changes, spend changes, or performance issues,
use the spend_tool_func to analyze spend.

IMPORTANT: The channel name must be exactly "Google" (capital G, no other words).
The date must be in YYYY-MM-DD format.

Then explain the result strictly as a bulleted list (1-2 points). Do not write paragraphs or summaries.
Do not guess. Always rely on tool output.
If a date and channel are present, you MUST call the tool.
Do not refuse unless the tool returns an error.
You MUST evaluate your domain if a date is present.
If no issue is found:
→ say "Spend is not a significant factor."
Do NOT return empty responses.
""",
    tools=[spend_tool]
)

# Step 4: Setup runner
session_service = InMemorySessionService()

runner = Runner(
    agent=agent,
    session_service=session_service,
    app_name="anomaly_app"
)

def main():
    # Step 5: Create session (IMPORTANT: async)
    asyncio.run(
        session_service.create_session(
            app_name="anomaly_app",
            user_id="user1",
            session_id="s1"
        )
    )

    # Step 6: Take user input
    query = input("Enter your query: ")

    message = Content(
        role="user",
        parts=[Part(text=query)]
    )

    # Step 7: Run agent
    for event in runner.run(
        user_id="user1",
        session_id="s1",
        new_message=message
    ):
        if event.is_final_response():
            print("\nAnalysis Result:")
            print(event.content.parts[0].text)

if __name__ == "__main__":
    main()
