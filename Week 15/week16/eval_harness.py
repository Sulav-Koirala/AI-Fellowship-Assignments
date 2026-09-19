import asyncio
import os

from app.llm_client import get_client
from app.config import PRIMARY
from app.rag import retrieve, ingest_docs_folder
from app.prompts import build_messages
from app.tools import TOOLS, execute_tool_calls
from week16.agent import run_agent, _accum, _create

IN_RATE, OUT_RATE = 0.25, 1.50

CASES = [
    {"id": "kb_direct", "query": "What are the three core components of a RAG pipeline?",
     "kind": "kb", "expect_tool": "search_knowledge_base"},
    {"id": "kb_reword", "query": "When the documents do not cover a question, how should a grounded assistant behave?",
     "kind": "kb", "expect_tool": "search_knowledge_base"},
    {"id": "math", "query": "What is 197 multiplied by 34?",
     "kind": "tool", "expect_tool": "calculator"},
    {"id": "weather", "query": "What is the current weather in Tokyo?",
     "kind": "tool", "expect_tool": "get_weather"},
    {"id": "refuse", "query": "Who won the 2022 FIFA World Cup final?",
     "kind": "refuse", "expect_tool": None},
    {"id": "fail_inject", "query": "What are the three core components of a RAG pipeline?",
     "kind": "refuse", "expect_tool": "search_knowledge_base", "inject": "search_unavailable"},
    {"id": "fail_malformed", "query": "What are the three core components of a RAG pipeline?",
     "kind": "refuse", "expect_tool": "search_knowledge_base", "inject": "malformed"},
]

REFUSAL = ("do not have", "don't have", "lacks", "cannot", "could not", "unavailable",
           "not able", "no information", "not contain", "unable")


def is_refusal(ans):
    a = ans.lower()
    return any(p in a for p in REFUSAL)


def completed(case, res):
    ans = res["answer"].lower()
    cid = case["id"]
    if case["kind"] == "refuse":
        return is_refusal(ans)
    if cid == "math":
        return "6698" in ans.replace(",", "")
    if cid == "weather":
        return "°c" in ans or "temperature" in ans or "degree" in ans
    if cid == "kb_direct":
        return sum(w in ans for w in ("chunk", "embed", "vector")) >= 2
    if cid == "kb_reword":
        return any(k in ans for k in ("explicit", "acknowledg", "not have enough",
                                      "does not have", "do not have", "say so", "rather than"))
    return not is_refusal(ans) and len(ans) > 0


def tool_correct(case, tool_log):
    exp = case["expect_tool"]
    if exp is None:
        return all(t["ok"] for t in tool_log)
    used = [t for t in tool_log if t["name"] == exp]
    return bool(used) and all(t["ok"] for t in used)


def cost_usd(t):
    return (t.get("prompt", 0) * IN_RATE + t.get("completion", 0) * OUT_RATE) / 1e6


def classify(case, res, ok):
    if res["status"] == "no_answer":
        return "hard"
    if ok:
        return "-"
    if case.get("inject") and not is_refusal(res["answer"].lower()):
        return "cascading_soft"
    return "soft"


async def run_baseline(query):
    client = get_client(PRIMARY)
    tokens = {"prompt": 0, "completion": 0, "total": 0}
    hits = retrieve(query)
    context = "\n\n".join(f"[{m['source']}] {d}" for d, m in hits)
    messages = build_messages(query, context=context)
    resp = await _create(client, model=PRIMARY["model"], messages=messages, tools=TOOLS, temperature=0.2)
    _accum(tokens, resp.usage)
    msg = resp.choices[0].message
    answer = msg.content or ""
    if msg.tool_calls:
        assistant_msg = msg.model_dump(exclude_none=True)
        assistant_msg.setdefault("content", "")
        messages.append(assistant_msg)
        messages = await execute_tool_calls(messages, msg.tool_calls)
        resp2 = await _create(client, model=PRIMARY["model"], messages=messages, temperature=0.2)
        _accum(tokens, resp2.usage)
        answer = resp2.choices[0].message.content or ""
    return {"answer": answer, "tokens": tokens}


