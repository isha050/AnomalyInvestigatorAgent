from datetime import datetime
from collections import defaultdict

def analyze_creative(data, channel, target_date):
    filtered_data = [row for row in data if row.get("channel") == channel]
    
    if target_date not in [row.get("date") for row in filtered_data]:
        return {"error": "Date not found"}
        
    creatives = defaultdict(list)
    for row in filtered_data:
        creatives[row["creative_id"]].append(row)
        
    fmt = "%Y-%m-%d"
    target_dt = datetime.strptime(target_date, fmt)
    
    results = []
    
    for cid, rows in creatives.items():
        # Sort by date
        rows.sort(key=lambda x: x["date"])
        
        # Filter for rows up to target_date
        valid_rows = [r for r in rows if r["date"] <= target_date]
        
        if len(valid_rows) < 3:
            continue
            
        # Target date must be present in the creative's valid rows to be evaluated accurately 
        # (Based on standard window constraints)
        if valid_rows[-1]["date"] != target_date:
            continue
            
        launch_date_str = valid_rows[0]["date"]
        launch_dt = datetime.strptime(launch_date_str, fmt)
        age_days = (target_dt - launch_dt).days
        
        early_rows = valid_rows[:3]
        recent_rows = valid_rows[-3:]
        
        early_ctr = sum(r["ctr"] for r in early_rows) / 3
        recent_ctr = sum(r["ctr"] for r in recent_rows) / 3
        
        if early_ctr == 0:
            continue
            
        ctr_drop_pct = ((recent_ctr - early_ctr) / early_ctr) * 100
        ctr_drop_pct = round(ctr_drop_pct, 1)
        
        if age_days > 14 and ctr_drop_pct < -20:
            is_fatigue = True
            reason = "Creative fatigue detected"
        else:
            is_fatigue = False
            reason = "No fatigue"
            
        results.append({
            "creative_id": cid,
            "age_days": age_days,
            "ctr_drop_pct": ctr_drop_pct,
            "is_fatigue": is_fatigue,
            "reason": reason
        })
        
    return results

if __name__ == "__main__":
    from data_loader import CREATIVE_DATA
    result = analyze_creative(CREATIVE_DATA, "Google", "2024-01-17")
    print(result)
