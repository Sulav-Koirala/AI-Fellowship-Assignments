# Week 3 Task 3 and 4: Text-to-SQL Agent Pipeline

A FastAPI application that converts natural language questions into SQL queries using LangChain and Google Generative AI, executes them against PostgreSQL, and returns intelligent summaries.

## Project Structure

```text
main.py                FastAPI application entry point
agent_pipeline.py      Multi-stage processing pipeline orchestration
sql_generator.py       LLM-based SQL generation and natural language processing
executor.py            Database connection management and query execution
validator.py           SQL validation and security checks
database.py            Database connection pool initialization
prompts/
  prompts.py           LLM prompt templates
logs/                  Application and database logs directory
```

Other important files:

```text
Dockerfile
docker-compose.yml
requirements.txt
seed.sql
.env
```

## Pipeline Stages

1. Question Decomposition - breaks down natural language into components
2. SQL Generation - creates SQL query from decomposed question
3. SQL Validation - validates generated SQL for syntax and security
4. Query Execution - executes SQL against PostgreSQL
5. Error Handling and Retry - repairs failed SQL and retries
6. Summary Generation - converts results to natural language

## Requirements

- Python 3.11
- PostgreSQL
- Google Cloud API key with Generative AI enabled
- Docker and Docker Compose, if running with containers

## Environment Variables

Create a `.env` file in the project root with these values:

```env
POSTGRES_HOST=postgres
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=classicmodels
POSTGRES_PORT=5432
GOOGLE_API_KEY=your_google_api_key
LOG_FILE=logs/app.log
```

For local development without Docker, set `POSTGRES_HOST` to `localhost`.

## Run With Docker

Build and start the API and PostgreSQL database:

```bash
docker-compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

## Run Locally

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

## API Endpoint

POST /agent/sql

Request:
```json
{
  "question": "How many shipped orders are from USA customers?"
}
```

Response:
```json
{
  "question": "How many shipped orders are from USA customers?",
  "sql": "SELECT COUNT(*) FROM orders o JOIN customers c ...",
  "result": [{"count": 42}],
  "summary": "There are 42 shipped orders from USA customers.",
  "status": "success"
}
```

## Database Schema

The ClassicModels database includes tables for:

```text
productlines    Product line information
products        Product details with inventory
offices         Company office locations
employees       Employee information
customers       Customer data
orders          Order records
orderdetails    Line items in orders
payments        Customer payment records
```

## Database Seed Data

The `seed.sql` file is mounted into the PostgreSQL container by `docker-compose.yml`. When the container starts for the first time, PostgreSQL runs this file to create and populate the database.

## Notes

- The main application entry point is `main.py`.
- The pipeline uses LangChain to orchestrate LLM calls and psycopg2 for database connectivity.
- The Docker container runs the app with Uvicorn on port 8000.
- Use `/docs` to test the API endpoint from the browser.
- Query results are logged to `logs/query_log.json` for debugging.
- Automatic error recovery attempts to repair and retry failed SQL queries.
- Google Generative AI API usage is billed based on token consumption.
