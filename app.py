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

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Anomaly Investigator",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS — dark mode: charcoal / blue / black ──────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    :root {
        --bg:            #0D1117;
        --surface:       #161B22;
        --surface-2:     #1C2330;
        --border:        #2D3748;
        --accent:        #3B82F6;
        --accent-light:  #60A5FA;
        --accent-pale:   #162035;
        --text-primary:  #F0F4F8;
        --text-secondary:#CBD5E0;
        --text-muted:    #8B9BBB;
        --text-faint:    #4A5568;
        --font-display:  'Playfair Display', Georgia, serif;
        --font-body:     'Sora', 'Segoe UI', sans-serif;
        --radius:        12px;
        --radius-lg:     20px;
        --shadow:        0 2px 20px rgba(0,0,0,.5);
        --shadow-card:   0 4px 32px rgba(0,0,0,.4);
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background: var(--bg) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
    }
    [data-testid="stHeader"]  { background: transparent !important; }
    [data-testid="stSidebar"] { background: var(--surface) !important; }
    #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="collapsedControl"] { display: none !important; }

    .block-container {
        max-width: 1000px !important;
        padding: 0 2.5rem 5rem !important;
        margin: 0 auto !important;
    }

    /* ── Hero header ─────────────────────────────────────────── */
    .hero-wrap {
        background: var(--surface);
        border-bottom: 1px solid var(--border);
        margin: 0 -2.5rem 2.8rem;
        padding: 2.4rem 2.5rem 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }
    .hero-left { display: flex; align-items: center; gap: 16px; }
    .hero-logo {
        width: 46px; height: 46px;
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%);
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 4px 16px rgba(59,130,246,.35);
    }
    .hero-logo svg { width: 24px; height: 24px; color: #fff; }
    .hero-title {
        font-family: var(--font-display);
        font-size: 1.65rem;
        color: var(--text-primary);
        line-height: 1.1;
        margin: 0;
    }
    .hero-title span { color: var(--accent); }
    .hero-sub {
        font-size: .72rem;
        color: var(--text-muted);
        font-weight: 500;
        letter-spacing: .9px;
        text-transform: uppercase;
        margin-top: 3px;
    }
    .hero-badge {
        background: var(--accent-pale);
        border: 1px solid var(--border);
        border-radius: 30px;
        padding: .45rem 1.1rem;
        font-size: .72rem;
        color: var(--accent);
        font-weight: 600;
        letter-spacing: .5px;
        display: flex; align-items: center; gap: 6px;
    }
    .hero-badge .dot {
        width: 7px; height: 7px;
        background: var(--accent);
        border-radius: 50%;
        animation: pulse-dot 2s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%,100%{opacity:1;transform:scale(1)}
        50%{opacity:.5;transform:scale(.85)}
    }

    /* ── Section label ───────────────────────────────────────── */
    .section-label {
        font-size: .68rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: .6rem;
    }

    /* ── Query card ──────────────────────────────────────────── */
    .query-outer {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 2rem 2.2rem 1.8rem;
        box-shadow: var(--shadow-card);
        margin-bottom: 1.4rem;
    }

    /* Streamlit text input override */
    [data-testid="stTextInput"] label {
        font-size: .68rem !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
        font-family: var(--font-body) !important;
        margin-bottom: .5rem !important;
    }
    [data-testid="stTextInput"] input {
        background: var(--surface-2) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
        font-size: .95rem !important;
        padding: .8rem 1.1rem !important;
        box-shadow: none !important;
        transition: border-color .2s, box-shadow .2s !important;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(232,81,42,.12) !important;
    }
    [data-testid="stTextInput"] input::placeholder {
        color: var(--text-faint) !important;
    }

    /* ── Button ──────────────────────────────────────────────── */
    [data-testid="stFormSubmitButton"] button,
    .stButton > button {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%) !important;
        color: #fff !important;
        font-family: var(--font-body) !important;
        font-weight: 600 !important;
        font-size: .85rem !important;
        letter-spacing: .5px !important;
        border: none !important;
        border-radius: var(--radius) !important;
        padding: .75rem 2rem !important;
        box-shadow: 0 4px 16px rgba(59,130,246,.35) !important;
        transition: transform .15s, box-shadow .15s !important;
    }
    [data-testid="stFormSubmitButton"] button:hover,
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(59,130,246,.45) !important;
    }

    /* ── Pill row ─────────────────────────────────────────────── */
    .pill-row {
        display: flex; gap: 8px; flex-wrap: wrap;
        margin-bottom: 2.4rem;
    }
    .pill {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 30px;
        padding: .32rem .95rem;
        font-size: .72rem;
        color: var(--text-secondary);
        font-weight: 500;
        letter-spacing: .3px;
        box-shadow: 0 1px 4px rgba(26,18,16,.05);
    }

    /* ── Tabs ─────────────────────────────────────────────────── */
    [data-testid="stTabs"] [role="tablist"] {
        border-bottom: 2px solid var(--border) !important;
        gap: 0 !important;
        background: transparent !important;
        margin-bottom: 1.2rem !important;
    }
    [data-testid="stTabs"] button[role="tab"] {
        font-family: var(--font-body) !important;
        font-size: .75rem !important;
        font-weight: 600 !important;
        letter-spacing: .8px !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        margin-bottom: -2px !important;
        padding: .8rem 1.6rem !important;
        transition: color .2s !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom-color: var(--accent) !important;
    }
    [data-testid="stTabs"] button[role="tab"]:hover {
        color: var(--text-secondary) !important;
    }

    /* ── User bubble ──────────────────────────────────────────── */
    .user-bubble {
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        border-top-right-radius: 4px;
        padding: 1rem 1.4rem;
        margin-bottom: 1.2rem;
        text-align: right;
        font-size: .9rem;
        color: var(--text-secondary);
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 10px;
    }

    /* ── Chat bubble (synthesis) ─────────────────────────────── */
    .chat-bubble {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        border-radius: var(--radius-lg);
        border-top-left-radius: 4px;
        padding: 1.8rem 2rem;
        margin: .4rem 0 1.6rem;
        box-shadow: var(--shadow-card);
        line-height: 1.8;
        font-size: .93rem;
        color: var(--text-primary);
    }
    .chat-bubble .bubble-label {
        font-size: .68rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .chat-bubble ul {
        margin: .5rem 0 .5rem 1.2rem;
        padding: 0;
        color: var(--text-secondary);
    }
    .chat-bubble li { margin-bottom: .5rem; }
    .chat-bubble b, .chat-bubble strong {
        color: var(--text-primary);
        font-weight: 600;
    }

    /* ── Signal cards ─────────────────────────────────────────── */
    .signal-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.6rem;
        box-shadow: var(--shadow-card);
        transition: box-shadow .2s;
    }
    .signal-card:hover {
        box-shadow: 0 8px 40px rgba(59,130,246,.12);
    }
    .signal-card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 1.1rem;
        padding-bottom: .9rem;
        border-bottom: 1px solid var(--border);
    }
    .signal-icon {
        width: 34px; height: 34px;
        background: var(--accent-pale);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }
    .signal-icon svg { width: 17px; height: 17px; color: var(--accent); }
    .signal-card-title {
        font-size: .72rem;
        font-weight: 700;
        letter-spacing: .9px;
        text-transform: uppercase;
        color: var(--text-muted);
    }
    .signal-card-body {
        font-size: .88rem;
        color: var(--text-secondary);
        line-height: 1.78;
    }
    .signal-card-body b, .signal-card-body strong {
        color: var(--text-primary);
        font-weight: 600;
    }

    /* ── Status banner ────────────────────────────────────────── */
    .status-banner {
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.4rem;
        color: var(--text-secondary);
        font-size: .84rem;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: .6rem;
    }

    /* ── Empty state ──────────────────────────────────────────── */
    .empty-state {
        text-align: center;
        padding: 5rem 2rem;
        color: var(--text-faint);
    }
    .empty-icon-wrap {
        width: 64px; height: 64px;
        background: var(--surface);
        border: 1.5px solid var(--border);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1.4rem;
    }
    .empty-icon-wrap svg { width: 28px; height: 28px; color: var(--accent-light); }

    /* ── Stats row ───────────────────────────────────────────── */
    .stats-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .stat-card {
        flex: 1;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.4rem 1.6rem;
        box-shadow: var(--shadow-card);
    }
    .stat-card .stat-val {
        font-family: var(--font-display);
        font-size: 1.7rem;
        color: var(--accent);
        line-height: 1;
        margin-bottom: .3rem;
    }
    .stat-card .stat-label {
        font-size: .72rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: .7px;
        font-weight: 600;
    }

    hr { border-color: var(--border) !important; margin: 1.6rem 0 !important; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Matplotlib warm theme ─────────────────────────────────────────────────────

matplotlib.rcParams.update({
    "figure.facecolor": "#161B22",
    "axes.facecolor":   "#161B22",
    "axes.edgecolor":   "#2D3748",
    "axes.labelcolor":  "#8B9BBB",
    "axes.titlecolor":  "#F0F4F8",
    "xtick.color":      "#8B9BBB",
    "ytick.color":      "#8B9BBB",
    "grid.color":       "#2D3748",
    "text.color":       "#F0F4F8",
    "lines.color":      "#3B82F6",
    "lines.linewidth":  2.0,
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
    fig, ax = plt.subplots(figsize=(8, 2.6))
    ax.plot(dates, values, color="#3B82F6", linewidth=2.0,
            marker="o", markersize=4, markerfacecolor="#3B82F6",
            markeredgecolor="#161B22", markeredgewidth=1.5, zorder=3)
    ax.fill_between(range(len(dates)), values, color="#3B82F6", alpha=0.08)
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=40, ha="right", fontsize=8.5, color="#8B9BBB")
    ax.set_ylabel(ylabel, fontsize=8.5, color="#8B9BBB")
    ax.set_title(title, fontsize=10.5, fontweight="bold", pad=10, color="#F0F4F8")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x:,.0f}" if x >= 1000 else f"{x:.2f}" if x < 1 else f"{x:.1f}"
    ))
    ax.grid(axis="y", linestyle="--", alpha=0.4, color="#2D3748")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#2D3748")
    fig.tight_layout(pad=1.2)
    return fig