async def main():
    ingest_docs_folder("docs")
    rows, done, fails = [], 0, {}
    agent_tok, agent_cmp, base_tok = 0, 0, 0
    agent_cost, agent_cost_cmp, base_cost = 0.0, 0.0, 0.0

    for case in CASES:
        try:
            res = await run_agent(case["query"], inject_failure=case.get("inject"))
        except Exception as e:
            res = {"answer": f"[exception: {e}]", "sources": [], "confidence": 0.0, "iterations": 0,
                   "status": "no_answer", "tool_calls": [], "trajectory": [], "tokens": {"total": 0}}
        base = None
        if not case.get("inject"):
            try:
                base = await run_baseline(case["query"])
            except Exception as e:
                base = {"answer": f"[exception: {e}]", "tokens": {"total": 0}}

        ok = completed(case, res)
        tc_ok = tool_correct(case, res["tool_calls"])
        fail = classify(case, res, ok)
        done += ok
        if fail != "-":
            fails[fail] = fails.get(fail, 0) + 1
        agent_tok += res["tokens"]["total"]
        a_cost = cost_usd(res["tokens"])
        agent_cost += a_cost
        if base:
            base_tok += base["tokens"]["total"]
            agent_cmp += res["tokens"]["total"]
            agent_cost_cmp += a_cost
            base_cost += cost_usd(base["tokens"])

        names = ",".join(t["name"] for t in res["tool_calls"]) or "-"
        rows.append([case["id"], case["kind"], str(res["iterations"]), names,
                     "yes" if tc_ok else "no", "yes" if ok else "no", fail,
                     str(res["tokens"]["total"]), f"${a_cost:.5f}",
                     str(base["tokens"]["total"]) if base else "n/a"])
        print(f"[{case['id']}] done={ok} tool_ok={tc_ok} iters={res['iterations']} "
              f"fail={fail} tokens={res['tokens']['total']} :: {res['answer'][:140]}")
        await asyncio.sleep(6)

    n = len(CASES)
    header = ["ID", "Kind", "Iters", "Tools called", "Tool OK", "Completed", "Failure", "Agent tok", "Agent $", "Base tok"]
    md = ["# Week 16 - Evaluation Results", "",
          f"Agentic feature: iterative re-retrieval + grounded verification (single-agent loop).",
          f"Test queries: {n}", ""]
    md.append("| " + " | ".join(header) + " |")
    md.append("|" + "|".join(["---"] * len(header)) + "|")
    for r in rows:
        md.append("| " + " | ".join(r) + " |")
    n_cmp = sum(1 for c in CASES if not c.get("inject"))
    md += ["", "## Aggregate metrics", "",
           f"- Task completion rate: {done}/{n} ({done / n:.0%})",
           f"- Avg trajectory length: {sum(int(r[2]) for r in rows) / n:.1f} iterations",
           f"- Total tokens (agent, all {n} cases): {agent_tok}  (${agent_cost:.4f} at gemini-3.1-flash-lite rates, ${IN_RATE}/1M in, ${OUT_RATE}/1M out)",
           f"- Failure log: {fails if fails else 'none - both injected failures were recognized and safely refused, not fabricated'}",
           "", "## Cost accounting vs W15 baseline", "",
           f"Compared on the {n_cmp} cases a single-pass W15 pipeline can also run (the 2 injected-failure cases have no baseline).", "",
           f"- Agent: {agent_cmp} tokens, ${agent_cost_cmp:.4f}",
           f"- W15 single-pass baseline: {base_tok} tokens, ${base_cost:.4f}",
           f"- Overhead: {agent_cmp - base_tok} tokens, ${agent_cost_cmp - base_cost:.4f} "
           f"({(agent_cmp / base_tok if base_tok else 0):.1f}x tokens) - the price of iterative re-retrieval plus a verification pass per query.", ""]
    with open(os.path.join(os.path.dirname(__file__), "results.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("\n" + "\n".join(md[-16:]))
    print("\nWrote week16/results.md")


if __name__ == "__main__":
    asyncio.run(main())
