# Anomaly Investigator Agent

## Project Summary
The Anomaly Investigator Agent is a multi-agent marketing diagnostic platform. It uses a coordinated system of specialized AI agents to analyze performance anomalies in marketing campaigns. 

The system includes:
- **Coordinator Agent**: Orchestrates the diagnostic process and synthesizes findings.
- **Spend Agent**: Analyzes spend anomalies, budget pacing, and channel allocation.
- **Creative Agent**: Evaluates creative performance, click-through rates (CTR), and ad fatigue.
- **Seasonality Agent**: Checks for external seasonal impacts on performance.
- **Competitor Agent**: Analyzes competitor trends and market changes.
- **Technical Agent**: Investigates technical issues like site downtime or tracking errors.

The agents ingest data from local CSV datasets (spend, creative, seasonality, conversion rates, and competitor trends) and provide decisive, data-backed root cause analyses through a Streamlit user interface.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Necessary API Keys for the LLM provider (e.g., OpenAI, Gemini) depending on the underlying agent configurations.

### Installation
1. **Navigate to the project directory**:
   ```bash
   cd AnomalyInvestigatorAgent
   ```

2. **Install dependencies**:
   If you have a `requirements.txt` file, install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
   *(Typically requires `streamlit`, `pandas`, and your chosen LLM framework packages).*

3. **Set Environment Variables**:
   Ensure you have your API keys exported in your terminal or set up in a `.env` file in the root directory.
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

### Running the Application
To launch the Streamlit interface, run the following command from the root of the project:
```bash
streamlit run app.py
```

This will start a local server and open the marketing diagnostics dashboard in your default web browser. From there, you can input a channel and date to run the coordinated anomaly investigation.
