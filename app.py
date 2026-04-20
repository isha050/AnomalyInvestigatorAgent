import streamlit as st
import asyncio
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from coordinator_agent import coordinator
from data_loader import SPEND_DATA, CREATIVE_DATA, CVR_DATA, COMPETITOR_TREND_DATA
from spend_analysis import analyze_spend
from creative_analysis import analyze_creative
from seasonal_analysis import analyze_seasonality
from competitor_analysis import analyze_competitor_trend
from tech_analysis import analyze_tech_performance

# ── Page config (must be first Streamlit call) ────────────────────────────────

st.set_page_config(
    page_title="Anomaly Investigator",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

    :root {
        --bg:          #09090b; /* Zinc 950 */
        --surface:     #18181b; /* Zinc 900 */
        --surface-2:   #27272a; /* Zinc 800 */
        --border:      #3f3f46; /* Zinc 700 */
        --accent:      #3b82f6; /* Blue 500 */
        --accent-dim:  #2563eb; /* Blue 600 */
        --text-primary:#eee;
        --text-muted:  #a1a1aa; /* Zinc 400 */
        --text-faint:  #71717a; /* Zinc 500 */
        --font-display:'DM Serif Display', Georgia, serif;
        --font-body:   'DM Sans', 'Segoe UI', sans-serif;
        --radius:      10px;
        --radius-lg:   18px;
        --shadow:      0 4px 32px rgba(0,0,0,.55);
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background: var(--bg) !important;
        color: var(--text-primary);
        font-family: var(--font-body);
    }
    [data-testid="stHeader"]  { background: transparent !important; }
    [data-testid="stSidebar"] { background: var(--surface) !important; }
    #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="collapsedControl"] { display: none !important; }

    .block-container {
        max-width: 960px !important;
        padding: 3rem 2rem 4rem !important;
        margin: 0 auto;
    }

    /* Brand header */
    .brand-header {
        display: flex; align-items: center; gap: 14px;
        margin-bottom: 2.5rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--border);
    }
    .brand-icon {
        width: 40px; height: 40px;
        background: var(--accent);
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }
    .brand-icon svg { width: 22px; height: 22px; }
    .brand-title {
        font-family: var(--font-display);
        font-size: 1.55rem;
        color: var(--text-primary);
        line-height: 1; margin: 0;
    }
    .brand-subtitle {
        font-size: .75rem;
        color: var(--text-muted);
        letter-spacing: .7px;
        text-transform: uppercase;
        margin-top: 4px;
    }

    /* Query card */
    .query-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.4rem;
        box-shadow: var(--shadow);
    }
    .query-card label {
        font-size: .72rem !important;
        font-weight: 600 !important;
        letter-spacing: .8px !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
    }

    [data-testid="stTextInput"] input {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
        font-size: .95rem !important;
        padding: .75rem 1rem !important;
        box-shadow: none !important;
        transition: border-color .2s;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(59,130,246,.15) !important;
    }

    /* Button */
    [data-testid="stFormSubmitButton"] button, .stButton > button {
        background: var(--accent) !important;
        color: #0D0F14 !important;
        font-family: var(--font-body) !important;
        font-weight: 600 !important;
        font-size: .85rem !important;
        letter-spacing: .4px !important;
        border: none !important;
        border-radius: var(--radius) !important;
        padding: .65rem 1.8rem !important;
        cursor: pointer !important;
        transition: background .2s, transform .1s !important;
        box-shadow: none !important;
    }
    [data-testid="stFormSubmitButton"] button:hover, .stButton > button:hover {
        background: var(--accent-dim) !important;
        transform: translateY(-1px) !important;
    }

    /* Tabs */
    [data-testid="stTabs"] [role="tablist"] {
        border-bottom: 1px solid var(--border) !important;
        gap: 0 !important;
        background: transparent !important;
    }
    [data-testid="stTabs"] button[role="tab"] {
        font-family: var(--font-body) !important;
        font-size: .78rem !important;
        font-weight: 600 !important;
        letter-spacing: .7px !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: .75rem 1.4rem !important;
        transition: color .2s !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom-color: var(--accent) !important;
    }
    [data-testid="stTabs"] button[role="tab"]:hover {
        color: var(--text-primary) !important;
    }

    /* Chat bubbles */
    .user-bubble {
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        border-top-right-radius: 4px;
        padding: 1rem 1.4rem;
        margin-bottom: 1.2rem;
        text-align: right;
        font-size: .9rem;
        color: var(--text-muted);
        display: flex; align-items: center;
        justify-content: flex-end; gap: 10px;
    }
    .chat-bubble {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        border-top-left-radius: 4px;
        padding: 1.6rem 1.8rem;
        margin: .4rem 0 1.5rem;
        box-shadow: var(--shadow);
        line-height: 1.75;
        font-size: .93rem;
        color: var(--text-primary);
    }
    .chat-bubble .bubble-label {
        font-size: .68rem;
        font-weight: 700;
        letter-spacing: .9px;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: .9rem;
        display: flex; align-items: center; gap: 7px;
    }
    .chat-bubble ul {
        margin: .5rem 0 .5rem 1.2rem; padding: 0;
    }
    .chat-bubble li { margin-bottom: .45rem; }

    /* Signal cards */
    .signal-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        border-radius: var(--radius);
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.4rem;
    }
    .signal-card-title {
        font-size: .7rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: .85rem;
        display: flex; align-items: center; gap: 8px;
    }
    .signal-card-body {
        font-size: .88rem;
        color: var(--text-muted);
        line-height: 1.72;
    }

    /* Pills */
    .pill-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 1.6rem; }
    .pill {
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: .3rem .85rem;
        font-size: .72rem;
        color: var(--text-muted);
        font-weight: 500;
        letter-spacing: .3px;
    }

    /* Status banner */
    .status-banner {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.4rem;
        color: var(--text-muted);
        font-size: .84rem;
        display: flex; align-items: center; gap: 10px;
        margin-top: .4rem;
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 4.5rem 2rem;
        color: var(--text-faint);
    }
    .empty-icon-wrap {
        width: 56px; height: 56px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 1.2rem;
    }

    hr { border-color: var(--border) !important; margin: 1.6rem 0 !important; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Matplotlib dark theme ─────────────────────────────────────────────────────

matplotlib.rcParams.update({
    "figure.facecolor": "#18181b",
    "axes.facecolor":   "#18181b",
    "axes.edgecolor":   "#3f3f46",
    "axes.labelcolor":  "#a1a1aa",
    "axes.titlecolor":  "#eeeeee",
    "xtick.color":      "#a1a1aa",
    "ytick.color":      "#a1a1aa",
    "grid.color":       "#3f3f46",
    "text.color":       "#eeeeee",
    "lines.color":      "#3b82f6",
    "lines.linewidth":  1.8,
    "font.family":      "sans-serif",
    "font.size":        10,
})

# ── Data preparation ──────────────────────────────────────────────────────────

spend_plot_data       = {item["date"]: item["spend"] for item in SPEND_DATA if item["channel"] == "Google"}
ctr_plot_data         = {item["date"]: item["ctr"]   for item in CREATIVE_DATA if item["channel"] == "Google"}
cvr_plot_data         = CVR_DATA
competitor_trend_plot = COMPETITOR_TREND_DATA

# ── Chart renderer ────────────────────────────────────────────────────────────

def render_chart(title: str, dates: list, values: list, ylabel: str):
    fig, ax = plt.subplots(figsize=(8, 2.8))
    ax.plot(dates, values, color="#3b82f6", linewidth=1.8,
            marker="o", markersize=3.5, markerfacecolor="#3b82f6", zorder=3)
    ax.fill_between(range(len(dates)), values, color="#3b82f6", alpha=0.07)
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8.5)
    ax.set_title(title, fontsize=10.5, fontweight="bold", pad=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x:,.0f}" if x >= 1000 else f"{x:.2f}" if x < 1 else f"{x:.1f}"
    ))
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#3f3f46")
    fig.tight_layout(pad=1.2)
    return fig

