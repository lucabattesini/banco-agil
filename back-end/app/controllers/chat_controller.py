from langchain_core.messages import HumanMessage

from app.graph.builder import graph
from app.schemas.routes import ChatRequest, ChatResponse


def handle_chat_message(request: ChatRequest) -> ChatResponse:
    try:
        result = graph.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config={"configurable": {"thread_id": request.session_id}},
        )
    except Exception:
        return ChatResponse(reply="Desculpe, tivemos um problema técnico, tente novamente mais tarde.")

    return ChatResponse(
        reply=result["messages"][-1].content,
        end=result.get("conversation_ended", False),
    )
