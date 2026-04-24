# Anomaly Investigator

Root cause analysis for marketing performance anomalies using parallel AI agents.

## Project Structure
- `backend/`: FastAPI server with Google ADK agents and BigQuery integration.
- `frontend/`: React + Vite + Tailwind + Recharts dashboard.

## Setup

### Prerequisites
- Node.js & npm
- Python 3.10+

### Environment Variables
Create a `.env` file in the `backend/` directory with the following:
```env
GOOGLE_API_KEY=your_gemini_api_key
BQ_PROJECT_ID=your_bigquery_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account.json
```

## Running the Application

### Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn server:app --reload
   ```
   The backend will be available at `http://localhost:8000`.

### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`.
