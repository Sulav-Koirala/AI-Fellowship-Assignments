import json
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from prompts.prompts import (
    DECOMPOSITION_PROMPT,
    SCHEMA_CONTEXT,
    SQL_FIX_PROMPT,
    SQL_GENERATION_PROMPT,
    SUMMARY_PROMPT,
)
from validator import clean_sql

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "4"))

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing. Add it to this project's .env file.")

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=GEMINI_API_KEY,
    temperature=0,
    max_retries=GEMINI_MAX_RETRIES,
)


def decompose_question(question: str) -> dict:
    prompt_template = PromptTemplate.from_template(DECOMPOSITION_PROMPT)
    chain = prompt_template | llm | JsonOutputParser()
    plan = chain.invoke({"schema": SCHEMA_CONTEXT, "question": question})
    logger.info("Question decomposition: %s", plan)
    return plan


def generate_sql(question: str, decomposition: dict) -> str:
    time.sleep(4)
    prompt_template = PromptTemplate.from_template(SQL_GENERATION_PROMPT)
    chain = prompt_template | llm | StrOutputParser()
    
    raw_sql = chain.invoke({
        "schema": SCHEMA_CONTEXT,
        "question": question,
        "decomposition": json.dumps(decomposition, indent=2),
    })
    
    sql = clean_sql(raw_sql)
    logger.info("Generated SQL: %s", sql)
    return sql


def fix_sql(question: str, failed_sql: str, error: str) -> str:
    time.sleep(4)
    prompt_template = PromptTemplate.from_template(SQL_FIX_PROMPT)
    chain = prompt_template | llm | StrOutputParser()
    
    raw_sql = chain.invoke({
        "schema": SCHEMA_CONTEXT,
        "question": question,
        "sql": failed_sql,
        "error": error,
    })
    
    sql = clean_sql(raw_sql)
    logger.info("Repaired SQL: %s", sql)
    return sql


def generate_summary(question: str, rows: list[dict]) -> str:
    time.sleep(4)
    prompt_template = PromptTemplate.from_template(SUMMARY_PROMPT)
    chain = prompt_template | llm | StrOutputParser()
    
    summary = chain.invoke({
        "question": question,
        "rows": json.dumps(rows[:25], default=str, indent=2),
    })
    
    return summary.strip()