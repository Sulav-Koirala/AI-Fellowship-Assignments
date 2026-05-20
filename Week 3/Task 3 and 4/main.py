import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from agent_pipeline import run_text_to_sql
from database import close_db, init_db


LOG_FILE = Path(os.getenv("LOG_FILE", "logs/app.log"))
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["How many shipped orders are from USA customers?"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Text-to-SQL service started")
    yield
    close_db()
    logger.info("Text-to-SQL service stopped")


app = FastAPI(
    title="ClassicModels Text-to-SQL Assistant",
    version="2.0.0",
    lifespan=lifespan,
)

@app.post("/agent/sql")
def ask_database(payload: QuestionRequest):
    started_at = time.perf_counter()
    try:
        state = run_text_to_sql(payload.question)
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        return {
            "status": state["status"],
            "question": state["question"],
            "decomposition": state["decomposition"],
            "sql": state["sql"],
            "result": state["result"],
            "summary": state["summary"],
            "retry_count": state["retry_count"],
            "error": state["error"],
            "elapsed_ms": elapsed_ms,
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.exception("Request failed in %.2f ms", elapsed_ms)
        return {
            "status": "failed",
            "question": payload.question,
            "error": str(exc),
            "elapsed_ms": elapsed_ms,
        }
