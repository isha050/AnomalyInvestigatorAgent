import os
from dotenv import load_dotenv
from spend_analysis import analyze_spend
from google.genai import Client

load_dotenv()

def main():
    from data_loader import SPEND_DATA

    data = SPEND_DATA

    channel = input("Enter channel (e.g. Google): ").strip()
    date = input("Enter date (YYYY-MM-DD): ").strip()

    # Step 3: Call function
    result = analyze_spend(data, channel, date)

    if "error" in result:
        print(result)
        return

    # Step 4: Create a prompt for the LLM
    prompt = f"""
You are a marketing analyst.

Use ONLY the provided data. Do NOT recalculate anything.

Data:
{result}

Tasks:
1. State what happened to spend.
2. Explain how this impacts CPA.

Keep it concise (2-3 lines).

You MUST evaluate your domain if a date is present.

If no issue is found:
→ say "Spend is not a significant factor."

Do NOT return empty responses.
"""

    # Step 5: Call the LLM
    client = Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    # Step 6: Output
    print(response.text)

if __name__ == "__main__":
    main()
