import groq
from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, GROQ_FALLBACK_MODEL, GROQ_MODEL

_PER_CALL_TIMEOUT_SECONDS = 30

_primary = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, timeout=_PER_CALL_TIMEOUT_SECONDS)
_fallback = ChatGroq(model=GROQ_FALLBACK_MODEL, api_key=GROQ_API_KEY, timeout=_PER_CALL_TIMEOUT_SECONDS)

llm = _primary.with_fallbacks(
    [_fallback],
    exceptions_to_handle=(groq.RateLimitError, groq.APITimeoutError),
)
