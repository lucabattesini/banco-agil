import logging

from langchain_core.messages import HumanMessage

from app.graph.builder import graph
from app.schemas.routes import ChatRequest, ChatResponse

logger = logging.getLogger("banco_agil.chat")


def handle_chat_message(request: ChatRequest) -> ChatResponse:
    try:
        result = graph.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config={"configurable": {"thread_id": request.session_id}, "recursion_limit": 15},
        )
    except Exception:
        logger.exception("Falha ao processar mensagem (session_id=%r)", request.session_id)
        return ChatResponse(reply="Desculpe, tivemos um problema técnico, tente novamente mais tarde.")

    return ChatResponse(
        reply=result["messages"][-1].text,
        end=result.get("conversation_ended", False),
    )
