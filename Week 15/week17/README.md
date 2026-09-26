# Week 17 — Track B: MLOps for the Agentic Assistant

Track A applies MLOps to a model's *weights*. Track B applies the same discipline to something that has no weights at all: the **behavior and configuration** of the Weeks 15/16 assistant. The "model" being versioned here is the **prompt + decoding config**, the experiment being tracked is a sweep over prompt versions, and "drift/regression" is measured by an **LLM-as-judge** against a golden set. It's the same loop — version, track, evaluate, alert — pointed at an agent instead of a classifier.

This is built in place on top of the existing assistant (`app/`, `week16/`) with **one backward-compatible edit** to `week16/agent.py`; all new code lives in `week17/`. Track A is the standalone churn project in [`../Week 17 - Track A/`](../Week%2017%20-%20Track%20A/).

## a. Environment & Reproducibility

The assistant is migrated to [uv](https://docs.astral.sh/uv/). `pyproject.toml` lists the assistant's direct deps plus `mlflow>=2.18,<3` and `evidently` for the MLOps layer; `.python-version` pins **3.12**; the committed `uv.lock` pins everything transitive. A clean clone reproduces the env with:

```bash
cd "Week 15"
uv sync
```

Pins that matter: **Python 3.12** (MLflow 2.x and Evidently top out there; the assistant previously ran on 3.14), **`mlflow<3`** (the model-registry stage API Track A needs was dropped in MLflow 3, and both tracks share one MLflow install), and **torch routed through the PyTorch CPU index** so the migration doesn't drag in the ~1 GB CUDA stack the old `requirements.txt` froze. The resolved env used here: mlflow 2.22.5, evidently 0.7.23, torch 2.14.0+cpu, chromadb 1.5.9, sentence-transformers 6.0.1. `requirements.txt` is kept as the pip fallback.

**The one existing-file edit.** `week16/agent.py`'s `run_agent(...)` gained three keyword args — `system_prompt`, `temperature`, `retrieval_k` — each **defaulting to the value that was previously hardcoded**, and `_search` gained a `k=6` default. So every current caller (including `week16/eval_harness.py`) runs the identical code path it did before — re-running the W16 harness still passes 7/7 with the same per-case tool sequences and both injected failures refused; only token counts and trajectory lengths drift run-to-run, since the LLM itself is non-deterministic. The args exist only so `week17/` can vary the prompt and retrieval depth per version. That is the whole edit — no other Week 15/16 file is touched.

## b. Experiment Tracking

**Three prompt versions** (`week17/prompts.py`), each a config dict logged to MLflow as params:

| Version | System prompt | temp | k | max_iters |
|---|---|---|---|---|
| **v1** | terse "be helpful", no grounding/refusal rule, no reword-and-retry | 0.7 | 2 | 3 |
| **v2** | grounded: refuse when unsupported + reword-and-retry | 0.2 | 4 | 5 |
| **v3** | v2 + explicit verification discipline (the current agent prompt) | 0.2 | 6 | 5 |

These are a genuine progression, not cosmetic rewording: v1 is deliberately weak (hot, shallow retrieval, no discipline) so it produces failures worth diagnosing; v3 is the prompt the assistant ships with. `retrieval_k` and `temperature` move with the prompt because prompt quality and how much evidence the loop is *allowed* to gather are the same lever.

`week17/run_versions.py` runs every version across the golden set and, per query, captures the **full trace** — the trajectory (search → reword → tool → verify), each tool call with its arguments, iteration count, termination status, and token usage — to `week17/traces/{version}_{id}.json`, all logged as MLflow artifacts (so each version keeps both its successes and its failures). Per-version metrics land in the `assistant_prompt_versions` experiment: `total_tokens`, `cost_usd` (at gemini-3.1-flash-lite rates), `verified_rate`, `avg_iters`.

The **diagnose → revise** loop the assignment asks for is exactly this: read v1's failure traces (where a shallow, undisciplined prompt answers from prior knowledge or gives a thin, incomplete answer), and that motivates the grounding/refusal rules in v2 and the verification framing in v3. The per-version pass-rate-vs-token-cost comparison is exported to `week17/reports/version_comparison.md`.

## c. Regression Testing (the behavioral analogue of drift)

A churn model drifts when the input distribution shifts; an assistant "drifts" when a prompt or config change quietly regresses answer quality. `week17/regression.py` catches that with an **Evidently LLM-as-judge Test Suite** over the golden set (`week17/golden.py` — reference answers for the W16 suite: `kb_direct`, `kb_reword`, `math`, `weather`, `refuse`), using **two** checks:

- **`CorrectnessLLMEval`** — judges each answer against its golden reference (CORRECT / INCORRECT).
- **`DeclineLLMEval`** — judges whether the answer is a refusal, which is the *correct* behavior on the `refuse` query (whose answer isn't in the knowledge base) and incorrect elsewhere.

The judge is **Gemini itself**, reached through Evidently's `OpenAIOptions(api_url=...)` pointed at the same Gemini OpenAI-compatible endpoint the assistant uses — so the evaluator needs no extra provider or key. (Evidently's judge client sends a `seed` field and fires every judge call at once; the Gemini endpoint 400s on `seed` and the free tier caps at 15 rpm, so `regression.py` carries a small `OpenAIWrapper.complete` shim that drops `seed` and throttles/retries — the one place the library needed adapting to this endpoint.) Each version's **`pct_tests_passed`** lands in the `assistant_prompt_regression` experiment, the HTML report in `week17/reports/regression_{version}.html`, and the per-case verdicts in `week17/reports/verdicts.jsonl`.

**What the run actually found** (`week17/reports/version_comparison.md`):

| Version | pct_tests_passed | Tokens | Fails |
|---|---|---|---|
| v1 | 80% (4/5) | 6,731 | `kb_direct` |
| v2 | 80% (4/5) | 9,350 | `kb_direct` |
| v3 | 80% (4/5) | 10,514 | `kb_direct` |

All three tie at **80%**, and all three fail the same case, `kb_direct` ("the three core components of a RAG pipeline") — but the *nature* of the failure shifts across versions in a way that's more concerning than the tied pass rate suggests, not less.

**v1** (k=2, no discipline) names two of the three components — Chunking, Embeddings — and **honestly hedges** on the third, explicitly noting the source text cuts off before naming it. That's an incomplete but safe failure: the model knows what it doesn't know.

**v2** and **v3** — despite added grounding/refusal discipline and deeper retrieval (k=4, k=6) — both **confidently fabricate** a plausible-sounding third component ("Retrieval and Generation") instead of naming the actual missing piece (the vector store), at confidence 0.90–0.95. That is a *worse* failure than v1's, not a better one: more retrieval depth and more prompt discipline didn't recover the missing fact, they just made the wrong answer sound more certain.

The shared failure is the diagnostic payoff: no version fixes `kb_direct`, because the bottleneck isn't the prompt — the chunk naming the *vector store* as the third component isn't landing in retrieval cleanly, the same fixed-size-chunking limitation already documented in the [Week 15 README](../README.MD). A prompt sweep can't paper over a retrieval/data gap, and in this case the extra discipline actively backfired on this one query by trading an honest hedge for a confident wrong answer.

Cost scales with the added machinery as expected — v1 (6,731 tokens) < v2 (9,350) < v3 (10,514) — but since correctness on `kb_direct` doesn't improve with that spend, the honest read is that **v3's extra cost buys robustness on the queries it was actually designed for (grounding discipline on `kb_reword`, refusal on `refuse`), not a fix for this specific retrieval gap.** Pass rate alone can't separate the versions on this 5-case set — the auto-exported report says exactly that, noting v1 as the cheapest of the tie — but the trace-level read shows v1 and v3 are not equally good: v1 fails safe, v2 and v3 fail confidently. v3 still ships, on the strength of its behavior across the other four cases, but `kb_direct` is a known, unresolved gap that a retrieval fix — not a further prompt revision — would need to close. The honest limitation: separating the versions numerically, rather than by reading the traces, needs a larger and harder golden set than five cases.

## d. Orchestration (bonus)

`week17/dags/eval_regression_dag.py` is an Airflow DAG (`assistant_prompt_regression`, `@daily`): `evaluate` re-runs the version sweep + regression, then `check_threshold` reads the latest `pct_tests_passed` from MLflow and raises a **regression alert** if any version drops below 80%. Provided as a DAG file (the bonus asks for the DAG, not a live scheduler) — it's the CI gate you'd wire a prompt change through before shipping it.

## Running it

From `Week 15/`, with `GEMINI_API_KEY` in `.env`:

```bash
uv run python -m week17.run_versions   # sweep 3 versions over the golden set, log traces + tokens
uv run python -m week17.regression     # Evidently LLM-judge -> pct_tests_passed + HTML
```

Backward-compatibility of the `agent.py` edit is checked by re-running the untouched W16 harness and confirming `week16/results.md` still reads 7/7:

```bash
uv run python -m week16.eval_harness
```

## Layout

```
Week 15/
  pyproject.toml / uv.lock / .python-version   # uv migration of the assistant
  week16/agent.py                              # one backward-compatible edit
  week17/
    prompts.py        # v1 / v2 / v3 + per-version config
    golden.py         # golden queries + reference answers
    run_versions.py   # sweep versions, capture full traces, log to MLflow
    regression.py     # Evidently LLM-as-judge -> pct_tests_passed + HTML
    dags/eval_regression_dag.py               # Airflow DAG (file only)
    traces/  reports/                          # per-query traces + exported comparison
```