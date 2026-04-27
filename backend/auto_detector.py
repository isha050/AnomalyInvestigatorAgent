from data_loader import (
    SPEND_DATA,
    CREATIVE_DATA,
    CVR_DATA,
    COMPETITOR_TREND_DATA,
    SEASONAL_EVENTS_DATA
)
from spend_analysis import analyze_spend
from creative_analysis import analyze_creative
from tech_analysis import analyze_tech_performance
from competitor_analysis import analyze_competitor_trend
from seasonal_analysis import analyze_seasonality

def detect_all_anomalies(lookback_days=30) -> list[dict]:
    # Get unique dates from SPEND_DATA, sorted descending
    unique_dates = sorted(list(set(row["date"] for row in SPEND_DATA)), reverse=True)
    target_dates = unique_dates[:lookback_days]
    
    anomalies = []
    
    for date in target_dates:
        signals = []
        
        # 1. Spend Analysis
        try:
            spend_res = analyze_spend(SPEND_DATA, "Google", date)
            if isinstance(spend_res, dict) and not spend_res.get("error"):
                if spend_res.get("is_anomaly"):
                    signals.append("is_anomaly")
        except Exception:
            pass
            
        # 2. Creative Analysis
        try:
            creative_res = analyze_creative(CREATIVE_DATA, "Google", date)
            if isinstance(creative_res, list):
                if any(c.get("is_fatigue") for c in creative_res):
                    signals.append("is_fatigue")
            elif isinstance(creative_res, dict) and not creative_res.get("error"):
                # Just in case it returns a single dict without error
                if creative_res.get("is_fatigue"):
                    signals.append("is_fatigue")
        except Exception:
            pass
            
        # 3. Tech Analysis
        try:
            tech_res = analyze_tech_performance(date)
            if isinstance(tech_res, dict) and not tech_res.get("error"):
                if tech_res.get("is_tech_issue"):
                    signals.append("is_tech_issue")
        except Exception:
            pass
            
        # 4. Competitor Analysis
        try:
            comp_res = analyze_competitor_trend(date)
            if isinstance(comp_res, dict) and not comp_res.get("error"):
                if comp_res.get("is_competitor_spike"):
                    signals.append("is_competitor_spike")
        except Exception:
            pass
            
        # 5. Seasonal Analysis
        try:
            seas_res = analyze_seasonality(date)
            if isinstance(seas_res, dict) and not seas_res.get("error"):
                if seas_res.get("is_seasonal"):
                    signals.append("is_seasonal")
        except Exception:
            pass
            
        if signals:
            if len(signals) >= 3:
                severity = "high"
            elif len(signals) == 2:
                severity = "medium"
            else:
                severity = "low"
                
            anomalies.append({
                "date": date,
                "signals": signals,
                "severity": severity
            })
            
    # Ensure sorted by date descending
    anomalies.sort(key=lambda x: x["date"], reverse=True)
    return anomalies
