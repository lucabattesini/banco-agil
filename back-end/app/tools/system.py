from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.types import Command


def end_conversation(tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    """End the conversation.

    Use when the customer explicitly asks to stop, or when the current flow reaches its natural
    conclusion (e.g. authentication failed with no attempts left). After calling this, send the
    customer a friendly closing message in the same turn — do not call speculatively.
    """
    return Command(
        update={
            "conversation_ended": True,
            "messages": [ToolMessage(content="Atendimento encerrado.", tool_call_id=tool_call_id)],
        }
    )
