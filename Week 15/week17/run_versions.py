import asyncio
import json
import os

import mlflow

from app.rag import ingest_docs_folder
from app.config import PRIMARY
from week16.agent import run_agent
from week17.prompts import VERSIONS
from week17.golden import GOLDEN

IN_RATE, OUT_RATE = 0.25, 1.50
HERE = os.path.dirname(__file__)
TRACES = os.path.join(HERE, "traces")
TRACKING_URI = "sqlite:///mlflow.db"
EXPERIMENT = "assistant_prompt_versions"


def cost_usd(t):
    return (t.get("prompt", 0) * IN_RATE + t.get("completion", 0) * OUT_RATE) / 1e6


async def run_version(vid, cfg):
    kw = {k: cfg[k] for k in ("system_prompt", "temperature", "retrieval_k", "max_iters")}
    rows = []
    for case in GOLDEN:
        res = await run_agent(case["query"], **kw)
        trace = {"version": vid, "id": case["id"], "kind": case["kind"], "query": case["query"],
                 "reference": case["reference"], "answer": res["answer"], "status": res["status"],
                 "verified": res["verified"], "iterations": res["iterations"],
                 "trajectory": res["trajectory"], "tool_calls": res["tool_calls"], "tokens": res["tokens"]}
        with open(os.path.join(TRACES, f"{vid}_{case['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(trace, f, indent=2, ensure_ascii=False)
        rows.append(trace)
        print(f"[{vid}/{case['id']}] status={res['status']} iters={res['iterations']} "
              f"tok={res['tokens']['total']} :: {res['answer'][:90]}")
        await asyncio.sleep(5)
    return rows


async def main():
    os.makedirs(TRACES, exist_ok=True)
    ingest_docs_folder("docs")
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)
    all_rows = []
    for vid, cfg in VERSIONS.items():
        rows = await run_version(vid, cfg)
        tok = sum(r["tokens"]["total"] for r in rows)
        cost = sum(cost_usd(r["tokens"]) for r in rows)
        verified = sum(r["verified"] for r in rows)
        avg_iters = sum(r["iterations"] for r in rows) / len(rows)
        with mlflow.start_run(run_name=vid):
            mlflow.log_param("version", vid)
            mlflow.log_param("model", PRIMARY["model"])
            mlflow.log_params({k: cfg[k] for k in ("temperature", "retrieval_k", "max_iters")})
            mlflow.log_param("note", cfg["note"])
            mlflow.log_metrics({"total_tokens": tok, "cost_usd": cost,
                                "verified_rate": verified / len(rows), "avg_iters": avg_iters})
            for r in rows:
                mlflow.log_artifact(os.path.join(TRACES, f"{vid}_{r['id']}.json"))
        all_rows.extend(rows)
        print(f"== {vid}: tokens={tok} cost=${cost:.4f} verified={verified}/{len(rows)} "
              f"avg_iters={avg_iters:.1f}")
    with open(os.path.join(HERE, "answers.jsonl"), "w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(all_rows)} traces to week17/traces and week17/answers.jsonl")


if __name__ == "__main__":
    asyncio.run(main())
