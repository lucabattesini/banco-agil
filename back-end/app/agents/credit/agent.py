from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.tools.capture import capture_requested_limit
from app.tools.credit import get_credit_limit, register_limit_increase_request
from app.tools.handoffs import route_to_score_interview
from app.tools.system import end_conversation

llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)

credit_agent = llm.bind_tools(
    [
        get_credit_limit,
        capture_requested_limit,
        register_limit_increase_request,
        route_to_score_interview,
        end_conversation,
    ]
)
