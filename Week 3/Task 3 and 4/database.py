import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def connection_settings() -> dict:
    """Fetch database credentials with standard defaults."""
    return {
        "host": os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST") or "localhost",
        "port": int(os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT") or 5432),
        "dbname": os.getenv("DB_NAME") or os.getenv("POSTGRES_DB") or "classicmodels",
        "user": os.getenv("DB_USER") or os.getenv("POSTGRES_USER") or "postgres",
        "password": os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD") or "postgres",
    }


def get_connection():
    """Create a unique connection that returns rows as clean dictionaries."""
    return psycopg2.connect(**connection_settings(), cursor_factory=RealDictCursor)


@contextmanager
def database_cursor():
    """Context manager to borrow a cursor. Automatically handles commits, rollbacks, and closing."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(max_attempts: int = 10, delay_seconds: float = 2.0) -> None:
    """Keep trying to ping the database until it wakes up."""
    for attempt in range(1, max_attempts + 1):
        try:
            with database_cursor() as cursor:
                cursor.execute("SELECT 1 AS ok;")
                cursor.fetchone()
            logger.info("Database is ready on attempt %s/%s", attempt, max_attempts)
            return
        except Exception as exc:
            logger.warning("Database is not ready yet (%s/%s): %s", attempt, max_attempts, exc)
            if attempt < max_attempts:
                time.sleep(delay_seconds)
            else:
                raise RuntimeError(f"Could not connect to PostgreSQL after {max_attempts} attempts: {exc}")


def close_db() -> None:
    """Placeholder hook for FastAPI shutdown sequence."""
    logger.info("Database shutdown hook completed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db(max_attempts=1)
    print("PostgreSQL connection OK")