# ── Signal text helpers ───────────────────────────────────────────────────────

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

    # Spend
    if date:
        try:
            result = analyze_spend(SPEND_DATA, channel, date)
            if "error" in result:
                signals["spend"] = f"• Could not analyze spend: {result['error']}"
            else:
                change   = result.get("percentage_change", 0)
                recent   = result.get("recent_avg", 0)
                baseline = result.get("baseline_avg", 0)
                reason   = result.get("reason", "")
                anomaly  = result.get("is_anomaly", False)
                verdict  = "<b>Significant spend change detected.</b>" if anomaly else "<b>Spend is within normal range.</b>"
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

    # Creative
    if date:
        try:
            result = analyze_creative(CREATIVE_DATA, channel, date)
            if not result:
                signals["creative"] = "• <b>No creative data found for this channel/date.</b>"
            elif isinstance(result, list) and len(result) > 0:
                lines = []
                for item in result[:3]:
                    cid      = item.get("creative_id", "unknown")
                    ctr      = item.get("ctr", 0)
                    fatigued = item.get("is_fatigued", False)
                    change   = item.get("ctr_change_pct", 0)
                    verdict  = f"<b>Creative fatigue detected ({change:+.1f}% CTR drop)</b>" if fatigued else f"<b>No fatigue ({change:+.1f}% CTR change)</b>"
                    lines.append(f"• {cid}: CTR {ctr:.3f} — {verdict}")
                signals["creative"] = "<br>".join(lines)
            else:
                signals["creative"] = f"• {result}"
        except Exception as e:
            signals["creative"] = f"• Creative analysis error: {e}"
    else:
        signals["creative"] = "• No date found in query — could not run creative analysis."

    # Seasonal
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
                    verdict     = "<b>Seasonal event detected.</b>" if is_seasonal else "<b>No seasonal impact detected.</b>"
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

    # Competitor
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

    # Tech
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
            html.append(f"<p style='margin:.6rem 0 .25rem;font-weight:600;"
                        f"color:var(--text-primary)'>{content}</p>")
    if in_ul:
        html.append("</ul>")
    return "".join(html)

