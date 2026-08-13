from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph

from app.agents.credit.agent import credit_agent
from app.agents.exchange.agent import exchange_agent
from app.agents.score_interview.agent import score_interview_agent
from app.agents.triage.agent import triage_agent
from app.schemas.state import GraphState

builder = StateGraph(GraphState)
builder.add_node("triage", triage_agent)
builder.add_node("credit", credit_agent)
builder.add_node("score_interview", score_interview_agent)
builder.add_node("exchange", exchange_agent)
builder.add_edge(START, "triage")

graph = builder.compile(checkpointer=MemorySaver())
