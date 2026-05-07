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
    # Step 1 — Extract all unique channels from SPEND_DATA.
    all_channels = sorted(list(set(row["channel"] for row in SPEND_DATA)))
    
    # Step 2 — Extract target dates.
    unique_dates = sorted(list(set(row["date"] for row in SPEND_DATA)), reverse=True)
    target_dates = unique_dates[:lookback_days]
    
    anomalies = []
    
    for date in target_dates:
        signals = []
        affected_channels_set = set()
        
        # Step 3 — For each date, run channel-specific analyses across ALL channels.
        
        # 3.1 Spend Analysis
        for channel in all_channels:
            try:
                spend_res = analyze_spend(SPEND_DATA, channel, date)
                if isinstance(spend_res, dict) and not spend_res.get("error"):
                    if spend_res.get("is_anomaly"):
                        signals.append(f"spend_anomaly:{channel}")
                        affected_channels_set.add(channel)
            except Exception:
                pass
                
        # 3.2 Creative Analysis
        for channel in all_channels:
            # Only run creative analysis for a channel if that channel has at least one row in CREATIVE_DATA.
            has_creative = any(row["channel"] == channel for row in CREATIVE_DATA)
            if not has_creative:
                continue
                
            try:
                creative_res = analyze_creative(CREATIVE_DATA, channel, date)
                if isinstance(creative_res, list):
                    if any(c.get("is_fatigue") for c in creative_res):
                        signals.append(f"creative_fatigue:{channel}")
                        affected_channels_set.add(channel)
                elif isinstance(creative_res, dict) and not creative_res.get("error"):
                    if creative_res.get("is_fatigue"):
                        signals.append(f"creative_fatigue:{channel}")
                        affected_channels_set.add(channel)
            except Exception:
                pass
                
        # 3.3 Tech, Competitor, and Seasonal analyses (not channel-specific)
        try:
            tech_res = analyze_tech_performance(date)
            if isinstance(tech_res, dict) and not tech_res.get("error"):
                if tech_res.get("is_tech_issue"):
                    signals.append("is_tech_issue")
        except Exception:
            pass
            
        try:
            comp_res = analyze_competitor_trend(date)
            if isinstance(comp_res, dict) and not comp_res.get("error"):
                if comp_res.get("is_competitor_spike"):
                    signals.append("is_competitor_spike")
        except Exception:
            pass
            
        try:
            seas_res = analyze_seasonality(date)
            if isinstance(seas_res, dict) and not seas_res.get("error"):
                if seas_res.get("is_seasonal"):
                    signals.append("is_seasonal")
        except Exception:
            pass
            
        if not signals:
            continue
            
        # Step 4 — Determine severity AND correlation type.
        unique_affected_channels = sorted(list(affected_channels_set))
        num_affected_channels = len(unique_affected_channels)
        total_signal_count = len(signals)
        
        if num_affected_channels >= 3:
            severity = "high"
            correlation_type = "multi_channel_event"
        elif total_signal_count >= 3:
            severity = "high"
            correlation_type = "single_channel_event"
        elif total_signal_count == 2:
            severity = "medium"
            correlation_type = "single_channel_event"
        else: # total_signal_count == 1
            severity = "low"
            correlation_type = "single_channel_event"
            
        # Step 5 — Build the affected_channels list. (Already done in unique_affected_channels)
        
        # Step 6 — The anomaly dict structure
        anomalies.append({
            "date": date,
            "signals": signals,
            "severity": severity,
            "correlation_type": correlation_type,
            "affected_channels": unique_affected_channels
        })
            
    # Sort the final list by date descending before returning.
    anomalies.sort(key=lambda x: x["date"], reverse=True)
    return anomalies