# ── SVG icons ─────────────────────────────────────────────────────────────────

SVG = {
    "pulse":      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "pulse_white":'<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "brain":      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2a2.5 2.5 0 0 1 5 0v.5A5.5 5.5 0 0 1 20 8v1a3 3 0 0 1 0 6v1a5.5 5.5 0 0 1-5.5 5.5h-5A5.5 5.5 0 0 1 4 16v-1a3 3 0 0 1 0-6V8A5.5 5.5 0 0 1 9.5 2.5V2Z"/></svg>',
    "chart":      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "money":      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v12M9 9.5h4.5a1.5 1.5 0 0 1 0 3h-3a1.5 1.5 0 0 0 0 3H15"/></svg>',
    "brush":      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L4 13.67V20h6.33l9.06-9.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
    "cal":        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    "target":     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "cog":        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "user":       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "arrow_right":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
}

def icon(key: str, size: int = 15, color: str = "var(--text-muted)") -> str:
    return (f'<span style="display:inline-flex;align-items:center;'
            f'width:{size}px;height:{size}px;color:{color}">{SVG[key]}</span>')

# ── Session state ─────────────────────────────────────────────────────────────

for key, val in [("final_output", None), ("agent_signals", {}), ("last_query", "")]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── Hero header ───────────────────────────────────────────────────────────────