# ── Text helpers ──────────────────────────────────────────────────────────────

# ✅ NEW: Build signal texts directly from analysis functions.
# This bypasses the broken intermediate event parsing entirely.
def get_signal_texts(query: str) -> dict:
    import re

    date_match = re.search(r"\d{4}-\d{2}-\d{2}", query)
    date = date_match.group(0) if date_match else None

    channel = "Google"
    for ch in ["Google", "Meta", "Facebook", "TikTok"]:
        if ch.lower() in query.lower():
            channel = ch
            break

    signals = {}

    # ── Spend ──────────────────────────────────────────────────────────────
    if date:
        try:
            result = analyze_spend(SPEND_DATA, channel, date)
            if "error" in result:
                signals["spend"] = f"• Could not analyze spend: {result['error']}"
            else:
                change  = result.get("percentage_change", 0)
                recent  = result.get("recent_avg", 0)
                baseline= result.get("baseline_avg", 0)
                reason  = result.get("reason", "")
                anomaly = result.get("is_anomaly", False)
                verdict = "<b>Significant spend change detected.</b>" if anomaly else "<b>Spend is within normal range.</b>"
                signals["spend"] = (
                    f"• {verdict}<br>"
                    f"• {reason}<br>"
                    f"• Recent average spend: <b>${recent:,.0f}</b><br>"
                    f"• Baseline average spend: <b>${baseline:,.0f}</b><br>"
                    f"• Change: <b>{change:+.1f}%</b>"
                )
        except Exception as e:
            signals["spend"] = f"• Spend analysis error: {e}"
    else:
        signals["spend"] = "• No date found in query — could not run spend analysis."

    # ── Creative ────────────────────────────────────────────────────────────
    if date:
        try:
            result = analyze_creative(CREATIVE_DATA, channel, date)
            if not result:
                signals["creative"] = "• <b>No creative data found for this channel/date.</b>"
            elif isinstance(result, list) and len(result) > 0:
                lines = []
                for item in result[:3]:
                    cid    = item.get("creative_id", "unknown")
                    ctr    = item.get("ctr", 0)
                    fatigued = item.get("is_fatigued", False)
                    change = item.get("ctr_change_pct", 0)
                    if fatigued:
                        verdict = f"<b>Creative fatigue detected ({change:+.1f}% CTR drop)</b>"
                    else:
                        verdict = f"<b>No fatigue ({change:+.1f}% CTR change)</b>"
                    lines.append(f"• {cid}: CTR {ctr:.3f} — {verdict}")
                signals["creative"] = "<br>".join(lines)
            else:
                signals["creative"] = f"• {result}"
        except Exception as e:
            signals["creative"] = f"• Creative analysis error: {e}"
    else:
        signals["creative"] = "• No date found in query — could not run creative analysis."

    # ── Seasonal ────────────────────────────────────────────────────────────
    if date:
        try:
            result = analyze_seasonality(date)
            if isinstance(result, dict):
                if "error" in result:
                    signals["seasonal"] = f"• {result['error']}"
                else:
                    is_seasonal = result.get("is_seasonal", False)
                    event       = result.get("event")
                    days        = result.get("days_from_event")
                    reason      = result.get("reason", "")
                    verdict = "<b>Seasonal event detected.</b>" if is_seasonal else "<b>No seasonal impact detected.</b>"
                    lines = [f"• {verdict}", f"• {reason}"]
                    if event:
                        lines.append(f"• Nearby event: <b>{event}</b> ({days} days away)")
                    signals["seasonal"] = "<br>".join(lines)
            else:
                signals["seasonal"] = f"• {result}"
        except Exception as e:
            signals["seasonal"] = f"• Seasonal analysis error: {e}"
    else:
        signals["seasonal"] = "• No date found in query — could not run seasonal analysis."

    # ── Competitor ──────────────────────────────────────────────────────────
    if date:
        try:
            result = analyze_competitor_trend(date)
            if isinstance(result, dict):
                if "error" in result:
                    signals["competitor"] = f"• {result['error']}"
                else:
                    spike   = result.get("is_competitor_spike", False)
                    change  = result.get("trend_change_pct", 0)
                    reason  = result.get("reason", "")
                    verdict = "<b>Competitor activity spike detected.</b>" if spike else "<b>No significant competitor activity.</b>"
                    signals["competitor"] = (
                        f"• {verdict}<br>"
                        f"• {reason}<br>"
                        f"• Search demand change: <b>{change:+.1f}%</b>"
                    )
            else:
                signals["competitor"] = f"• {result}"
        except Exception as e:
            signals["competitor"] = f"• Competitor analysis error: {e}"
    else:
        signals["competitor"] = "• No date found in query — could not run competitor analysis."

    # ── Tech ────────────────────────────────────────────────────────────────
    if date:
        try:
            result = analyze_tech_performance(date)
            if isinstance(result, dict):
                if "error" in result:
                    signals["tech"] = f"• {result['error']}"
                else:
                    issue   = result.get("is_tech_issue", False)
                    change  = result.get("cvr_change_pct", 0)
                    reason  = result.get("reason", "")
                    verdict = "<b>Possible tech or tracking issue detected.</b>" if issue else "<b>No tech or tracking issues detected.</b>"
                    signals["tech"] = (
                        f"• {verdict}<br>"
                        f"• {reason}<br>"
                        f"• Conversion rate change: <b>{change:+.1f}%</b>"
                    )
            else:
                signals["tech"] = f"• {result}"
        except Exception as e:
            signals["tech"] = f"• Tech analysis error: {e}"
    else:
        signals["tech"] = "• No date found in query — could not run tech analysis."

    return signals


