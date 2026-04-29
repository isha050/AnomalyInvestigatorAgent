import numpy as np
from data_loader import SPEND_DATA, CVR_DATA

def fit_channel_models(spend_data, cvr_data):
    """
    Fits simple linear regression models for each channel based on spend and CVR.
    """
    channel_groups = {}
    skipped_channels = {}
    
    for entry in spend_data:
        channel = entry["channel"]
        date = entry["date"]
        spend = entry["spend"]
        
        if date in cvr_data:
            if channel not in channel_groups:
                channel_groups[channel] = {"x": [], "y": []}
            channel_groups[channel]["x"].append(spend)
            channel_groups[channel]["y"].append(cvr_data[date])
            
    models = {}
    for channel, data in channel_groups.items():
        x = np.array(data["x"])
        y = np.array(data["y"])
        
        # Issue 1: Skip if fewer than 5 data points
        if len(x) < 5:
            skipped_channels[channel] = f"Insufficient data: only {len(x)} points found."
            print(f"WARNING: Skipping channel {channel}. {skipped_channels[channel]}")
            continue
            
        # Fit degree 1 polynomial (linear regression)
        slope, intercept = np.polyfit(x, y, 1)
        
        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        models[channel] = {
            "slope": float(slope),
            "intercept": float(intercept),
            "r_squared": float(r_squared),
            "min_spend": float(np.min(x)),
            "max_spend": float(np.max(x))
        }
        
    return models, skipped_channels

def get_channel_spend_history(spend_data, channel, last_n_days=30):
    """
    Returns sorted spend history for a channel, limited to last N days.
    """
    history = [
        {"date": item["date"], "spend": item["spend"]}
        for item in spend_data if item["channel"] == channel
    ]
    # Sort by date
    history.sort(key=lambda x: x["date"])
    # Take last N
    return history[-last_n_days:]

def predict_cvr(channel_models, channel, spend_value):
    """
    Predicts CVR for a given channel and spend value using the fitted models.
    Returns a dict with predicted_cvr and extrapolation_warning flag.
    """
    if channel not in channel_models:
        return None
        
    model = channel_models[channel]
    prediction = model["slope"] * spend_value + model["intercept"]
    
    # Issue 2: Extrapolation warning
    extrapolation_warning = spend_value < model["min_spend"] or spend_value > model["max_spend"]
    
    # Clamp between 0.001 and 1.0
    clamped_prediction = max(0.001, min(1.0, prediction))
    
    return {
        "predicted_cvr": float(clamped_prediction),
        "extrapolation_warning": extrapolation_warning
    }

def simulate_scenario(channel_models, allocations):
    """
    Simulates a marketing scenario based on spend allocations.
    """
    results = []
    total_spend = 0.0
    total_conversions = 0.0
    
    for channel, spend in allocations.items():
        # Handle new return shape
        prediction_result = predict_cvr(channel_models, channel, spend)
        
        if prediction_result is not None:
            predicted_cvr = prediction_result["predicted_cvr"]
            extrapolation_warning = prediction_result["extrapolation_warning"]
            
            conversions = spend * predicted_cvr
            
            # Issue 3: Handle division by zero/near-zero conversions
            if round(conversions, 4) <= 0:
                cpa = None
            else:
                cpa = spend / conversions
            
            results.append({
                "channel": channel,
                "spend": spend,
                "predicted_cvr": predicted_cvr,
                "extrapolation_warning": extrapolation_warning,
                "estimated_conversions": conversions,
                "estimated_cpa": cpa
            })
            
            total_spend += spend
            total_conversions += conversions
            
    summary = {
        "total_spend": total_spend,
        "total_conversions": total_conversions,
        "blended_cpa": total_spend / total_conversions if total_conversions > 0 else 0.0
    }
    
    return results, summary

if __name__ == "__main__":
    # Load data from data_loader (already imported)
    print("Fitting models...")
    models, skipped = fit_channel_models(SPEND_DATA, CVR_DATA)
    print(f"Skipped: {skipped}")
    
    # Test simulation
    test_allocations = {"Google": 5000, "Meta": 3000, "TikTok": 2000}
    print(f"\nRunning simulation with allocations: {test_allocations}")
    
    details, summary = simulate_scenario(models, test_allocations)
    
    print("\nDetailed Results:")
    for d in details:
        print(f"Channel: {d['channel']}")
        print(f"  Spend: ${d['spend']:,.2f}")
        print(f"  Predicted CVR: {d['predicted_cvr']:.4f} (Extrapolated: {d['extrapolation_warning']})")
        print(f"  Estimated Conversions: {d['estimated_conversions']:.2f}")
        print(f"  Estimated CPA: ${d['estimated_cpa'] if d['estimated_cpa'] is not None else 'N/A'}")
        
    print("\nSummary:")
    print(f"  Total Spend: ${summary['total_spend']:,.2f}")
    print(f"  Total Conversions: {summary['total_conversions']:.2f}")
    print(f"  Blended CPA: ${summary['blended_cpa']:,.2f}")
