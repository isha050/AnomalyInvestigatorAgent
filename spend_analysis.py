def analyze_spend(data, channel, date):
    if date not in [row["date"] for row in data]:
        return {"error": "Date not found"}
        
    # 1. Filter only rows matching the given channel
    filtered_data = [row for row in data if row.get("channel") == channel]
    
    # 2. Sort by date ascending
    filtered_data.sort(key=lambda x: x["date"])
    
    # 3. Locate the target date index
    target_idx = -1
    for i, row in enumerate(filtered_data):
        if row["date"] == date:
            target_idx = i
            break
            
    if target_idx == -1:
        return {"error": "Target date not found"}
        
    # 5. If fewer than 6 days exist before/including target date
    if target_idx < 5:
        return {"error": "Insufficient data"}
        
    # 4. Define windows
    # Recent window -> target date + previous 2 days (3 days total)
    recent_window = filtered_data[target_idx-2 : target_idx+1]
    
    # Baseline window -> 3 days before the recent window
    baseline_window = filtered_data[target_idx-5 : target_idx-2]
    
    # 6. Compute averages
    recent_avg = sum(row.get("spend", 0) for row in recent_window) / 3
    baseline_avg = sum(row.get("spend", 0) for row in baseline_window) / 3
    
    if baseline_avg == 0:
        return {"error": "Baseline spend is zero"}
        
    percentage_change = ((recent_avg - baseline_avg) / baseline_avg) * 100
    percentage_change = round(percentage_change, 2)
        
    # 7. Determine anomaly
    is_anomaly = abs(percentage_change) > 20
    
    if is_anomaly:
        if percentage_change < 0:
            reason = f"Spend dropped by {abs(percentage_change)}%"
        else:
            reason = f"Spend increased by {abs(percentage_change)}%"
    else:
        reason = "No significant change"

    return {
        "channel": channel,
        "date": date,
        "recent_avg": recent_avg,
        "baseline_avg": baseline_avg,
        "percentage_change": percentage_change,
        "is_anomaly": is_anomaly,
        "reason": reason
    }

if __name__ == "__main__":
    data = [
        {"date": "2024-01-01", "channel": "Google", "spend": 5000},
        {"date": "2024-01-02", "channel": "Google", "spend": 5000},
        {"date": "2024-01-03", "channel": "Google", "spend": 5000},
        {"date": "2024-01-04", "channel": "Google", "spend": 2000},
        {"date": "2024-01-05", "channel": "Google", "spend": 2100},
        {"date": "2024-01-06", "channel": "Google", "spend": 2200}
    ]

    result = analyze_spend(data, "Google", "2024-01-06")
    print(result)
