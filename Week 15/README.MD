# Week 15 Assignment - AI Assistant

A retrieval-augmented, tool-using AI assistant with a production backend (async, retry, rate limiting, fallback, caching) and a Streamlit UI, built for Task 1 (Applied AI) and Task 2 (Engineering AI Systems).

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