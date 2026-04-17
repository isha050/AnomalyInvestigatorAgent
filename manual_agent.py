from spend_analysis import analyze_spend
from google.genai import Client
from dotenv import load_dotenv
import re

load_dotenv()

def main():
    from data_loader import SPEND_DATA
    data = SPEND_DATA

    # Step 3: Take user input
    query = input("Enter your query: ")
    query_lower = query.lower()

    # Step 4: Extract channel
    if "Google" in query or "google" in query_lower:
        channel = "Google"
    elif "Meta" in query or "meta" in query_lower:
        channel = "Meta"
    else:
        print("Error: Channel not found in query")
        return

    # Step 5: Extract date using regex
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", query)
    if not date_match:
        print("Error: Date not found in query")
        return
    date = date_match.group(0)

    # Step 6: Decision logic
    keywords = ["cpa", "spend", "increase", "drop"]
    if any(k in query_lower for k in keywords):
        # Step 7: Call function
        result = analyze_spend(data, channel, date)
        if "error" in result:
            print(result)
            return
            
        # Step 8: Create prompt
        prompt = f"""
You are a marketing analyst.

Use ONLY the provided data. Do NOT recalculate anything.

Data:
{result}

Tasks:
1. State what happened to spend.
2. Explain how this COULD impact CPA (do not assume exact formula behavior).

Keep it concise (2-3 lines).

You MUST evaluate your domain if a date is present.

If no issue is found:
→ say "Spend is not a significant factor."

Do NOT return empty responses.
"""
        
        # Step 9: Call LLM
        client = Client()
        # Changed to gemini-2.5-flash as gemini-1.0-pro is not supported in the SDK API.
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Step 10: Print output
        print("\nAnalysis Result:")
        print(response.text)
    else:
        print("I can only analyze spend-related issues right now")

if __name__ == "__main__":
    main()
