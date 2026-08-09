from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from app.agents.score_interview.prompt import build_score_interview_prompt
from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.schemas.state import GraphState
from app.tools.capture import capture_interview_data
from app.tools.handoffs import route_to_credit
from app.tools.score import calculate_credit_score
from app.tools.system import end_conversation

llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)


def _score_interview_prompt(state: GraphState) -> list:
    system = build_score_interview_prompt(
        customer=state["customer"],
        pending_income=state.get("pending_income"),
        pending_employment_type=state.get("pending_employment_type"),
        pending_expenses=state.get("pending_expenses"),
        pending_dependents=state.get("pending_dependents"),
        pending_has_debt=state.get("pending_has_debt"),
    )
    return [SystemMessage(content=system), *state["messages"]]


score_interview_agent = create_react_agent(
    model=llm,
    tools=[
        capture_interview_data,
        calculate_credit_score,
        route_to_credit,
        end_conversation,
    ],
    prompt=_score_interview_prompt,
    state_schema=GraphState,
)
