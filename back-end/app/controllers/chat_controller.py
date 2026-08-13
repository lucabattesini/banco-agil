import asyncio
import logging

import httpx
from langchain_core.messages import HumanMessage
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from app.graph.builder import graph
from app.schemas.routes import ChatRequest, ChatResponse

logger = logging.getLogger("banco_agil.chat")

REQUEST_TIMEOUT_SECONDS = 40
_BUSY_MESSAGE = "Estamos com um volume alto de atendimentos no momento. Por favor, tente novamente em alguns instantes."


async def handle_chat_message(request: ChatRequest) -> ChatResponse:
    try:
        result = await asyncio.wait_for(
            graph.ainvoke(
                {"messages": [HumanMessage(content=request.message)], "last_bounced_agent": None},
                config={"configurable": {"thread_id": request.session_id}, "recursion_limit": 15},
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except (asyncio.TimeoutError, ChatGoogleGenerativeAIError, httpx.TimeoutException) as exc:
        logger.warning(
            "Rate limit/timeout do provedor (session_id=%r): %s: %s",
            request.session_id,
            type(exc).__name__,
            exc,
        )
        return ChatResponse(reply=_BUSY_MESSAGE)
    except Exception:
        logger.exception("Falha ao processar mensagem (session_id=%r)", request.session_id)
        return ChatResponse(reply="Desculpe, tivemos um problema técnico, tente novamente mais tarde.")

    return ChatResponse(
        reply=result["messages"][-1].text,
        end=result.get("conversation_ended", False),
    )
