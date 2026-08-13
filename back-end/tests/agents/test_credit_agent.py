from langchain_core.messages import AIMessage

from app.agents.credit.agent import _debug_post_model_hook


def test_clears_score_recalculated_after_a_final_text_reply():
    state = {
        "messages": [AIMessage(content="Seu novo score é 620 e o pedido foi aprovado.")],
        "score_recalculated": True,
    }

    assert _debug_post_model_hook(state) == {"score_recalculated": False}


def test_keeps_the_flag_while_still_mid_turn_on_a_tool_call():
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{"name": "register_limit_increase_request", "args": {}, "id": "t1"}],
            )
        ],
        "score_recalculated": True,
    }

    assert _debug_post_model_hook(state) == {}


def test_does_nothing_when_there_was_no_pending_recalculation():
    state = {
        "messages": [AIMessage(content="Seu limite atual é R$5000.")],
        "score_recalculated": False,
    }

    assert _debug_post_model_hook(state) == {}
