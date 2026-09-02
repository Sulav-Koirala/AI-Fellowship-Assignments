from openai import AsyncOpenAI
from app.config import PRIMARY, FALLBACK

def get_client(provider: dict) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=provider["api_key"], base_url=provider["base_url"])

primary_client = get_client(PRIMARY)
fallback_client = get_client(FALLBACK)

async def ask(messages, temperature=0.2, top_p=1.0, use_fallback=False, tools=None):
    provider = FALLBACK if use_fallback else PRIMARY
    client = fallback_client if use_fallback else primary_client
    kwargs = dict(model=provider["model"], messages=messages, temperature=temperature, top_p=top_p)
    if tools:
        kwargs["tools"] = tools
    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message