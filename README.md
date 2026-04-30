# 🔍 Anomaly Investigator Agent

> A multi-agent AI system for automated marketing performance anomaly detection, root cause analysis, and budget scenario simulation — powered by **Google ADK**, **Gemini 2.5 Flash**, and **BigQuery**.

---

## 📌 Overview

**Anomaly Investigator** is a full-stack intelligence platform built for marketing analysts. When a KPI drops or a CPA spikes unexpectedly, this system dispatches a team of specialized AI agents — each examining a different domain — and synthesizes their findings into a decisive, bullet-point root cause report.

Key capabilities:
- 🤖 **Multi-agent parallel root cause analysis** across 5 marketing domains
- 📡 **Real-time MMM (Marketing Mix Modeling) context injection** from the Lifesight API
- 📊 **Interactive scenario simulation** with AI-narrated results
- 🚨 **Automated anomaly detection** scanning the last 30 days of data
- 💬 **Conversational drill-down** for follow-up questions on any analysis
- 📈 **Live charts** for spend, CTR, CVR, and competitor trend data
- 🌐 **Causal DAG visualization** with Lifesight platform integration

---

## 🏗️ Architecture

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

## 🤖 Agent System

The agent system is built on **Google ADK (Agent Development Kit)** using a `SequentialAgent → ParallelAgent → SynthesisAgent` pipeline.

### Coordinator (`coordinator_agent.py`)
Orchestrates the full pipeline:
1. Dispatches all 5 specialist agents **in parallel**
2. Passes their outputs to the **Synthesis Agent**

### Specialist Agents (run in parallel)

| Agent | File | Tool Function | Domain |
|-------|------|---------------|--------|
| **Spend Agent** | `adk_agent.py` | `spend_tool_func(channel, date)` | Ad spend anomaly detection |
| **Creative Agent** | `creative_agent.py` | `creative_tool_func(channel, date)` | Creative fatigue & CTR drop |
| **Seasonal Agent** | `seasonal_agent.py` | `seasonal_tool_func(date)` | Holiday / seasonal effects |
| **Competitor Agent** | `competitor_agent.py` | `competitor_tool_func(date)` | Competitor activity spikes |
| **Tech Agent** | `tech_agent.py` | `tech_tool_func(date)` | Technical performance issues |

Each agent wraps its domain analysis function as a **`FunctionTool`** and is instructed to only evaluate its domain — no cross-domain speculation.

### Synthesis Agent
- Model: `gemini-2.5-flash`
- Receives all 5 agent outputs + **MMM context** (channel contribution percentages)
- Outputs a structured bullet-point report: **Most Likely Cause → Secondary Factors → Ruled Out**
- Treats MMM data as statistical ground truth when available

### Drilldown Agent
A lightweight conversational agent powered directly by `google.genai` (no ADK runner) that answers follow-up questions about a completed analysis, maintaining full chat history.

---

## 📡 API Reference

The FastAPI backend exposes the following endpoints at `http://localhost:8000`:

### `POST /analyze`
Triggers the full multi-agent root cause analysis pipeline.
- **Body:** `{ "query": "Why did CPA increase on 2025-03-15 for Google?" }`
- **Response:** Server-Sent Events (SSE) stream — one event per agent result, then a `done` event
- **Enriches** the query with live MMM context before dispatching to agents

### `POST /drilldown`
Follow-up conversational Q&A on a completed analysis.
- **Body:** `{ "query": "...", "history": [...], "context": "<prior analysis text>" }`
- **Response:** SSE stream with the Gemini-generated answer

### `GET /auto-detect`
Scans the last 30 days of data across all 5 domains and returns detected anomalies.
- **Response:** `{ "anomalies": [...], "scan_date": "...", "total_dates_scanned": 30 }`
- Each anomaly includes: `date`, `signals[]`, `severity` (low / medium / high)

### `GET /chart-data?channel=Google`
Returns time-series data for charting.
- **Response:** `{ "spend": [...], "ctr": [...], "cvr": [...], "competitor": [...] }`

### `GET /scenario-models`
Returns fitted linear regression models and spend history for each channel.
- **Response:** `{ "channels": [...], "models": { channelName: { slope, intercept, r_squared, ... } }, ... }`

