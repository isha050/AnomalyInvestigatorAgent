import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Initialize BigQuery client using BQ_PROJECT_ID from environment
client = bigquery.Client(project=os.getenv("BQ_PROJECT_ID"))

def query_bigquery(sql: str) -> dict:
    """
    Executes a SQL query against BigQuery and returns the results.
    
    Args:
        sql (str): The standard SQL query to execute.
        
    Returns:
        dict: A dictionary containing:
            - 'rows': A list of dictionaries representing the query results.
            - 'row_count': Total number of rows returned.
            On failure, returns {"error": "Error message"}.
    """
    try:
        query_job = client.query(sql)
        results = query_job.result()
        rows = [dict(row) for row in results]
        return {"rows": rows, "row_count": len(rows)}
    except Exception as e:
        return {"error": str(e)}
