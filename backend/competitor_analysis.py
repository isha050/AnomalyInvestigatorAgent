from data_loader import COMPETITOR_TREND_DATA

def analyze_competitor_trend(date: str) -> dict:
    trend_data = COMPETITOR_TREND_DATA

    if date not in trend_data:
        return {"error": "Date not found"}

    sorted_dates = sorted(trend_data.keys())
    
    idx = sorted_dates.index(date)
        
    if idx < 5:
        return {"error": "Insufficient data"}
        
    recent_dates = sorted_dates[idx-2:idx+1]
    baseline_dates = sorted_dates[idx-5:idx-2]
    
    recent_avg = sum(trend_data[d] for d in recent_dates) / 3
    baseline_avg = sum(trend_data[d] for d in baseline_dates) / 3
    
    if baseline_avg == 0:
        return {"error": "Baseline average is zero"}
        
    pct_change = ((recent_avg - baseline_avg) / baseline_avg) * 100
    
    if pct_change > 20:
        is_spike = True
        reason = "Search demand increased significantly"
    else:
        is_spike = False
        reason = "No significant increase in competitor search demand"
        
    return {
        "trend_change_pct": round(pct_change, 2),
        "is_competitor_spike": is_spike,
        "reason": reason
    }

if __name__ == "__main__":
    print(analyze_competitor_trend("2024-01-06"))
