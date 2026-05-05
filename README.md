# Anomaly Investigator

A multi-agent AI system for automated marketing performance anomaly detection, root cause analysis, and budget scenario simulation. Built on Google ADK, Gemini 2.5 Flash, and BigQuery.

---

## Overview

Anomaly Investigator is a full-stack intelligence platform designed for marketing analysts. When a KPI degrades or a CPA spikes unexpectedly, the system dispatches a team of specialized AI agents — each examining a distinct domain — and synthesizes their findings into a structured root cause report with ranked contributing factors.

Core capabilities:

- Multi-agent parallel root cause analysis across five marketing domains
- Real-time MMM (Marketing Mix Modeling) context injection from the Lifesight API
- Interactive budget scenario simulation with AI-narrated results
- Automated anomaly detection scanning the last 30 days of data
- Conversational drill-down for follow-up questions on any completed analysis
- Live time-series charts for spend, CTR, CVR, and competitor trend data
- Causal DAG visualization with Lifesight platform integration

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              React Frontend (Vite)           │
│  Investigator.jsx + 11 UI Components         │
└─────────────────┬───────────────────────────┘
                  │ HTTP / SSE (EventSource)
┌─────────────────▼───────────────────────────┐
│           FastAPI Backend (Python)           │
│              server.py  :8000                │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │         Coordinator Agent            │   │
│  │  (SequentialAgent via Google ADK)    │   │
│  │                                      │   │
│  │  ┌─────────────────────────────┐    │   │
│  │  │     ParallelAgent           │    │   │
│  │  │  ┌───────┐  ┌───────────┐  │    │   │
│  │  │  │Spend  │  │ Creative  │  │    │   │
│  │  │  │Agent  │  │  Agent    │  │    │   │
│  │  │  └───────┘  └───────────┘  │    │   │
│  │  │  ┌────────┐ ┌──────────┐   │    │   │
│  │  │  │Season  │ │Competitor│   │    │   │
│  │  │  │ Agent  │ │  Agent   │   │    │   │
│  │  │  └────────┘ └──────────┘   │    │   │
│  │  │  ┌───────┐                 │    │   │
│  │  │  │ Tech  │                 │    │   │
│  │  │  │ Agent │                 │    │   │
│  │  │  └───────┘                 │    │   │
│  │  └─────────────────────────────┘    │   │
│  │            ▼                        │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │     Synthesis Agent          │   │   │
│  │  │  (gemini-2.5-flash)          │   │   │
│  │  └──────────────────────────────┘   │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌───────────┐  ┌─────────┐  ┌──────────┐  │
│  │ BigQuery  │  │  MMM    │  │ Scenario │  │
│  │  Tool     │  │ Client  │  │  Model   │  │
│  └───────────┘  └─────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
         │                  │
    ┌────▼────┐     ┌───────▼──────────┐
    │BigQuery │     │ Lifesight MMM API │
    │(GCP)    │     │ (console-platform)│
    └─────────┘     └──────────────────┘
```

---

## Agent System

The agent system is built on Google ADK using a `SequentialAgent → ParallelAgent → SynthesisAgent` pipeline.

### Coordinator (`coordinator_agent.py`)

Orchestrates the full pipeline by dispatching all five specialist agents in parallel, then passing their combined outputs to the Synthesis Agent.

### Specialist Agents

All five agents execute concurrently via `ParallelAgent`.

| Agent | File | Tool Function | Domain |
|---|---|---|---|
| Spend Agent | `adk_agent.py` | `spend_tool_func(channel, date)` | Ad spend anomaly detection |
| Creative Agent | `creative_agent.py` | `creative_tool_func(channel, date)` | Creative fatigue and CTR decay |
| Seasonal Agent | `seasonal_agent.py` | `seasonal_tool_func(date)` | Holiday and seasonal effects |
| Competitor Agent | `competitor_agent.py` | `competitor_tool_func(date)` | Competitor activity spikes |
| Tech Agent | `tech_agent.py` | `tech_tool_func(date)` | Conversion rate and tracking issues |

Each agent wraps its domain analysis function as a `FunctionTool` and is scoped strictly to its domain.

### Synthesis Agent

- Model: `gemini-2.5-flash`
- Receives all five agent outputs plus MMM context (channel contribution percentages)
- Produces a structured bullet-point report: Most Likely Cause, Secondary Factors, Ruled Out
- Treats MMM contribution data as statistical ground truth when available

### Drilldown Agent

A lightweight conversational agent powered directly by `google.genai` (no ADK runner) that answers follow-up questions about a completed analysis, maintaining full chat history across turns.

---

## API Reference

The FastAPI backend exposes the following endpoints at `http://localhost:8000`.

