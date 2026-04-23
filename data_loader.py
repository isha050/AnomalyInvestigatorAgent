import os
from bigquery_tool import query_bigquery

def _load_spend_data():
    result = query_bigquery("SELECT * FROM marketing_data.spend_data")
    if "error" in result:
        print(f"Error loading spend data: {result['error']}")
        return []
    
    data = []
    for row in result["rows"]:
        data.append({
            "date": row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"]),
            "channel": row["channel"],
            "spend": float(row["spend"])
        })
    return data

def _load_creative_data():
    result = query_bigquery("SELECT * FROM marketing_data.creative_data")
    if "error" in result:
        print(f"Error loading creative data: {result['error']}")
        return []
        
    data = []
    for row in result["rows"]:
        data.append({
            "creative_id": row["creative_id"],
            "channel": row["channel"],
            "date": row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"]),
            "ctr": float(row["ctr"])
        })
    return data

def _load_cvr_data():
    result = query_bigquery("SELECT * FROM marketing_data.cvr_data")
    if "error" in result:
        print(f"Error loading cvr data: {result['error']}")
        return {}
        
    data = {}
    for row in result["rows"]:
        date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
        data[date_str] = float(row["cvr"])
    return data

def _load_competitor_trend_data():
    result = query_bigquery("SELECT * FROM marketing_data.competitor_trend_data")
    if "error" in result:
        print(f"Error loading competitor trend data: {result['error']}")
        return {}
        
    data = {}
    for row in result["rows"]:
        date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
        data[date_str] = float(row["trend_index"])
    return data

def _load_seasonal_events():
    result = query_bigquery("SELECT * FROM marketing_data.seasonal_events")
    if "error" in result:
        print(f"Error loading seasonal events: {result['error']}")
        return {}
        
    data = {}
    for row in result["rows"]:
        date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
        data[date_str] = row["event"]
    return data

SPEND_DATA = _load_spend_data()
CREATIVE_DATA = _load_creative_data()
CVR_DATA = _load_cvr_data()
COMPETITOR_TREND_DATA = _load_competitor_trend_data()
SEASONAL_EVENTS_DATA = _load_seasonal_events()
