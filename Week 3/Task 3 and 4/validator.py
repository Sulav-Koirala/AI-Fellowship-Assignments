import re

BLOCKED_KEYWORDS = {
    "ALTER",
    "CALL",
    "CREATE",
    "DELETE",
    "DROP",
    "EXEC",
    "EXECUTE",
    "GRANT",
    "INSERT",
    "MERGE",
    "REPLACE",
    "REVOKE",
    "TRUNCATE",
    "UPDATE",
}


def clean_sql(sql: str) -> str:
    cleaned = (sql or "").strip()
    cleaned = re.sub(r"^```(?:sql)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned if cleaned.endswith(";") else f"{cleaned};"


def validate_sql(sql: str) -> dict[str, str | bool]:
    normalized = clean_sql(sql)
    
    query_body = normalized[:-1].strip() if normalized.endswith(";") else normalized

    if not query_body:
        return {"is_valid": False, "reason": "The generated SQL was empty."}

    if ";" in query_body:
        return {"is_valid": False, "reason": "Only one SQL statement is allowed."}

    if not re.match(r"^\s*(SELECT|WITH)\b", query_body, flags=re.IGNORECASE):
        return {"is_valid": False, "reason": "Only read-only SELECT or WITH queries are allowed."}

    if re.search(r"--|/\*|\*/", query_body):
        return {"is_valid": False, "reason": "SQL comments are not allowed in generated queries."}

    raw_tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', query_body)
    tokens = {token.upper() for token in raw_tokens}
    
    blocked = sorted(tokens.intersection(BLOCKED_KEYWORDS))
    if blocked:
        return {"is_valid": False, "reason": f"Blocked keyword detected: {blocked[0]}"}

    return {"is_valid": True, "reason": "SQL passed the read-only validator."}


def is_query_safe(sql: str) -> bool:
    return bool(validate_sql(sql)["is_valid"])


if __name__ == "__main__":
    samples = [
        'SELECT "customerName" FROM customers;',
        "WITH totals AS (SELECT 1) SELECT * FROM totals;",
        "DELETE FROM customers;",
        "SELECT * FROM orders; DROP TABLE orders;",
        'SELECT "updateDate" FROM orders;',
    ]
    for sample in samples:
        print(f"Query: {sample:<50} Result: {validate_sql(sample)}")