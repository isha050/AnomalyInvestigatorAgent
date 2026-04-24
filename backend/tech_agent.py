import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai.types import Content, Part

from tech_analysis import analyze_tech_performance

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Step 2: Tool
def tech_tool_func(date: str) -> dict:
    return analyze_tech_performance(date)

tech_tool = FunctionTool(func=tech_tool_func)

# Step 3: Agent
tech_agent = Agent(
    name="tech_agent",
    model="gemini-2.5-flash", # Used gemini-2.5-flash instead of 1.0-pro to prevent 404 error
    instruction="""
You are a marketing analyst focusing on conversion performance.

If a date is present, you MUST use tech_tool_func.

Rules:

* If CVR dropped significantly → explain that conversion issues likely contributed to higher CPA.
* If no drop → clearly say conversion performance is not a significant factor.
* Do NOT say "data not found".
* Use tool output only.
* Provide your response strictly as a bulleted list (1-2 points). Do not write paragraphs or summaries.

You MUST evaluate your domain if a date is present.

If no issue is found:
→ say "Technical performance is not a significant factor."

Do NOT return empty responses.
""",
    tools=[tech_tool]
)

# Step 4: Runner
session_service = InMemorySessionService()

runner = Runner(
    agent=tech_agent,
    session_service=session_service,
    app_name="tech_app"
)

def main():
    asyncio.run(
        session_service.create_session(
            app_name="tech_app",
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
            print("\nTech Analysis:")
            print(event.content.parts[0].text)

if __name__ == "__main__":
    main()
