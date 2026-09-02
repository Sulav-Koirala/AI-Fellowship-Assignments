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

## Project Structure

Week 15/

├── README.MD

├── Architecture_diagram.png

├── requirements.txt

├── .env

├── .env.example

├── .gitignore

├── docker-compose.yml

├── Dockerfile

├── .venv/ # local virtual environment (not committed)

├── docs/ # source documents for RAG (replace with your own)

├── app/

│ ├── config.py # env vars, provider configs

│ ├── prompts.py # system prompt, message builder

│ ├── llm_client.py # async OpenAI-compatible client (Gemini / vLLM)

│ ├── structured_output.py # JSON-schema-validated responses

│ ├── tools.py # get_weather, calculator, tool dispatch

│ ├── rag.py # chunking, embeddings, Chroma retrieval

│ └── backend.py # FastAPI app: /chat endpoint, retry/fallback/cache

└── ui/

└── app.py # Streamlit chat frontend

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
vllm serve mistralai/Mistral-7B-Instruct-v0.2 --port 8001
```

This exposes an OpenAI-compatible server at `http://localhost:8001/v1`, matching `VLLM_BASE_URL` in `.env`. The backend automatically falls back to this model if the Gemini API fails or times out.

## Design Notes

- **Why Gemini Flash-Lite:** free tier, generally available (not preview), supports tool calling and structured output, and is inexpensive enough for heavy iteration during development.
- **Why low temperature (0.1–0.2):** this is a fact-grounded RAG assistant; consistency matters more than creative variation.
- **RAG grounding:** the system prompt explicitly instructs the model to defer to retrieved context over its own prior knowledge, and to say "I don't know" rather than fabricate an answer when context is insufficient.
- **ONNX conversion - not applicable:** the local model is served via vLLM, which uses its own optimized CUDA kernels and continuous batching for inference. Converting to ONNX would bypass these optimizations rather than improve on them, so it was not used.
- **Caching:** identical prompts are cached in-memory (`response_cache`) keyed by a SHA-256 hash, avoiding repeat LLM calls for repeated questions.

## Known Limitations

- The in-memory cache and rate limiter reset on restart (no Redis backing).
- `calculator()` uses Python's `eval` in a restricted namespace, acceptable for this assignment's scope, not intended for production reuse.
- Free-tier Gemini rate limits (~30 requests/minute) may throttle heavy local testing; the retry logic handles this gracefully.
- The backend (port 8000) and the local vLLM server (port 8001) must run on different ports, they cannot both bind to 8000 on the same machine.