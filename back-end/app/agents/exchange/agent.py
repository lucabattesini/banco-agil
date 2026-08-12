from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode, create_react_agent

from app.agents.exchange.prompt import build_exchange_prompt
from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.errors import handle_tool_errors
from app.schemas.state import GraphState
from app.tools.exchange import get_exchange_rate
from app.tools.system import end_conversation

llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)


def _exchange_prompt(state: GraphState) -> list:
    system = build_exchange_prompt(customer=state["customer"])
    return [SystemMessage(content=system), *state["messages"]]


exchange_agent = create_react_agent(
    model=llm,
    tools=ToolNode(
        [
            get_exchange_rate,
            end_conversation,
        ],
        handle_tool_errors=handle_tool_errors,
    ),
    prompt=_exchange_prompt,
    state_schema=GraphState,
)
