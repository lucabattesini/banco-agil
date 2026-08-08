from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.tools.capture import capture_auth_data
from app.tools.customer import validate_customer
from app.tools.handoffs import route_to_credit, route_to_exchange, route_to_score_interview
from app.tools.system import end_conversation

llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY)

triage_agent = llm.bind_tools(
    [
        capture_auth_data,
        validate_customer,
        end_conversation,
        route_to_credit,
        route_to_score_interview,
        route_to_exchange,
    ]
)
