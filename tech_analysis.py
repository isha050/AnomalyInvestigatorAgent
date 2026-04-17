from datetime import datetime, timedelta

from data_loader import CVR_DATA

def analyze_tech_performance(date: str) -> dict:
    cvr_data = CVR_DATA

    if date not in cvr_data:
        return {"error": "Date not found"}

    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format"}

    # Calculate recent 3 days (including the target date)
    recent_dates = [(target_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
    # Calculate baseline 3 days (prior to the recent window)
    baseline_dates = [(target_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3, 6)]

    recent_cvr = [cvr_data[d] for d in recent_dates if d in cvr_data]
    baseline_cvr = [cvr_data[d] for d in baseline_dates if d in cvr_data]

    if len(recent_cvr) < 3 or len(baseline_cvr) < 3:
        return {"error": "Insufficient data"}

    recent_avg = sum(recent_cvr) / 3
    baseline_avg = sum(baseline_cvr) / 3

    pct_change = ((recent_avg - baseline_avg) / baseline_avg) * 100
    is_tech_issue = pct_change < -15
    reason = "Conversion rate dropped significantly" if is_tech_issue else "No significant conversion rate drop detected"

    return {
        "cvr_change_pct": round(pct_change, 2),
        "is_tech_issue": is_tech_issue,
        "reason": reason
    }

if __name__ == "__main__":
    # Test
    result = analyze_tech_performance("2024-01-06")
    print("Test result for 2024-01-06:")
    print(result)
