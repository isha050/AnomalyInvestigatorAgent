import os
import httpx

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")


def _post(blocks: list, text: str) -> bool:
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        print("[slack] SLACK_BOT_TOKEN or SLACK_CHANNEL_ID not set, skipping.")
        return False
    try:
        response = httpx.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "channel": SLACK_CHANNEL_ID,
                "text": text,
                "blocks": blocks
            },
            timeout=10.0
        )
        data = response.json()
        if not data.get("ok"):
            print(f"[slack] API error: {data.get('error')}")
            return False
        print(f"[slack] message sent ts={data.get('ts')}")
        return True
    except Exception as e:
        print(f"[slack] post failed: {e}")
        return False


def _severity_emoji(severity: str) -> str:
    return {"high": ":red_circle:", "medium": ":large_yellow_circle:", "low": ":large_blue_circle:"}.get(severity.lower(), ":white_circle:")


def _signal_label(signal: str) -> str:
    return {
        "is_anomaly": "Spend anomaly",
        "is_fatigue": "Creative fatigue",
        "is_tech_issue": "Tech/tracking issue",
        "is_competitor_spike": "Competitor spike",
        "is_seasonal": "Seasonal event"
    }.get(signal, signal)


def send_anomaly_alert(anomalies: list[dict], scan_date: str, total_scanned: int):
    if not anomalies:
        return
    high = [a for a in anomalies if a["severity"] == "high"]
    medium = [a for a in anomalies if a["severity"] == "medium"]
    low = [a for a in anomalies if a["severity"] == "low"]

    header_text = f":mag: *Anomaly Report - {scan_date}*"
    summary = f"{len(anomalies)} anomalies found across {total_scanned} dates scanned"
    if high:
        summary += f" | {len(high)} high :red_circle:"
    if medium:
        summary += f" | {len(medium)} medium :large_yellow_circle:"
    if low:
        summary += f" | {len(low)} low :large_blue_circle:"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Anomaly Investigator Report", "emoji": True}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{header_text}\n{summary}"}
        },
        {"type": "divider"}
    ]

    for anomaly in anomalies[:10]:
        emoji = _severity_emoji(anomaly["severity"])
        signals_text = " | ".join(_signal_label(s) for s in anomaly["signals"])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *{anomaly['date']}* - {anomaly['severity'].upper()}\n{signals_text}"
            }
        })

    if len(anomalies) > 10:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"_...and {len(anomalies) - 10} more. Open the dashboard to see all._"}
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"Scanned {total_scanned} dates | {scan_date}"}]
    })

    _post(blocks=blocks, text=f"Anomaly Report: {len(anomalies)} anomalies found on {scan_date}")


def send_investigation_alert(query: str, synthesis_text: str, date: str = None, channel: str = None):
    label = f"{channel} - {date}" if channel and date else (date or query[:60])
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Investigation Complete", "emoji": True}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f":brain: *Query:* {query}"}
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Root Cause Summary - {label}*\n{synthesis_text[:2900]}"}
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "Sent by Anomaly Investigator"}]
        }
    ]
    _post(blocks=blocks, text=f"Investigation complete: {query}")
