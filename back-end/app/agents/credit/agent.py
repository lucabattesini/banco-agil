from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode, create_react_agent

from app.agents.credit.prompt import build_credit_prompt
from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.errors import handle_tool_errors
from app.schemas.state import GraphState
from app.tools.capture import capture_requested_limit
from app.tools.credit import get_credit_limit, register_limit_increase_request
from app.tools.handoffs import return_to_triage, route_to_score_interview
from app.tools.system import end_conversation

llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)


def _credit_prompt(state: GraphState) -> list:
    system = build_credit_prompt(
        customer=state["customer"],
        pending_requested_limit=state.get("pending_requested_limit"),
    )
    return [SystemMessage(content=system), *state["messages"]]


credit_agent = create_react_agent(
    model=llm,
    tools=ToolNode(
        [
            get_credit_limit,
            capture_requested_limit,
            register_limit_increase_request,
            route_to_score_interview,
            return_to_triage,
            end_conversation,
        ],
        handle_tool_errors=handle_tool_errors,
    ),
    prompt=_credit_prompt,
    state_schema=GraphState,
)
