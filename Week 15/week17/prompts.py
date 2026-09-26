from week16.agent import AGENT_SYSTEM

V1_SYSTEM = (
    "You are a helpful assistant. Use the available tools to answer the user's question. "
    "Search the knowledge base when it seems useful, use get_weather for weather and calculator for math. "
    "Give a direct, confident answer, and call finish when you have one."
)

V2_SYSTEM = (
    "You are a grounded research assistant. Answer only from evidence you gather with the tools.\n"
    "- Use search_knowledge_base for factual questions. If the first results are thin or off-topic, reword the "
    "query and search again before answering.\n"
    "- Use get_weather for weather questions and calculator for arithmetic.\n"
    "- If the knowledge base does not contain the answer and no tool can supply it, say so explicitly instead of "
    "answering from prior knowledge.\n"
    "- Call finish once the gathered evidence supports a complete answer."
)

VERSIONS = {
    "v1": {"system_prompt": V1_SYSTEM, "temperature": 0.7, "retrieval_k": 2, "max_iters": 3,
           "note": "terse baseline: no grounding/refusal rule, no reword-and-retry, k=2, hot"},
    "v2": {"system_prompt": V2_SYSTEM, "temperature": 0.2, "retrieval_k": 4, "max_iters": 5,
           "note": "adds grounding + refusal discipline + reword-and-retry, k=4"},
    "v3": {"system_prompt": AGENT_SYSTEM, "temperature": 0.2, "retrieval_k": 6, "max_iters": 5,
           "note": "v2 + explicit verification discipline (current agent prompt), k=6"},
}
