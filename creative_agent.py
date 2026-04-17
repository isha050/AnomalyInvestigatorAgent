from dotenv import load_dotenv
load_dotenv()

import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai.types import Content, Part

from creative_analysis import analyze_creative
from data_loader import CREATIVE_DATA

# Step 2: Wrap function as tool
def creative_tool_func(channel: str, date: str) -> list:
    return analyze_creative(CREATIVE_DATA, channel, date)

creative_tool = FunctionTool(func=creative_tool_func)

# Step 3: Create agent
creative_agent = Agent(
    name="creative_agent",
    model="gemini-2.5-flash", # changed from gemini-1.0-pro to bypass SDK 404 error
    instruction="""
You are a marketing analyst specializing in ad creatives.

If the user asks about CTR drops, ad performance decline, or creative fatigue,
use the creative_tool_func.

If fatigue is detected:
→ clearly explain that creatives are aging and losing effectiveness.

If no fatigue is detected or data is insufficient:
→ say "Creative performance is not a significant factor."

Never mention missing data explicitly.

Provide your response strictly as a bulleted list (1-2 points). Do not write paragraphs or summaries.
Do not guess. Use tool output only.

If a date and channel are present, you MUST call the tool.
Do not refuse unless the tool returns an error.

You MUST evaluate your domain if a date is present.

If no issue is found:
→ say "Creative fatigue is not a significant factor."

Do NOT return empty responses.
""",
    tools=[creative_tool]
)

# Step 4: Runner setup
session_service = InMemorySessionService()

runner = Runner(
    agent=creative_agent,
    session_service=session_service,
    app_name="creative_app"
)

def main():
    # Step 5: Create session
    asyncio.run(
        session_service.create_session(
            app_name="creative_app",
            user_id="user1",
            session_id="s1"
        )
    )

    # Step 6: Input
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
            print("\nCreative Analysis:")
            print(event.content.parts[0].text)

if __name__ == "__main__":
    main()