### `POST /simulate`
Runs a what-if budget scenario simulation.
- **Body:** `{ "allocations": { "Google": 5000, "Meta": 3000 }, "baseline_date": "2025-03-01" }`
- **Response:** Scenario vs. baseline comparison with predicted CVR, conversions, CPA, and an AI-narrated summary

### `GET /mmm-status`
Health check for the external Lifesight MMM API integration.
- **Response:** `{ "status": "ok", "model_id": "...", "contributions": {...} }`

### Causal DAG Endpoints (Lifesight Platform)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/causal-dag-settings?dagType=MMM` | Fetch current DAG configuration |
| `POST` | `/causal-dag-settings` | Update DAG configuration |
| `GET` | `/causal-dag-graph?modelId=...` | Fetch the rendered causal DAG graph |

---

## 🧰 Core Modules

### `data_loader.py`
Loads all marketing data from **Google BigQuery** at startup. Tables queried:

| Variable | BigQuery Table | Schema |
|----------|---------------|--------|
| `SPEND_DATA` | `marketing_data.spend_data` | `date, channel, spend` |
| `CREATIVE_DATA` | `marketing_data.creative_data` | `creative_id, channel, date, ctr` |
| `CVR_DATA` | `marketing_data.cvr_data` | `date, cvr` |
| `COMPETITOR_TREND_DATA` | `marketing_data.competitor_trend_data` | `date, trend_index` |
| `SEASONAL_EVENTS_DATA` | `marketing_data.seasonal_events` | `date, event` |

### `bigquery_tool.py` — `query_bigquery(sql: str) → dict`
Generic BigQuery query executor. Used by `data_loader.py` for all data retrieval.

### `mmm_client.py`
Integrates with the **Lifesight MMM API** to fetch real channel contribution data.
- `get_mmm_contributions() → dict | None` — Fetches the most recent successful MMM model and extracts paid/non-paid split and per-channel coefficients
- `format_mmm_for_agent(mmm_result) → str` — Formats MMM data as plain text for injection into agent context

### `auto_detector.py` — `detect_all_anomalies(lookback_days=30) → list[dict]`
Scans all dates in the lookback window, runs all 5 domain analysis functions, and flags dates with anomaly signals. Severity is determined by signal count (1 = low, 2 = medium, 3+ = high).

### `scenario_model.py`
Statistical budget simulation engine:
- `fit_channel_models(spend_data, cvr_data)` — Fits per-channel linear regression (spend → CVR)
- `predict_cvr(channel_models, channel, spend_value)` — Predicts CVR with extrapolation warnings
- `simulate_scenario(channel_models, allocations)` — Simulates conversions and CPA across channels
- `get_channel_spend_history(spend_data, channel, last_n_days)` — Returns spend history for charting

### Domain Analysis Functions

| Module | Function | Returns |
|--------|----------|---------|
| `spend_analysis.py` | `analyze_spend(data, channel, date)` | `{ is_anomaly, spend_change_pct, ... }` |
| `creative_analysis.py` | `analyze_creative(data, channel, date)` | `[{ is_fatigue, ctr_change_pct, ... }]` |
| `seasonal_analysis.py` | `analyze_seasonality(date)` | `{ is_seasonal, event_name, ... }` |
| `competitor_analysis.py` | `analyze_competitor_trend(date)` | `{ is_competitor_spike, trend_index, ... }` |
| `tech_analysis.py` | `analyze_tech_performance(date)` | `{ is_tech_issue, ... }` |

---

## 🖥️ Frontend Components

Built with **React 19 + Vite + TailwindCSS + Recharts**.

