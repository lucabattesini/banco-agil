import asyncio

import httpx
import pytest
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from app.controllers import chat_controller
from app.schemas.routes import ChatRequest

_REQUEST = ChatRequest(message="Oi", session_id="test-session")


def _rate_limit_error() -> ChatGoogleGenerativeAIError:
    return ChatGoogleGenerativeAIError("rate limit exceeded")


def _timeout_error() -> httpx.TimeoutException:
    request = httpx.Request("POST", "https://generativelanguage.googleapis.com")
    return httpx.ReadTimeout("timed out", request=request)


def test_returns_busy_message_on_rate_limit_error(monkeypatch):
    async def fake_ainvoke(*args, **kwargs):
        raise _rate_limit_error()

    monkeypatch.setattr(chat_controller.graph, "ainvoke", fake_ainvoke)

    result = asyncio.run(chat_controller.handle_chat_message(_REQUEST))

    assert result.reply == chat_controller._BUSY_MESSAGE


def test_returns_busy_message_on_provider_timeout(monkeypatch):
    async def fake_ainvoke(*args, **kwargs):
        raise _timeout_error()

    monkeypatch.setattr(chat_controller.graph, "ainvoke", fake_ainvoke)

    result = asyncio.run(chat_controller.handle_chat_message(_REQUEST))

    assert result.reply == chat_controller._BUSY_MESSAGE


def test_returns_busy_message_when_overall_deadline_is_exceeded(monkeypatch):
    monkeypatch.setattr(chat_controller, "REQUEST_TIMEOUT_SECONDS", 0.05)

    async def slow_ainvoke(*args, **kwargs):
        await asyncio.sleep(1)

    monkeypatch.setattr(chat_controller.graph, "ainvoke", slow_ainvoke)

    result = asyncio.run(chat_controller.handle_chat_message(_REQUEST))

    assert result.reply == chat_controller._BUSY_MESSAGE


def test_returns_generic_message_on_unexpected_error(monkeypatch):
    async def fake_ainvoke(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(chat_controller.graph, "ainvoke", fake_ainvoke)

    result = asyncio.run(chat_controller.handle_chat_message(_REQUEST))

    assert result.reply == "Desculpe, tivemos um problema técnico, tente novamente mais tarde."


def test_returns_reply_on_success(monkeypatch):
    class _FakeMessage:
        text = "Olá! Como posso ajudar?"

    async def fake_ainvoke(*args, **kwargs):
        return {"messages": [_FakeMessage()], "conversation_ended": False}

    monkeypatch.setattr(chat_controller.graph, "ainvoke", fake_ainvoke)

    result = asyncio.run(chat_controller.handle_chat_message(_REQUEST))

    assert result.reply == "Olá! Como posso ajudar?"
    assert result.end is False
