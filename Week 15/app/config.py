import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_BASE_URL = os.environ.get("GEMINI_BASE_URL")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")

VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL")
VLLM_MODEL = os.environ.get("VLLM_MODEL")

CHROMA_PATH = os.environ.get("CHROMA_PATH")

PRIMARY = {"base_url": GEMINI_BASE_URL, "model": GEMINI_MODEL, "api_key": GEMINI_API_KEY}
FALLBACK = {"base_url": VLLM_BASE_URL, "model": VLLM_MODEL, "api_key": "not-needed"}