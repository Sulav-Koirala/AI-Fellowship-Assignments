import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from database import database_cursor
from validator import clean_sql, validate_sql


logger = logging.getLogger(__name__)

LOG_FILE = Path(os.getenv("QUERY_LOG_FILE", "logs/query_log.json"))


def _json_safe(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _normalize_row(row: dict) -> dict:
    return {key: _json_safe(value) for key, value in dict(row).items()}


def _read_logs() -> list[dict]:
    if not LOG_FILE.exists():
        return []
    try:
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Query log was not valid JSON. Starting a fresh log list.")
        return []


def save_query_log(entry: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logs = _read_logs()
    logs.append(entry)
    LOG_FILE.write_text(json.dumps(logs, indent=2, default=str), encoding="utf-8")


def execute_sql(sql: str, question: str, retry_count: int = 0) -> dict:
    cleaned_sql = clean_sql(sql)
    validation = validate_sql(cleaned_sql)
    timestamp = datetime.now().isoformat(timespec="seconds")

    if not validation["is_valid"]:
        entry = {
            "timestamp": timestamp,
            "question": question,
            "sql": cleaned_sql,
            "status": "blocked",
            "error": validation["reason"],
            "retry_count": retry_count,
            "result": [],
        }
        save_query_log(entry)
        return entry

    try:
        with database_cursor() as cursor:
            cursor.execute(cleaned_sql)
            rows = [_normalize_row(row) for row in cursor.fetchall()]

        entry = {
            "timestamp": timestamp,
            "question": question,
            "sql": cleaned_sql,
            "status": "success",
            "error": None,
            "retry_count": retry_count,
            "result": rows,
        }
        save_query_log({**entry, "result": rows[:5]})
        return entry
    except Exception as exc:
        entry = {
            "timestamp": timestamp,
            "question": question,
            "sql": cleaned_sql,
            "status": "failed",
            "error": str(exc),
            "retry_count": retry_count,
            "result": [],
        }
        save_query_log(entry)
        return entry