### POST /analyze

Triggers the full multi-agent root cause analysis pipeline.

**Request body:** `{ "query": "Why did CPA increase on 2025-03-15 for Google?" }`

**Response:** Server-Sent Events (SSE) stream — one event per agent result, followed by a `done` event.

The query is enriched with live MMM context before being dispatched to agents.

### POST /drilldown

Conversational follow-up Q&A on a completed analysis.

**Request body:** `{ "query": "...", "history": [...], "context": "<prior analysis text>" }`

**Response:** SSE stream with the Gemini-generated answer.

### GET /auto-detect

Scans the last 30 days of data across all five domains and returns detected anomalies.

**Response:**
```json
{
  "anomalies": [...],
  "scan_date": "YYYY-MM-DD",
  "total_dates_scanned": 30
}
```

Each anomaly includes `date`, `signals[]`, and `severity` (`low` / `medium` / `high`).

### GET /chart-data?channel=Google

Returns time-series data for charting.

**Response:** `{ "spend": [...], "ctr": [...], "cvr": [...], "competitor": [...] }`

### GET /scenario-models

Returns fitted linear regression models and spend history for each channel.

**Response:** `{ "channels": [...], "models": { channelName: { slope, intercept, r_squared, ... } }, ... }`

### POST /simulate

Runs a what-if budget scenario simulation.

**Request body:** `{ "allocations": { "Google": 5000, "Meta": 3000 }, "baseline_date": "2025-03-01" }`

**Response:** Scenario vs. baseline comparison with predicted CVR, conversions, CPA, and an AI-narrated summary.

### GET /mmm-status

Health check for the Lifesight MMM API integration.

**Response:** `{ "status": "ok", "model_id": "...", "contributions": {...} }`

### Causal DAG Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/causal-dag-settings?dagType=MMM` | Fetch current DAG configuration |
| POST | `/causal-dag-settings` | Update DAG configuration |
| GET | `/causal-dag-graph?modelId=...` | Fetch the rendered causal DAG graph |

---

## Core Modules

### `data_loader.py`

Loads all marketing data from Google BigQuery at startup.

| Variable | BigQuery Table | Schema |
|---|---|---|
| `SPEND_DATA` | `marketing_data.spend_data` | `date, channel, spend` |
| `CREATIVE_DATA` | `marketing_data.creative_data` | `creative_id, channel, date, ctr` |
| `CVR_DATA` | `marketing_data.cvr_data` | `date, cvr` |
| `COMPETITOR_TREND_DATA` | `marketing_data.competitor_trend_data` | `date, trend_index` |
| `SEASONAL_EVENTS_DATA` | `marketing_data.seasonal_events` | `date, event` |

### `bigquery_tool.py`

Generic BigQuery query executor. Accepts a SQL string and returns rows as a list of dicts. Used by `data_loader.py` for all data retrieval.

### `mmm_client.py`

Integrates with the Lifesight MMM API to fetch real channel contribution data.

- `get_mmm_contributions()` — Fetches the most recent successful MMM model and extracts paid/non-paid split and per-channel coefficients.
- `format_mmm_for_agent(mmm_result)` — Formats MMM data as plain text for injection into agent context.

### `auto_detector.py`

Scans all dates in the lookback window, runs all five domain analysis functions, and flags dates with anomaly signals. Severity is determined by signal count: 1 = low, 2 = medium, 3+ = high.

### `scenario_model.py`

Statistical budget simulation engine.

