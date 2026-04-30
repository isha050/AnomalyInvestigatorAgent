import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import asyncio
from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# Implemented with 'adk_agent' instead of 'spend_agent' for the spend Agent based on the previous generation step.
from adk_agent import agent as spend_agent
from creative_agent import creative_agent
from seasonal_agent import seasonal_agent
from competitor_agent import competitor_agent
from tech_agent import tech_agent

# Step 2: Create Parallel Agent
parallel_agent = ParallelAgent(
    name="parallel_investigator",
    sub_agents=[spend_agent, creative_agent, seasonal_agent, competitor_agent, tech_agent]
)

# Step 3: Create Synthesis Agent
synthesis_agent = Agent(
    name="synthesis_agent",
    model="gemini-2.5-flash",
    instruction="""
You are a senior marketing analyst performing root cause analysis.

You will receive:
1. Findings from 5 specialist agents: spend, creative, seasonality, competitor, tech
2. An MMM context block containing channel contribution percentages read from an external model

CRITICAL RULES:
- If MMM context is present and shows contribution percentages, treat them as statistical ground truth.
- Use the agent findings to explain WHY the MMM numbers moved, not to override them.
- If MMM context is unavailable, rely solely on agent signals ranked by magnitude of change.
- Do NOT write any statement about MMM being unavailable in your output — just adapt silently.
- ALL OUTPUT MUST BE IN BULLET POINTS. No paragraphs.

Output format (strictly follow this):

Most likely cause:
- <Primary driver — cite MMM contribution % if available, plus agent corroboration>

Secondary factors:
- <Second and third ranked contributors with reasoning>
- <or write: None>

Ruled out:
- <Factors with low MMM contribution or no agent signal>

Be decisive. No hedging. No contradictions. No speculation beyond the data.
"""
)

# Step 4: Combine using SequentialAgent
coordinator = SequentialAgent(
    name="coordinator",
    sub_agents=[parallel_agent, synthesis_agent]
)



def main():
    # ✅ FIX 2b: session_service is now local to main() only
    local_session_service = InMemorySessionService()
    local_runner = Runner(
        agent=coordinator,
        session_service=local_session_service,
        app_name="anomaly_system"
    )

    asyncio.run(
        local_session_service.create_session(
            app_name="anomaly_system",
            user_id="user1",
            session_id="s1"
        )
    )

    query = input("Enter your query: ")
    message = Content(role="user", parts=[Part(text=query)])

    final_output = None
    for event in local_runner.run(user_id="user1", session_id="s1", new_message=message):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_output = event.content.parts[0].text

    print("\nFinal Analysis:")
    print(final_output)

if __name__ == "__main__":
    main()