| Component | Description |
|-----------|-------------|
| `Investigator.jsx` | Main app shell — routing, layout, state management |
| `KPIBanner.jsx` | Top-level KPI summary cards with trend indicators |
| `ChartPanel.jsx` | Multi-metric time-series charts (Recharts) for spend, CTR, CVR, competitor |
| `SignalCard.jsx` | Per-domain signal display card showing agent findings |
| `SummaryBubble.jsx` | Displays the synthesis agent's final root cause summary |
| `AgentStatus.jsx` | Live agent execution status indicators |
| `AutoDetector.jsx` | Anomaly heatmap and severity listing for the auto-scan feature |
| `ScenarioSimulator.jsx` | Budget allocation sliders + simulation results with AI narration |
| `CausalDAGSettings.jsx` | Full UI for viewing/editing the Lifesight Causal DAG configuration |
| `ChatThread.jsx` | Conversational drill-down chat interface |
| `MMMStatus.jsx` | MMM API connection status badge |
| `TimelineVisual.jsx` | Timeline view of anomaly events |

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core runtime |
| FastAPI | 0.135 | REST API + SSE streaming |
| Uvicorn | 0.44 | ASGI server |
| Google ADK | 1.30.0 | Multi-agent orchestration framework |
| Google GenAI | 1.73.1 | Gemini model access |
| Google Cloud BigQuery | 3.41.0 | Data warehouse / data source |
| google-cloud-aiplatform | 1.148.0 | Vertex AI integration |
| httpx | 0.28.1 | Async HTTP client (MMM API calls) |
| NumPy | 2.4.4 | Linear regression for scenario modeling |
| sse-starlette | 3.3.4 | Server-Sent Events support |
| python-dotenv | 1.2.2 | Environment variable management |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.2 | UI framework |
| Vite | 8.x | Build tool & dev server |
| TailwindCSS | 4.2 | Utility-first styling |
| Recharts | 3.8 | Chart rendering |
| Lucide React | 1.9 | Icon library |

### Cloud & External APIs
| Service | Purpose |
|---------|---------|
| **Google Cloud BigQuery** | Stores and serves all marketing datasets |
| **Google Vertex AI / Gemini 2.5 Flash** | Powers all AI agents and analysis |
| **Lifesight MMM API** | Provides Marketing Mix Model contributions and Causal DAG |

---

## ⚙️ Setup & Configuration

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Google Cloud project with BigQuery enabled
- A Google Cloud service account with BigQuery read permissions
- A Lifesight platform account (optional — for MMM and Causal DAG features)

### 1. Clone the repository
```bash
git clone <repo-url>
cd AnomalyInvestigatorAgent
```

### 2. Configure environment variables
Create `backend/.env` with the following:
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

### 3. Add your GCP service account credentials
Place your Google Cloud service account JSON at:
```
backend/credentials/dev.json
```
The service account needs `roles/bigquery.dataViewer` and `roles/aiplatform.user`.

### 4. Set up BigQuery tables
Ensure the following tables exist in your BigQuery project under the `marketing_data` dataset:

```sql
-- Required tables
marketing_data.spend_data        -- columns: date DATE, channel STRING, spend FLOAT64
marketing_data.creative_data     -- columns: creative_id STRING, channel STRING, date DATE, ctr FLOAT64
marketing_data.cvr_data          -- columns: date DATE, cvr FLOAT64
marketing_data.competitor_trend_data -- columns: date DATE, trend_index FLOAT64
marketing_data.seasonal_events   -- columns: date DATE, event STRING
```

### 5. Install backend dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Start the backend server
```bash
cd backend
python3 server.py
# Server runs at http://localhost:8000
```

### 7. Install and start the frontend
```bash
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:5173
```

---

## 📁 Project Structure

```
AnomalyInvestigatorAgent/
├── backend/
│   ├── server.py              # FastAPI app — all API endpoints
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
    │   ├── App.jsx            # Root app entry
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

## 🔒 Security Notes

- **Never commit** `backend/.env` or `backend/credentials/dev.json` — both are gitignored
- The `MMM_APIKEY` in `.env` is a workspace-scoped Lifesight API key
- All GCP authentication is done via a service account key file (`GOOGLE_APPLICATION_CREDENTIALS`)
- CORS is currently configured for `http://localhost:5173` only — update `server.py` before deploying to production

---

## 🧩 How It Works — End to End

1. **User submits a query** like *"Why did CPA spike on March 15th for Google?"*
2. The frontend POSTs to `/analyze` and opens an SSE stream
3. The backend fetches **live MMM contributions** from Lifesight and appends them to the query context
4. The **Coordinator** runs all 5 specialist agents **in parallel** via Google ADK
5. Each agent calls its domain tool (e.g. `analyze_spend("Google", "2025-03-15")`), which queries BigQuery data
6. All agent results are passed to the **Synthesis Agent** (Gemini 2.5 Flash), which produces the final root cause report weighted by MMM contribution data
7. Results are **streamed back** to the frontend via SSE as each agent completes
8. The user can ask **follow-up questions** via the drill-down chat interface
