from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, create_react_agent

from app.agents.score_interview.prompt import build_score_interview_prompt
from app.errors import handle_tool_errors
from app.agents.llm import llm
from app.agents.message_history import trim_history
from app.schemas.state import GraphState
from app.tools.handoffs import return_to_triage, route_to_credit
from app.tools.score import calculate_credit_score
from app.tools.system import end_conversation


def _score_interview_prompt(state: GraphState) -> list:
    system = build_score_interview_prompt(customer=state["customer"])
    return [SystemMessage(content=system), *trim_history(state["messages"])]


score_interview_agent = create_react_agent(
    model=llm,
    tools=ToolNode(
        [
            calculate_credit_score,
            route_to_credit,
            return_to_triage,
            end_conversation,
        ],
        handle_tool_errors=handle_tool_errors,
    ),
    prompt=_score_interview_prompt,
    state_schema=GraphState,
)
