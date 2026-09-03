import json
from pydantic import BaseModel, ValidationError
from app.llm_client import ask
from app.prompts import build_messages

class AssistantAnswer(BaseModel):
    answer: str
    sources: list[str] = []
    confidence: float

async def ask_structured_from_messages(messages, use_fallback=False) -> AssistantAnswer:
    messages = messages + [{"role": "user", "content":
        "Respond with ONLY a valid JSON object, no markdown fences, matching exactly this shape:\n"
        '{"answer": string, "sources": string[], "confidence": number between 0 and 1}'}]

    last_error = None
    for attempt in range(2):
        msg = await ask(messages, temperature=0.1, use_fallback=use_fallback)
        raw = (msg.content or "").strip().removeprefix("```json").removesuffix("```").strip()
        try:
            return AssistantAnswer.model_validate_json(raw)
        except (ValidationError, json.JSONDecodeError) as e:
            last_error = e
            messages.append({"role": "user", "content": f"That wasn't valid JSON matching the schema. Error: {e}. Try again, JSON only."})
    raise ValueError(f"Model failed to return valid structured output: {last_error}")