def format_bubble_html(text: str) -> str:
    if not text:
        return "<em style='color:var(--text-faint)'>No output received.</em>"
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    items = []
    for line in lines:
        clean = line.lstrip("-•*·").strip()
        if clean.endswith(":") and len(clean) < 80:
            items.append(("header", clean))
        else:
            items.append(("item", clean))
    html, in_ul = [], False
    for kind, content in items:
        if kind == "item":
            if not in_ul:
                html.append("<ul>"); in_ul = True
            html.append(f"<li>{content}</li>")
        else:
            if in_ul:
                html.append("</ul>"); in_ul = False
            html.append(f"<p style='margin:.6rem 0 .2rem;font-weight:600;"
                        f"color:var(--text-primary)'>{content}</p>")
    if in_ul:
        html.append("</ul>")
    return "".join(html)

# ── SVG icons (inline, no external deps) ─────────────────────────────────────

SVG = {
    "pulse":  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "pulse_dark": '<svg viewBox="0 0 24 24" fill="none" stroke="#0D0F14" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "brain":  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2a2.5 2.5 0 0 1 5 0v.5A5.5 5.5 0 0 1 20 8v1a3 3 0 0 1 0 6v1a5.5 5.5 0 0 1-5.5 5.5h-5A5.5 5.5 0 0 1 4 16v-1a3 3 0 0 1 0-6V8A5.5 5.5 0 0 1 9.5 2.5V2Z"/></svg>',
    "chart":  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "money":  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v12M9 9.5h4.5a1.5 1.5 0 0 1 0 3h-3a1.5 1.5 0 0 0 0 3H15"/></svg>',
    "brush":  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L4 13.67V20h6.33l9.06-9.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
    "cal":    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    "target": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "cog":    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "user":   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
}