- `fit_channel_models(spend_data, cvr_data)` — Fits per-channel linear regression (spend → CVR).
- `predict_cvr(channel_models, channel, spend_value)` — Predicts CVR with extrapolation warning flag.
- `simulate_scenario(channel_models, allocations)` — Simulates conversions and CPA across all channels.
- `get_channel_spend_history(spend_data, channel, last_n_days)` — Returns spend history for chart rendering.

### Domain Analysis Functions

| Module | Function | Returns |
|---|---|---|
| `spend_analysis.py` | `analyze_spend(data, channel, date)` | `{ is_anomaly, spend_change_pct, ... }` |
| `creative_analysis.py` | `analyze_creative(data, channel, date)` | `[{ is_fatigue, ctr_change_pct, ... }]` |
| `seasonal_analysis.py` | `analyze_seasonality(date)` | `{ is_seasonal, event_name, ... }` |
| `competitor_analysis.py` | `analyze_competitor_trend(date)` | `{ is_competitor_spike, trend_index, ... }` |
| `tech_analysis.py` | `analyze_tech_performance(date)` | `{ is_tech_issue, ... }` |

---

## Frontend Components

Built with React 19, Vite, TailwindCSS, and Recharts.

| Component | Description |
|---|---|
| `Investigator.jsx` | Main application shell: routing, layout, and state management |
| `KPIBanner.jsx` | Top-level KPI summary cards with animated sparklines and trend indicators |
| `ChartPanel.jsx` | Multi-metric time-series charts for spend, CTR, CVR, and competitor data |
| `SignalCard.jsx` | Per-domain signal display card showing agent findings with expandable detail |
| `SummaryBubble.jsx` | Renders the synthesis agent's final root cause summary with confidence meters |
| `AgentStatus.jsx` | Live agent execution status indicators with scroll-to-card behavior |
| `AutoDetector.jsx` | Anomaly severity listing for the auto-scan feature |
| `ScenarioSimulator.jsx` | Budget allocation sliders with simulation results and AI narration |
| `CausalDAGSettings.jsx` | Full UI for viewing and editing the Lifesight Causal DAG configuration |
| `ChatThread.jsx` | Conversational drill-down chat interface |
| `MMMStatus.jsx` | MMM API connection status badge |
| `TimelineVisual.jsx` | Lifecycle timeline view of a detected anomaly event |

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core runtime |
| FastAPI | 0.135 | REST API and SSE streaming |
| Uvicorn | 0.44 | ASGI server |
| Google ADK | 1.30.0 | Multi-agent orchestration framework |
| Google GenAI | 1.73.1 | Gemini model access |
| Google Cloud BigQuery | 3.41.0 | Data warehouse |
| google-cloud-aiplatform | 1.148.0 | Vertex AI integration |
| httpx | 0.28.1 | Async HTTP client for MMM API calls |
| NumPy | 2.4.4 | Linear regression for scenario modeling |
| sse-starlette | 3.3.4 | Server-Sent Events support |
| python-dotenv | 1.2.2 | Environment variable management |

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| React | 19.2 | UI framework |
| Vite | 8.x | Build tool and dev server |
| TailwindCSS | 4.2 | Utility-first styling |
| Recharts | 3.8 | Chart rendering |
| Lucide React | 1.9 | Icon library |

### External Services

| Service | Purpose |
|---|---|
| Google Cloud BigQuery | Stores and serves all marketing datasets |
| Google Vertex AI / Gemini 2.5 Flash | Powers all AI agents and analysis |
| Lifesight MMM API | Provides Marketing Mix Model contributions and Causal DAG |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Cloud project with BigQuery enabled
- A Google Cloud service account with BigQuery read and Vertex AI user permissions
- A Lifesight platform account (optional, required for MMM and Causal DAG features)

### 1. Clone the repository

```bash
git clone <repo-url>
cd AnomalyInvestigatorAgent
```

### 2. Configure environment variables

Create `backend/.env`:

```env
# Google Cloud / Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=credentials/dev.json
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True

# Lifesight MMM API (optional)
MMM_BASE_URL=https://console-platform-stg.lifesight.io
MMM_WORKSPACE=your_workspace_id
MMM_APIKEY=your_api_key
```

### 3. Add GCP service account credentials

Place your Google Cloud service account JSON at:

```
backend/credentials/dev.json
```

The service account requires `roles/bigquery.dataViewer` and `roles/aiplatform.user`.

### 4. Provision BigQuery tables

Ensure the following tables exist under the `marketing_data` dataset in your project:

```sql
marketing_data.spend_data            -- date DATE, channel STRING, spend FLOAT64
marketing_data.creative_data         -- creative_id STRING, channel STRING, date DATE, ctr FLOAT64
marketing_data.cvr_data              -- date DATE, cvr FLOAT64
marketing_data.competitor_trend_data -- date DATE, trend_index FLOAT64
marketing_data.seasonal_events       -- date DATE, event STRING
```

### 5. Install backend dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Start the backend

```bash
cd backend
python3 server.py
# Runs at http://localhost:8000
```

### 7. Install and start the frontend

```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

---

## Project Structure

```
AnomalyInvestigatorAgent/
├── backend/
│   ├── server.py              # FastAPI application — all API endpoints
│   ├── coordinator_agent.py   # SequentialAgent orchestrator
│   ├── adk_agent.py           # Spend Agent (Google ADK)
│   ├── creative_agent.py      # Creative Agent
│   ├── seasonal_agent.py      # Seasonal Agent
│   ├── competitor_agent.py    # Competitor Agent
│   ├── tech_agent.py          # Tech Performance Agent
│   ├── spend_analysis.py      # Spend anomaly detection logic
│   ├── creative_analysis.py   # Creative fatigue detection logic
│   ├── seasonal_analysis.py   # Seasonality analysis logic
│   ├── competitor_analysis.py # Competitor trend analysis logic
│   ├── tech_analysis.py       # Tech performance analysis logic
│   ├── data_loader.py         # BigQuery data ingestion
│   ├── bigquery_tool.py       # Generic BigQuery query executor
│   ├── mmm_client.py          # Lifesight MMM API client
│   ├── auto_detector.py       # Automated anomaly scanner
│   ├── scenario_model.py      # Budget simulation engine
│   ├── requirements.txt       # Python dependencies
│   ├── credentials/
│   │   └── dev.json           # GCP service account key (gitignored)
│   └── .env                   # Environment variables (gitignored)
│
└── frontend/
    ├── src/
    │   ├── Investigator.jsx   # Main application component
    │   ├── App.jsx            # Root entry point
    │   ├── components/
    │   │   ├── AgentStatus.jsx
    │   │   ├── AutoDetector.jsx
    │   │   ├── CausalDAGSettings.jsx
    │   │   ├── ChartPanel.jsx
    │   │   ├── ChatThread.jsx
    │   │   ├── KPIBanner.jsx
    │   │   ├── MMMStatus.jsx
    │   │   ├── ScenarioSimulator.jsx
    │   │   ├── SignalCard.jsx
    │   │   ├── SummaryBubble.jsx
    │   │   └── TimelineVisual.jsx
    │   └── index.css
    ├── package.json
    └── vite.config.js
```

---

## Request Flow

1. The user submits a natural language query such as "Why did CPA spike on March 15th for Google?"
2. The frontend POSTs to `/analyze` and opens an SSE stream.
3. The backend fetches live MMM contributions from Lifesight and appends them to the query context.
4. The Coordinator dispatches all five specialist agents concurrently via `ParallelAgent`.
5. Each agent calls its domain tool (e.g. `analyze_spend("Google", "2025-03-15")`), which reads from pre-loaded BigQuery data.
6. All agent results are passed to the Synthesis Agent (Gemini 2.5 Flash), which produces the final root cause report weighted by MMM contribution data.
7. Results are streamed back to the frontend via SSE as each agent completes.
8. The user may ask follow-up questions via the drill-down chat interface, which maintains full conversation history.

---

## Security Notes

- Do not commit `backend/.env` or `backend/credentials/dev.json` — both are gitignored.
- The `MMM_APIKEY` value is a workspace-scoped Lifesight API key.
- All GCP authentication is handled via the service account key file referenced by `GOOGLE_APPLICATION_CREDENTIALS`.
- CORS is currently restricted to `http://localhost:5173`. Update the `allow_origins` list in `server.py` before deploying to any non-local environment.
