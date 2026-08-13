from langchain_core.messages import trim_messages

MAX_HISTORY_TOKENS = 3000


def trim_history(messages: list) -> list:
    return trim_messages(
        messages,
        max_tokens=MAX_HISTORY_TOKENS,
        token_counter="approximate",
        strategy="last",
        start_on="human",
        allow_partial=False,
    )