st.markdown(
    f"""
    <div class="hero-wrap">
        <div class="hero-left">
            <div class="hero-logo">{SVG["pulse_white"]}</div>
            <div>
                <div class="hero-title">Anomaly <span>Investigator</span></div>
                <div class="hero-sub">Marketing Intelligence Platform</div>
            </div>
        </div>
        <div class="hero-badge">
            <span class="dot"></span>
            5 Agents Active
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Query input card ──────────────────────────────────────────────────────────

st.markdown('<div class="query-outer">', unsafe_allow_html=True)
with st.form("query_form", clear_on_submit=False):
    query = st.text_input(
        "Investigative Query",
        value="Why did Google CPA increase on 2024-01-06?",
        placeholder="e.g. Why did conversion rate drop on 2024-01-10?",
    )
    col_btn, col_hint, _ = st.columns([1.4, 3, 2])
    with col_btn:
        submitted = st.form_submit_button("Run Analysis →", use_container_width=True)
    with col_hint:
        st.markdown(
            "<p style='font-size:.78rem;color:var(--text-faint);margin:.6rem 0 0;line-height:1.4'>"
            "Include a date (YYYY-MM-DD) and channel name for best results."
            "</p>",
            unsafe_allow_html=True,
        )
st.markdown("</div>", unsafe_allow_html=True)

# ── Pill tags ─────────────────────────────────────────────────────────────────

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
            if event.is_final_response():
                if (hasattr(event, "content")
                        and event.content
                        and event.content.parts
                        and event.content.parts[0].text):
                    st.session_state.final_output = event.content.parts[0].text
                else:
                    st.session_state.final_output = "\n\n".join(intermediate_texts) or "No output received from agents."

    st.session_state.agent_signals = get_signal_texts(query)

# ── Output ────────────────────────────────────────────────────────────────────

if st.session_state.final_output:
    dates = list(spend_plot_data.keys())

    # User bubble
    st.markdown(
        f"""
        <div class="user-bubble">
            <span>{st.session_state.last_query}</span>
            {icon("user", 16, "var(--accent)")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Summary", "Detailed Signals"])

    # ── Summary ───────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # Stats row
        st.markdown(
            """
            <div class="stats-row">
                <div class="stat-card">
                    <div class="stat-val">5</div>
                    <div class="stat-label">Agents Queried</div>
                </div>
                <div class="stat-card">
                    <div class="stat-val">5</div>
                    <div class="stat-label">Signals Analyzed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-val">1</div>
                    <div class="stat-label">Root Cause Report</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="chat-bubble">
                <div class="bubble-label">
                    {icon("brain", 14, "var(--accent)")}
                    Synthesis Agent — Root Cause Analysis
                </div>
                {format_bubble_html(st.session_state.final_output)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="status-banner">
                {icon("arrow_right", 15, "var(--accent)")}
                Switch to <strong style="color:var(--text-primary);margin:0 5px">Detailed Signals</strong>
                to review individual channel findings and metric charts.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Detailed Signals ──────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        signals = st.session_state.agent_signals

        def signal_card(icon_key: str, label: str, body: str, chart=None):
            fallback = (f"<em style='color:var(--text-faint)'>"
                        f"No {label.lower()} findings available.</em>")
            body_html = f"<span>{body}</span>" if body else fallback
            st.markdown(
                f"""
                <div class="signal-card">
                    <div class="signal-card-header">
                        <div class="signal-icon">{SVG.get(icon_key,'')}</div>
                        <div class="signal-card-title">{label}</div>
                    </div>
                    <div class="signal-card-body">{body_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if chart:
                st.pyplot(chart, use_container_width=True)
                plt.close("all")
            st.markdown("<div style='height:.15rem'></div>", unsafe_allow_html=True)

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
            <div class="empty-icon-wrap">{SVG["pulse"]}</div>
            <div style="font-size:1.05rem;font-weight:600;
                        color:var(--text-secondary);margin-bottom:.55rem">
                No analysis yet
            </div>
            <div style="font-size:.84rem;line-height:1.75;
                        max-width:340px;margin:0 auto;color:var(--text-muted)">
                Enter a query above and click
                <strong style="color:var(--accent)">Run Analysis</strong>
                to investigate anomalies across your marketing channels.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )