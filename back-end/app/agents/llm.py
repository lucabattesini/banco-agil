import httpx
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from app.config import GEMINI_API_KEY, GEMINI_FALLBACK_MODEL, GEMINI_MODEL

_PER_CALL_TIMEOUT_SECONDS = 30

_primary = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GEMINI_API_KEY,
    timeout=_PER_CALL_TIMEOUT_SECONDS,
    reasoning_effort="low",
)
_fallback = ChatGoogleGenerativeAI(
    model=GEMINI_FALLBACK_MODEL,
    google_api_key=GEMINI_API_KEY,
    timeout=_PER_CALL_TIMEOUT_SECONDS,
    reasoning_effort="low",
)

llm = _primary.with_fallbacks(
    [_fallback],
    exceptions_to_handle=(ChatGoogleGenerativeAIError, httpx.TimeoutException),
)