def icon(key: str, size: int = 15, color: str = "var(--text-muted)") -> str:
    return (f'<span style="display:inline-flex;align-items:center;'
            f'width:{size}px;height:{size}px;color:{color}">{SVG[key]}</span>')

# ── Session state init ────────────────────────────────────────────────────────

for key, val in [("final_output", None), ("agent_signals", {}), ("last_query", "")]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── Brand header ──────────────────────────────────────────────────────────────

st.markdown(
    f"""
    <div class="brand-header">
        <div class="brand-icon">{SVG["pulse_dark"]}</div>
        <div>
            <div class="brand-title">Anomaly Investigator</div>
            <div class="brand-subtitle">Marketing Intelligence Platform</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Query input ───────────────────────────────────────────────────────────────

st.markdown('<div class="query-card">', unsafe_allow_html=True)
with st.form("query_form", clear_on_submit=False):
    query = st.text_input(
        "Investigative Query",
        value="Why did Google CPA increase on 2024-01-06?",
        placeholder="e.g. Why did conversion rate drop on 2024-01-10?",
    )
    col_btn, _ = st.columns([1, 5])
    with col_btn:
        submitted = st.form_submit_button("Run Analysis", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── Channel pills ─────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="pill-row">
        <span class="pill">Google Ads</span>
        <span class="pill">Spend Signal</span>
        <span class="pill">Creative CTR</span>
        <span class="pill">Conversion Rate</span>
        <span class="pill">Competitor Index</span>
        <span class="pill">Tech &amp; Tracking</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Run agent ─────────────────────────────────────────────────────────────────

if submitted and query.strip():
    st.session_state.last_query = query
    session_service = InMemorySessionService()
    runner = Runner(agent=coordinator, session_service=session_service, app_name="anomaly_system")
    asyncio.run(session_service.create_session(app_name="anomaly_system", user_id="user1", session_id="s1"))
    message = Content(role="user", parts=[Part(text=query)])
    intermediate_texts: list[str] = []

    with st.spinner("Analyzing signals across all channels..."):
        for event in runner.run(user_id="user1", session_id="s1", new_message=message):
            if hasattr(event, "content") and event.content and event.content.parts:
                t = event.content.parts[0].text
                if t:
                    intermediate_texts.append(t)
            # ✅ FIX 1A: Guard final output capture so it doesn't crash
            # if the final event has no content or parts
            if event.is_final_response():
                if (hasattr(event, "content")
                        and event.content
                        and event.content.parts
                        and event.content.parts[0].text):
                    st.session_state.final_output = event.content.parts[0].text
                else:
                    # Fallback: use everything collected so far as the output
                    st.session_state.final_output = "\n\n".join(intermediate_texts) or "No output received from agents."

    # ✅ NEW: Populate signal cards directly from analysis functions,
    # not from trying to parse the agent event stream (which doesn't
    # surface sub-agent text reliably with ParallelAgent).
    st.session_state.agent_signals = get_signal_texts(query)

# ── Output ────────────────────────────────────────────────────────────────────

if st.session_state.final_output:
    dates = list(spend_plot_data.keys())

    # User query echo
    st.markdown(
        f"""
        <div class="user-bubble">
            <span>{st.session_state.last_query}</span>
            {icon("user", 16)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Summary", "Detailed Signals"])

    # ── Summary tab ───────────────────────────────────────────────────────────
    with tab1:
        st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="chat-bubble">
                <div class="bubble-label">
                    {icon("brain", 14, "var(--accent)")}
                    Synthesis Agent
                </div>
                {format_bubble_html(st.session_state.final_output)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="status-banner">
                {icon("chart", 15, "var(--accent)")}
                Switch to <strong style="color:var(--text-primary);margin:0 4px">Detailed Signals</strong>
                to review individual channel findings and metric charts.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Detailed Signals tab ──────────────────────────────────────────────────
    with tab2:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        signals = st.session_state.agent_signals

        def signal_card(icon_key: str, label: str, body: str, chart=None):
            fallback = (f"<em style='color:var(--text-faint)'>"
                        f"No {label.lower()} findings extracted from agent output.</em>")
            body_html = (
                f"<span>{body}</span>" if body else fallback
            )
            st.markdown(
                f"""
                <div class="signal-card">
                    <div class="signal-card-title">
                        {icon(icon_key, 14, "var(--accent)")}
                        {label}
                    </div>
                    <div class="signal-card-body">{body_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if chart:
                st.pyplot(chart, use_container_width=True)
                plt.close("all")
            st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)

        signal_card("money",  "Spend Analysis",
                    signals.get("spend", ""),
                    render_chart("Daily Spend", dates, list(spend_plot_data.values()), "Spend ($)"))

        signal_card("brush",  "Creative Analysis",
                    signals.get("creative", ""),
                    render_chart("Click-Through Rate (CTR)", dates, list(ctr_plot_data.values()), "CTR"))

        signal_card("cal",    "Seasonal Analysis",
                    signals.get("seasonal", ""),
                    render_chart("Conversion Rate (CVR)", dates, list(cvr_plot_data.values()), "CVR"))

        signal_card("target", "Competitor Analysis",
                    signals.get("competitor", ""),
                    render_chart("Competitor Trend Index", dates, list(competitor_trend_plot.values()), "Trend Index"))

        signal_card("cog",    "Tech & Tracking Analysis",
                    signals.get("tech", ""))

else:
    # Empty state
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-icon-wrap"
                 style="color:var(--text-faint)">{SVG["pulse"]}</div>
            <div style="font-size:1rem;font-weight:500;
                        color:var(--text-muted);margin-bottom:.5rem">
                No analysis yet
            </div>
            <div style="font-size:.82rem;line-height:1.7;max-width:320px;margin:0 auto">
                Enter a query above and click
                <strong style="color:var(--text-primary)">Run Analysis</strong>
                to begin your investigation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )