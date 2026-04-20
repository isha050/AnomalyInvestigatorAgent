import csv
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def _load_spend_data():
    path = os.path.join(DATA_DIR, "spend_data.csv")
    data = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                "date": row["date"],
                "channel": row["channel"],
                "spend": float(row["spend"])
            })
    return data

def _load_creative_data():
    path = os.path.join(DATA_DIR, "creative_data.csv")
    data = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                "creative_id": row["creative_id"],
                "channel": row["channel"],
                "date": row["date"],
                "ctr": float(row["ctr"])
            })
    return data

def _load_cvr_data():
    path = os.path.join(DATA_DIR, "cvr_data.csv")
    data = {}
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row["date"]] = float(row["cvr"])
    return data

def _load_competitor_trend_data():
    path = os.path.join(DATA_DIR, "competitor_trend_data.csv")
    data = {}
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row["date"]] = float(row["trend_index"]) # Support floats generally
    return data

def _load_seasonal_events():
    path = os.path.join(DATA_DIR, "seasonal_events.csv")
    data = {}
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row["date"]] = row["event"]
    return data

SPEND_DATA = _load_spend_data()
CREATIVE_DATA = _load_creative_data()
CVR_DATA = _load_cvr_data()
COMPETITOR_TREND_DATA = _load_competitor_trend_data()
SEASONAL_EVENTS_DATA = _load_seasonal_events()
