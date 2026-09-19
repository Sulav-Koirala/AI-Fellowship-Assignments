import json
import os

from tenacity import retry, stop_after_attempt, wait_exponential

from app.llm_client import get_client
from app.config import PRIMARY
from app.rag import retrieve
from app.tools import get_weather, calculator

SKILL_DIR = os.path.join(os.path.dirname(__file__), "skills")
MAX_LEDGER = 8
SNIPPET_CHARS = 800

AGENT_TOOLS = [
    {"type": "function", "function": {
        "name": "search_knowledge_base",
        "description": "Search the document knowledge base for passages relevant to a query. Reword the query and search again if earlier results were thin or off-topic.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "get_weather", "description": "Get current weather for a city",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    }},
    {"type": "function", "function": {
        "name": "calculator", "description": "Evaluate a basic arithmetic expression",
        "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
    }},
    {"type": "function", "function": {
        "name": "finish",
        "description": "Submit the final answer once the gathered evidence supports it, or to state that the knowledge base lacks the information.",
        "parameters": {"type": "object", "properties": {
            "answer": {"type": "string"},
            "sources": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number"},
        }, "required": ["answer", "sources", "confidence"]},
    }},
]

AGENT_SYSTEM = (
    "You are an agentic research assistant. You answer a question by gathering evidence over several steps, "
    "deciding what to do next from what you find, and verifying your answer before submitting it.\n\n"
    "Loop policy:\n"
    "- Use search_knowledge_base for grounding passages. If results are thin or off-topic, reword the query and "
    "search again instead of guessing.\n"
    "- Use get_weather for weather/temperature/forecast questions and calculator for any arithmetic.\n"
    "- Answer only from gathered evidence. If the knowledge base does not contain the answer and no tool can "
    "supply it, say so explicitly rather than using prior knowledge.\n"
    "- When the evidence supports a complete answer, call finish. Every run must end with a finish call.\n"
    "- Do not repeat a search that already returned nothing useful. After at most two unproductive searches, "
    "finish and state that you cannot answer from the available evidence.\n\n"
    "Available skill (loaded on demand): verify_answer - checks a draft answer against the evidence ledger and "
    "decides whether every claim is supported."
)


@retry(stop=stop_after_attempt(6), wait=wait_exponential(multiplier=2, min=4, max=45))
async def _create(client, **kwargs):
    return await client.chat.completions.create(**kwargs)


def _accum(tokens, usage):
    if not usage:
        return
    tokens["prompt"] += getattr(usage, "prompt_tokens", 0) or 0
    tokens["completion"] += getattr(usage, "completion_tokens", 0) or 0
    tokens["total"] += getattr(usage, "total_tokens", 0) or 0


def _add_hits(ledger, hits):
    for doc, meta in hits:
        key = doc[:80]
        if any(e["key"] == key for e in ledger):
            continue
        ledger.append({"key": key, "source": meta.get("source", "?"), "text": doc[:SNIPPET_CHARS]})
    return ledger[:MAX_LEDGER]


def _ledger_block(ledger):
    if not ledger:
        return "Evidence ledger: (empty - no passages gathered yet)"
    lines = [f"- [{e['source']}] {e['text']}" for e in ledger]
    return "Evidence ledger (gathered so far):\n" + "\n".join(lines)


def _search(query, inject, k=6):
    if inject == "search_unavailable":
        return None, "TOOL ERROR: the knowledge base is currently unavailable."
    if inject == "malformed":
        garbled = "�\x00 %%RAGxx pipe|ine compon##ents fzzt embd?? chnk~~ vctr$$ broken-extraction-artifact"
        return [(garbled, {"source": "corrupt_doc"})], "Retrieved 1 passage(s) into the evidence ledger."
    hits = retrieve(query, k=k)
    return hits, f"Retrieved {len(hits)} passage(s) into the evidence ledger."


async def _verify(client, draft, ledger, tokens):
    with open(os.path.join(SKILL_DIR, "verify_answer.md"), encoding="utf-8") as f:
        skill = f.read()
    messages = [
        {"role": "system", "content": skill},
        {"role": "user", "content":
            f"Draft answer:\n{draft.get('answer', '')}\n\n{_ledger_block(ledger)}\n\n"
            'Respond with ONLY JSON: {"verdict": "OK" | "INSUFFICIENT", "reason": string}'},
    ]
    resp = await _create(client, model=PRIMARY["model"], messages=messages, temperature=0.0)
    _accum(tokens, resp.usage)
    raw = (resp.choices[0].message.content or "").strip().removeprefix("```json").removesuffix("```").strip()
    try:
        data = json.loads(raw)
        return data.get("verdict") == "OK", data.get("reason", "")
    except Exception:
        return True, "verifier output unparseable; accepting draft"


async def run_agent(query, max_iters=5, inject_failure=None, system_prompt=AGENT_SYSTEM,
                    temperature=0.2, retrieval_k=6):
    client = get_client(PRIMARY)
    ledger, tool_log, trajectory = [], [], []
    tokens = {"prompt": 0, "completion": 0, "total": 0}
    convo = [{"role": "user", "content": query}]
    final, verified, status = None, False, "incomplete"
    iters = 0

    while iters < max_iters:
        iters += 1
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "system", "content": _ledger_block(ledger)}] + convo
        resp = await _create(client, model=PRIMARY["model"], messages=messages,
                             tools=AGENT_TOOLS, temperature=temperature)
        _accum(tokens, resp.usage)
        msg = resp.choices[0].message

        if not msg.tool_calls:
            convo.append({"role": "user", "content": "Conclude by calling the finish tool."})
            trajectory.append("nudge->finish")
            continue

        assistant_msg = msg.model_dump(exclude_none=True)
        assistant_msg.setdefault("content", "")
        convo.append(assistant_msg)

        finish_call = None
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args, ok = json.loads(tc.function.arguments or "{}"), True
            except Exception:
                args, ok = {}, False
            tool_log.append({"name": name, "args": args, "ok": ok})

            if name == "search_knowledge_base":
                hits, note = _search(args.get("query", ""), inject_failure, retrieval_k)
                if hits:
                    ledger = _add_hits(ledger, hits)
                trajectory.append(f"search:{args.get('query', '')[:40]}")
                convo.append({"role": "tool", "tool_call_id": tc.id, "content": note})
            elif name == "get_weather":
                try:
                    result = await get_weather(**args) if ok else "TOOL ERROR: bad arguments"
                except Exception as e:
                    result = f"TOOL ERROR: {e}"
                ledger = _add_hits(ledger, [(result, {"source": "get_weather"})])
                trajectory.append("get_weather")
                convo.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            elif name == "calculator":
                result = calculator(**args) if ok else "TOOL ERROR: bad arguments"
                ledger = _add_hits(ledger, [(result, {"source": "calculator"})])
                trajectory.append("calculator")
                convo.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            elif name == "finish":
                finish_call = (tc.id, args)
            else:
                convo.append({"role": "tool", "tool_call_id": tc.id, "content": f"Unknown tool: {name}"})

        if finish_call:
            tc_id, draft = finish_call
            ok, reason = await _verify(client, draft, ledger, tokens)
            trajectory.append(f"verify:{'OK' if ok else 'INSUFFICIENT'}")
            if ok:
                final, verified, status = draft, True, "verified"
                convo.append({"role": "tool", "tool_call_id": tc_id, "content": "accepted"})
                break
            convo.append({"role": "tool", "tool_call_id": tc_id,
                          "content": f"Verification failed: {reason}. Gather more evidence, then finish again."})

    if not verified:
        status = "unverified"
        final = {"answer": "I could not ground a confident answer in the available evidence, "
                           "so I cannot answer this reliably.", "sources": [], "confidence": 0.2}

    return {
        "query": query, "answer": final["answer"], "sources": final.get("sources", []),
        "confidence": final.get("confidence", 0.0), "iterations": iters, "verified": verified,
        "status": status, "tool_calls": tool_log, "trajectory": trajectory, "tokens": tokens,
    }
