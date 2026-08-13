from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agents.message_history import trim_history


def test_trim_history_keeps_everything_when_under_the_budget():
    messages = [HumanMessage(content="Oi"), AIMessage(content="Olá! Como posso ajudar?")]

    assert trim_history(messages) == messages


def test_trim_history_drops_oldest_turns_first():
    old_turn = [HumanMessage(content="x" * 8000), AIMessage(content="y" * 8000)]
    recent_turn = [HumanMessage(content="Quero ver meu limite"), AIMessage(content="Seu limite é R$5000")]

    trimmed = trim_history(old_turn + recent_turn)

    assert old_turn[0] not in trimmed
    assert recent_turn[0] in trimmed
    assert recent_turn[1] in trimmed


def test_trim_history_never_leaves_an_orphaned_tool_message():
    old_turn = [HumanMessage(content="x" * 8000), AIMessage(content="y" * 8000)]
    recent_turn = [
        HumanMessage(content="Quero ver meu limite"),
        AIMessage(content="", tool_calls=[{"name": "get_credit_limit", "args": {}, "id": "t1"}]),
        ToolMessage(content="R$5000", tool_call_id="t1"),
    ]

    trimmed = trim_history(old_turn + recent_turn)

    for i, message in enumerate(trimmed):
        if isinstance(message, ToolMessage):
            assert i > 0
            previous = trimmed[i - 1]
            assert isinstance(previous, AIMessage)
            assert any(call["id"] == message.tool_call_id for call in previous.tool_calls)
