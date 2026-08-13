from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, create_react_agent

from app.agents.triage.prompt import build_triage_prompt
from app.errors import handle_tool_errors
from app.agents.llm import llm
from app.agents.message_history import trim_history
from app.schemas.state import GraphState
from app.tools.customer import validate_customer
from app.tools.handoffs import route_to_credit, route_to_exchange
from app.tools.system import end_conversation


def _triage_prompt(state: GraphState) -> list:
    system = build_triage_prompt(
        auth_attempts=state.get("auth_attempts", 0),
        customer=state.get("customer"),
    )
    return [SystemMessage(content=system), *trim_history(state["messages"])]


triage_agent = create_react_agent(
    model=llm,
    tools=ToolNode(
        [
            validate_customer,
            end_conversation,
            route_to_credit,
            route_to_exchange,
        ],
        handle_tool_errors=handle_tool_errors,
    ),
    prompt=_triage_prompt,
    state_schema=GraphState,
)
