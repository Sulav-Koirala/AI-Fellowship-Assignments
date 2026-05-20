import logging
from typing import Optional, TypedDict

from executor import execute_sql
from sql_generator import decompose_question, fix_sql, generate_sql, generate_summary
from validator import clean_sql

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    question: str
    decomposition: dict
    sql: str
    result: list[dict]
    summary: str
    status: str
    error: Optional[str]
    retry_count: int


def decompose_node(state: PipelineState) -> PipelineState:
    """Node 1: Break the question into structured components."""
    logger.info("Decomposing question: %s", state["question"])
    return {**state, "decomposition": decompose_question(state["question"])}


def generate_sql_node(state: PipelineState) -> PipelineState:
    """Node 2: Generate SQL from the decomposition."""
    sql = generate_sql(state["question"], state["decomposition"])
    return {**state, "sql": clean_sql(sql)}


def execute_node(state: PipelineState) -> PipelineState:
    """Node 3: Validate and execute SQL against PostgreSQL."""
    execution = execute_sql(state["sql"], state["question"], state["retry_count"])
    return {
        **state,
        "status": execution["status"],
        "error": execution["error"],
        "result": execution["result"],
    }


def retry_node(state: PipelineState) -> PipelineState:
    """Node 4: Repair failed SQL and retry once."""
    logger.info("Repairing SQL after error: %s", state["error"])
    fixed_sql = fix_sql(state["question"], state["sql"], state["error"] or "Unknown error")
    return {
        **state,
        "sql": clean_sql(fixed_sql),
        "retry_count": state["retry_count"] + 1,
    }


def output_node(state: PipelineState) -> PipelineState:
    """Node 5: Produce the final natural-language answer."""
    if state["status"] == "success":
        try:
            summary = generate_summary(state["question"], state["result"])
        except Exception as exc:
            logger.warning("Summary generation failed after SQL success: %s", exc)
            summary = (
                f"Query completed successfully and returned {len(state['result'])} rows, "
                "but Gemini was unavailable while generating the summary."
            )
        return {**state, "summary": summary}

    return {
        **state,
        "summary": "The SQL query could not be completed after the available retry attempts.",
    }


def run_text_to_sql(question: str) -> PipelineState:
    logger.info("Pipeline started for question: %s", question)
    
    # Initialize the starting state context
    state: PipelineState = {
        "question": question,
        "decomposition": {},
        "sql": "",
        "result": [],
        "summary": "",
        "status": "started",
        "error": None,
        "retry_count": 0,
    }

    # Execute linear steps sequentially
    state = decompose_node(state)
    state = generate_sql_node(state)
    state = execute_node(state)

    # Replicate conditional edge logic for retry loop
    if state["status"] != "success" and state["retry_count"] < 1:
        state = retry_node(state)
        state = execute_node(state)

    # Route final payload to output formatter
    state = output_node(state)

    if state["status"] == "success":
        logger.info("Pipeline completed successfully with %s rows", len(state["result"]))
    else:
        logger.warning("Pipeline finished with status=%s error=%s", state["status"], state["error"])
        
    return state


def print_pipeline_result(state: PipelineState) -> None:
    print("=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(f"Question : {state['question']}")
    print(f"SQL      : {state['sql']}")
    print(f"Status   : {state['status']}")
    print(f"Retries  : {state['retry_count']}")
    print(f"Summary  : {state['summary']}")
    if state["result"]:
        print(f"Results  : {len(state['result'])} rows returned")
        for row in state["result"][:3]:
            print(f"  -> {row}")
    elif state["error"]:
        print(f"Error    : {state['error']}")
    print("=" * 60)


if __name__ == "__main__":
    for sample in [
        "List all products",
        "Get orders with customer names",
    ]:
        print_pipeline_result(run_text_to_sql(sample))