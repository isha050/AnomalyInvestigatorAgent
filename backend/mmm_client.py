import os
import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MMM_BASE_URL = os.getenv("MMM_BASE_URL", "")
MMM_WORKSPACE = os.getenv("MMM_WORKSPACE", "")
MMM_APIKEY = os.getenv("MMM_APIKEY", "")


def get_mmm_contributions() -> dict | None:
    """
    Reads channel contribution percentages from the external MMM API.
    This is a read-only GET request. Nothing is written or modified externally.

    Returns a dict like:
    {
        "model_id": "...",
        "model_name": "...",
        "paid_contribution_pct": 56.77,
        "non_paid_contribution_pct": 43.22,
        "contributions": {
            "google_search_spend": 23555.26,
            "meta_prospecting_spend": 118127.26,
            ...
        }
    }

    Returns None if the API is unavailable or returns no usable models.
    """
    if not MMM_BASE_URL or not MMM_WORKSPACE or not MMM_APIKEY:
        print("[MMM] Skipping: MMM env vars not configured.")
        return None

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{MMM_BASE_URL}/mmm/models",
                params={
                    "isArchived": "false",
                    "onlySuccessModels": "true",
                    "includeDefaultScenarios": "true"
                },
                headers={
                    "x-moda-workspace": MMM_WORKSPACE,
                    "x-moda-apikey": MMM_APIKEY
                }
            )
            response.raise_for_status()
            data = response.json()

    except Exception as e:
        print(f"[MMM] API read failed: {e}")
        return None

    # Real response shape: {"data": [...], "success": true, "errors": []}
    models = (
        data.get("data")
        or data.get("models")
        or (data if isinstance(data, list) else [])
    )

    if not models:
        print("[MMM] No models in response.")
        return None

    # Take the first (most recent) successful model
    model = models[0]
    model_id = str(model.get("id") or model.get("modelId") or "unknown")
    model_name = model.get("modelDisplayName") or model.get("modelName") or model_id

    # Extract paid vs non-paid split from mmmSolutions
    solutions = model.get("mmmSolutions", [])
    paid_pct = None
    non_paid_pct = None
    if solutions:
        chosen = next((s for s in solutions if s.get("userSelected")), solutions[0])
        paid_pct = chosen.get("paidContributionPercentage")
        non_paid_pct = chosen.get("nonPaidContributionPercentage")

    # Extract per-channel coefficients from modelCoefficients
    contributions = {}
    model_coefs = model.get("modelCoefficients", [])
    if model_coefs:
        coefficients = model_coefs[0].get("coefficients", [])
        # Skip intercept and prophet vars, only keep channel spend contributors
        skip = {"(Intercept)", "season", "holiday", "trend"}
        for coef in coefficients:
            name = coef.get("channel_name", "")
            value = coef.get("coefficient", 0)
            if name not in skip and value > 0:
                contributions[name] = round(value, 2)

    if not contributions and paid_pct is None:
        print("[MMM] No usable contribution data found in model.")
        return None

    return {
        "model_id": model_id,
        "model_name": model_name,
        "paid_contribution_pct": paid_pct,
        "non_paid_contribution_pct": non_paid_pct,
        "contributions": contributions
    }


def format_mmm_for_agent(mmm_result: dict | None) -> str:
    """
    Formats the MMM data into plain text for injection into
    the synthesis agent's context.
    """
    if not mmm_result:
        return "MMM data: Not available — rely on agent signals only."

    model_name = mmm_result.get("model_name", "unknown")
    paid_pct = mmm_result.get("paid_contribution_pct")
    non_paid_pct = mmm_result.get("non_paid_contribution_pct")
    contributions = mmm_result.get("contributions", {})

    lines = [
        f"MMM Model: {model_name}",
    ]

    if paid_pct is not None:
        lines.append(f"  - Paid channels total contribution: {paid_pct:.1f}%")
        lines.append(f"  - Non-paid (baseline/organic) contribution: {non_paid_pct:.1f}%")

    if contributions:
        lines.append("Top channel coefficients (higher = more impact on revenue):")
        # Sort by coefficient value descending, show top 10
        sorted_channels = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
        for channel, value in sorted_channels[:10]:
            lines.append(f"  - {channel}: {value:,.0f}")

    return "\n".join(lines)