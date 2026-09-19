# Weeks 15 & 16 Assignment - AI Assistant

A retrieval-augmented, tool-using AI assistant with a production backend (async, retry, rate limiting, fallback, caching) and a Streamlit UI, built for Task 1 (Applied AI) and Task 2 (Engineering AI Systems). Week 16 (Task 3) extends it with an agentic loop over the same components, see the Week 16 section below.

## Features

- **LLM integration**: Google Gemini API (`gemini-3.1-flash-lite`) as the primary provider
- **Local model fallback**: open-source model served locally via vLLM (OpenAI-compatible)
- **Prompt engineering**: task-specific system prompt, tuned temperature/top_p
- **Structured output**: JSON responses validated against a Pydantic schema
- **Tool calling**: `get_weather` (Open-Meteo) and `calculator`
- **RAG pipeline**: chunking → embeddings (MiniLM) → Chroma vector store → retrieval
- **Web UI**: Streamlit chat interface, calling the backend over HTTP
- **Reliability**: retry with exponential backoff, rate limiting, automatic fallback to the local model, structured error handling
- **Performance**: fully async backend (FastAPI + `AsyncOpenAI`), in-memory response cache
- **Deployment**: Dockerfile + Docker Compose for the full stack

## Prerequisites

- Docker and Docker Compose
- A free [Google AI Studio](https://aistudio.google.com/apikey) API key (Gemini)
- (Optional, for the local fallback model) a GPU-enabled machine to run vLLM

## Setup

1. Clone the repo and enter it:
```bash
   git clone <your-repo-url>
   cd "Week 15"
```

2. Copy the environment template and fill in your key:
```bash
   cp .env.example .env
```
   Edit `.env` and set the following:

        GEMINI_API_KEY=your_actual_key_here
        VLLM_BASE_URL=http://localhost:8001/v1

3. (Optional) Replace the placeholder file in `docs/` with your own documents (`.txt` or `.md`), these are what the assistant retrieves from.

## Running with Docker Compose

```bash
docker compose up --build
```

- UI: `http://localhost:8501`
- Backend API: `http://localhost:8000/chat`

Stop with `Ctrl+C`, or `docker compose down` to remove containers.

## Running the Local Model (vLLM)

Requires a CUDA-capable GPU. Run this outside Docker, in its own terminal, **on a different port than the backend** (the backend already owns 8000):

```bash
pip install vllm
VLLM_USE_FLASHINFER_SAMPLER=0 vllm serve Qwen/Qwen2.5-1.5B-Instruct --port 8001 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 2048 \
  --enforce-eager
```

This exposes an OpenAI-compatible server at `http://localhost:8001/v1`, matching `VLLM_BASE_URL` in `.env`. The backend automatically falls back to this model if the Gemini API fails or times out.

## Design Notes

- **Why Gemini Flash-Lite:** free tier, generally available (not preview), supports tool calling and structured output, and is inexpensive enough for heavy iteration during development.
- **Why low temperature (0.1–0.2):** this is a fact-grounded RAG assistant; consistency matters more than creative variation.
- **RAG grounding vs. small talk:** the system prompt distinguishes between greetings/small talk (answered naturally, no context needed) and genuine questions (answered strictly from retrieved context, the model is explicitly instructed to refuse rather than answer from its own training knowledge, even when confident it knows the answer).
- **Retrieval quality filtering:** early testing surfaced a real chunking issue, a broken txt-extraction fragment scored as a spuriously close match to unrelated short queries like "hi", causing irrelevant document content to leak into unrelated answers. Fixed at two layers: chunks under 100 characters are dropped at ingestion time (removing extraction artifacts), and a cosine-distance threshold filters low-relevance matches at query time. This is a good illustration of why naive RAG systems need explicit relevance gating rather than always injecting the top-k results.
- **ONNX conversion - not applicable:** the local model is served via vLLM, which uses its own optimized CUDA kernels and continuous batching for inference. Converting to ONNX would bypass these optimizations rather than improve on them, so it was not used.
- **Caching:** identical prompts are cached in-memory (`response_cache`) keyed by a SHA-256 hash, avoiding repeat LLM calls for repeated questions.

## Known Limitations

- The in-memory cache and rate limiter reset on restart (no Redis backing).
- `calculator()` uses Python's `eval` in a restricted namespace, acceptable for this assignment's scope, not intended for production reuse.
- Free-tier Gemini rate limits (~30 requests/minute) may throttle heavy local testing; the retry logic handles this gracefully.
- The backend (port 8000) and the local vLLM server (port 8001) must run on different ports, they cannot both bind to 8000 on the same machine.
- Known retrieval limitation: fixed-size character chunking can still split a logical section across two chunks, occasionally causing a relevant detail to be missed even when it exists in the source document. Section-aware or semantic chunking would address this; not implemented here given assignment scope.

## Week 16 - Agentic Extension (Task 3)

The Week 15 assistant answers in a single pass: retrieve once, call at most one tool, return. That works when the first retrieval happens to hold the answer, but it has no way to recover when it doesn't, it can't reword a weak query and try again, and it never checks its own answer before handing it back. Week 16 wraps the same building blocks (RAG, tools, LLM client) in an agentic loop that picks its next action from what it has found so far and verifies the answer before finishing. All of it lives in `week16/` and changes no Week 15 file.

**Skill vs Agent, in one sentence:** the *agent* is the thing that decides and acts in a loop (it owns the control flow and picks the tools), while a *skill* is a packaged instruction set the agent loads into context on demand to do one narrow job, here the loop is the agent and `verify_answer` is a skill it consults only at the verification step.

### a. Context engineering technique

Two techniques, both aimed at keeping the working context small and relevant as the loop runs:

- **Structured evidence ledger (compaction + clearing tool results)** in `week16/agent.py` (`_add_hits`, `_ledger_block`). Every tool result, retrieved passages, a weather reading, a calculator result, is written into a compact, deduplicated ledger rather than left to pile up as raw tool messages in the transcript. Each model turn sees the ledger, capped at `MAX_LEDGER` entries, not the full history of every prior call. This is the fix for context saturation: without it, a run that searches three or four times carries every raw result forward, the passage that actually answers the question gets buried in accumulated noise, and token cost climbs on every subsequent turn.
- **Progressive disclosure via a skill file** (`week16/skills/verify_answer.md`). The verification procedure is not baked into the system prompt; the prompt only mentions the skill exists. Its full instructions are read from disk and injected into context *only* at the verification step (`_verify`). While the agent is still gathering evidence those instructions stay out of the window entirely, so the gathering turns stay lean and the model isn't distracted by instructions it doesn't need yet.

### b. Agentic pattern

**Single-agent tool-calling loop, not multi-agent.** One model runs the whole loop: it chooses among `search_knowledge_base`, `get_weather`, `calculator`, and `finish`, reads the ledger, and decides whether to search again, use a tool, or conclude. Iterations are capped (`max_iters=5`) so it cannot run forever, and if it can't ground an answer it returns an explicit refusal instead of guessing. I checked this choice against the five structural failure modes that usually push a design toward multiple agents:

- **Context saturation** - the real risk for this task, handled by the evidence ledger above rather than by giving a second agent its own context window. One capped, compacted context holds this workload comfortably.
- **Sequential bottleneck** - the sub-steps (retrieve, then compute, then verify) are genuinely sequential; verification depends on the gathered evidence, so parallel agents would have nothing to run in parallel.
- **Skill dilution** - with four tools in one narrow domain, a single agent isn't overloaded; splitting tools across agents would add coordination cost for no gain in focus.
- **Self-verification paradox** - normally the strongest argument for a separate verifier. I defuse it without a second agent by grounding verification in an *external* artifact: the verifier is handed the evidence ledger and asked whether each claim is supported by it, not asked whether it feels confident. Checking claims against retrieved text is an easier, different task than producing them, and it's the ledger, not the model's own conviction, that decides the verdict.
- **Single point of failure** - a multi-agent setup adds failure points (message passing, orchestration) about as often as it removes them; at this size, one loop with a hard iteration cap and a refusal fallback is more robust than several agents coordinating.

If the system grew (many more tools, or genuinely parallel sub-questions) I'd revisit this and peel exploration off into a sub-agent. At this scope a single agent is the right call.

### c. Evaluation harness

`week16/eval_harness.py` is written from scratch and runs a fixed suite of seven queries; the latest run is saved in `week16/results.md`. It measures:

- **Task completion rate** - did the final answer pass a per-case check (right number, temperature present, key concepts named, or a correct refusal). Latest: **7/7 (100%)**.
- **Tool-call correctness** - was the expected tool actually called, with well-formed arguments. All 7 correct.
- **Trajectory length** - iterations per query; avg **3.3**, with the three refusal/injection cases running to the cap (5) as expected and the four clean cases finishing in 2.
- **Failure log**, classified as **hard** (crashed / no answer), **soft** (finished but wrong or incomplete), or **cascading_soft** (took a corrupted or failed tool result at face value and fabricated an answer from it, a soft failure caused by an upstream one). Latest: **none**, including the two injected-failure cases, which the agent recognized and refused rather than fabricating from.

### Additional requirements

**Token & cost accounting (per query, with baseline).** The harness records prompt/completion tokens per query and prices them at gemini-3.1-flash-lite rates ($0.25/1M in, $1.50/1M out); per-query cost runs ~$0.0003 to $0.0018 (full table in `results.md`). To show what the loop costs over the Week 15 approach, it also runs each answerable query through a single-pass W15-style baseline. On the five comparable queries: **agent 10,493 tokens ($0.0035) vs baseline 3,225 tokens ($0.0011)**, about **3.3x the tokens**, which is the price of re-retrieval plus one verification call per query. All seven agent queries together cost **$0.0068**. That overhead buys recovery from a bad first retrieval and a refusal instead of a hallucination.

**Failure injection test.** Two cases inject faults into retrieval (`inject_failure` in `run_agent`): `search_unavailable` makes the knowledge-base tool return an error, and `malformed` returns a garbled, unreadable passage. The correct behavior in both is to notice the evidence is unusable and refuse; the classifier logs `cascading_soft` if the agent instead fabricates from the bad input. In the latest run it refused both, so the failure log is empty on purpose, not for lack of trying.

**Tool vs agent boundary.** The weather lookup shows where I drew the line. `get_weather` is a *tool*, not an agent: it takes a city, makes two bounded HTTP calls to Open-Meteo (geocode, then forecast), and returns a value, with no looping and no choosing what to do next. The *agent* is only the outer loop that decides *whether and when* to call the weather tool, what to do with its result, and when the question is fully answered. The rule I followed: a step with a fixed input to output contract that makes no autonomous decisions is a tool; a step that decides its own next action from intermediate results is (part of) the agent.

### Running the evaluation harness

From the project root, with `GEMINI_API_KEY` set in `.env`:

```bash
.venv/bin/python -m week16.eval_harness
```

It ingests `docs/`, runs the suite (pausing briefly between queries to respect free-tier rate limits), and rewrites `week16/results.md`.