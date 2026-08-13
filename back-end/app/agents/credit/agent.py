from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, create_react_agent

from app.agents.credit.prompt import build_credit_prompt
from app.errors import handle_tool_errors
from app.agents.llm import llm
from app.agents.message_history import trim_history
from app.schemas.state import GraphState
from app.tools.credit import get_credit_limit, register_limit_increase_request
from app.tools.handoffs import route_to_score_interview
from app.tools.system import end_conversation


def _credit_prompt(state: GraphState) -> list:
    system = build_credit_prompt(customer=state["customer"])
    return [SystemMessage(content=system), *trim_history(state["messages"])]


credit_agent = create_react_agent(
    model=llm,
    tools=ToolNode(
        [
            get_credit_limit,
            register_limit_increase_request,
            route_to_score_interview,
            end_conversation,
        ],
        handle_tool_errors=handle_tool_errors,
    ),
    prompt=_credit_prompt,
    state_schema=GraphState,
)
