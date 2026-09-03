import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.llm_client import ask
from app.prompts import build_messages
from app.rag import retrieve, ingest_docs_folder
from app.tools import TOOLS, execute_tool_calls
from app.struct_output import ask_structured_from_messages, AssistantAnswer

@asynccontextmanager
async def lifespan(app: FastAPI):
    ingest_docs_folder("docs")
    yield

app = FastAPI(title="AI Assistant Backend", lifespan=lifespan)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
response_cache: dict[str, str] = {}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8),
       retry=retry_if_exception_type(Exception))
async def call_model(messages, use_fallback=False) -> AssistantAnswer:
    msg = await ask(messages, temperature=0.2, tools=TOOLS, use_fallback=use_fallback)

    if msg.tool_calls:
        assistant_msg = {
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        }
        messages.append(assistant_msg)
        messages = await execute_tool_calls(messages, msg.tool_calls)

    last_user_msg = next(m["content"] for m in reversed(messages) if m["role"] == "user")
    context = next((m["content"].removeprefix("Context:\n") for m in messages
                     if m["role"] == "system" and m["content"].startswith("Context:")), "")
    return await ask_structured_from_messages(messages, use_fallback=use_fallback)

async def call_with_fallback(messages):
    try:
        return await call_model(messages, use_fallback=False)
    except Exception:
        try:
            return await call_model(messages, use_fallback=True)
        except Exception:
            raise HTTPException(status_code=503, detail="Both primary and fallback models are unavailable.")


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, body: ChatRequest):
    key = hashlib.sha256(body.message.encode()).hexdigest()
    if key in response_cache:
        return {"reply": response_cache[key], "cached": True}

    hits = retrieve(body.message)
    context = "\n\n".join(f"[{meta['source']}] {doc}" for doc, meta in hits)
    messages = build_messages(body.message, context=context)

    try:
        reply = await call_with_fallback(messages)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong processing your request.")

    payload = {"answer": reply.answer, "sources": reply.sources, "confidence": reply.confidence}
    response_cache[key] = payload
    return {"reply": payload, "cached": False}


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return {"error": "Too many requests, please slow down."}