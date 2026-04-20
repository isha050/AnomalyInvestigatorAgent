from datetime import datetime
from data_loader import SEASONAL_EVENTS_DATA

def analyze_seasonality(date: str, events: dict = None) -> dict:
    if events is None:
        events = SEASONAL_EVENTS_DATA

    fmt = "%Y-%m-%d"
    try:
        target_dt = datetime.strptime(date, fmt)
    except ValueError:
        return {"error": "Invalid date format"}

    for event_date_str, event_name in events.items():
        event_dt = datetime.strptime(event_date_str, fmt)
        days_diff = (target_dt - event_dt).days
        if abs(days_diff) <= 3:
            return {
                "is_seasonal": True,
                "event": event_name,
                "days_from_event": days_diff,
                "reason": "Performance may be impacted by seasonal demand"
            }

    return {
        "is_seasonal": False,
        "event": None,
        "days_from_event": None,
        "reason": "No significant seasonal events nearby"
    }

if __name__ == "__main__":
    print("Testing 2024-01-01:")
    print(analyze_seasonality("2024-01-01"))

    print("\nTesting 2024-01-06:")
    print(analyze_seasonality("2024-01-06"))