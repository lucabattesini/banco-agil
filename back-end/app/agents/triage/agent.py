from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from app.agents.triage.prompt import build_triage_prompt
from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.schemas.state import GraphState
from app.tools.capture import capture_auth_data
from app.tools.customer import validate_customer
from app.tools.handoffs import route_to_credit, route_to_exchange, route_to_score_interview
from app.tools.system import end_conversation

llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY)


def _triage_prompt(state: GraphState) -> list:
    system = build_triage_prompt(
        auth_attempts=state["auth_attempts"],
        pending_cpf=state.get("pending_cpf"),
        pending_birth_date=state.get("pending_birth_date"),
    )
    return [SystemMessage(content=system), *state["messages"]]


triage_agent = create_react_agent(
    model=llm,
    tools=[
        capture_auth_data,
        validate_customer,
        end_conversation,
        route_to_credit,
        route_to_score_interview,
        route_to_exchange,
    ],
    prompt=_triage_prompt,
    state_schema=GraphState,
)
