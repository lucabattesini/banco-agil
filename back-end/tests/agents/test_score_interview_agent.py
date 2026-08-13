from langchain_core.messages import AIMessage

from app.agents.score_interview.agent import _post_model_hook


def test_hands_off_to_credit_after_a_final_text_reply_following_a_recalculation():
    state = {
        "messages": [AIMessage(content="Sua pontuação foi atualizada com sucesso!")],
        "score_recalculated": True,
    }

    assert _post_model_hook(state) == {"current_agent": "credit"}


def test_does_not_hand_off_when_the_reply_is_a_tool_call():
    state = {
        "messages": [AIMessage(content="", tool_calls=[{"name": "calculate_credit_score", "args": {}, "id": "t1"}])],
        "score_recalculated": True,
    }

    assert _post_model_hook(state) == {}


def test_does_not_hand_off_when_the_score_was_not_recalculated():
    state = {
        "messages": [AIMessage(content="Poderia me informar sua renda mensal?")],
        "score_recalculated": False,
    }

    assert _post_model_hook(state) == {}
