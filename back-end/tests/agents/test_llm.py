import httpx
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from app.agents.llm import llm


def test_llm_falls_back_only_on_rate_limit_and_timeout():
    assert llm.exceptions_to_handle == (ChatGoogleGenerativeAIError, httpx.TimeoutException)


def test_llm_has_exactly_one_fallback_model_configured():
    assert len(llm.fallbacks) == 1


def test_primary_and_fallback_use_different_models():
    primary_model = llm.runnable.model
    fallback_model = llm.fallbacks[0].model

    assert primary_model != fallback_model
