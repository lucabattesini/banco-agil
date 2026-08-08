from datetime import datetime, timezone

import pandas as pd

from app.config import CLIENTES_CSV, SCORE_LIMITE_CSV, SOLICITACOES_CSV


def get_credit_limit(cpf: str) -> dict:
    df = pd.read_csv(CLIENTES_CSV, dtype={"cpf": str})
    match = df[df["cpf"] == cpf]

    if match.empty:
        return {"success": False, "error": "not_found"}

    return {"success": True, "limite_credito": float(match.iloc[0]["limite_credito"])}


def check_score_eligibility(score: int, requested_limit: float) -> dict:
    df = pd.read_csv(SCORE_LIMITE_CSV)
    match = df[(df["score_min"] <= score) & (score <= df["score_max"])]

    if match.empty:
        return {"eligible": False, "limite_maximo": 0.0}

    limite_maximo = float(match.iloc[0]["limite_maximo"])
    return {"eligible": requested_limit <= limite_maximo, "limite_maximo": limite_maximo}


def register_limit_increase_request(cpf: str, score: int, current_limit: float, requested_limit: float) -> dict:
    eligibility = check_score_eligibility(score, requested_limit)
    status = "aprovado" if eligibility["eligible"] else "rejeitado"

    df = pd.read_csv(SOLICITACOES_CSV, dtype={"cpf_cliente": str})
    new_row = {
        "cpf_cliente": cpf,
        "data_hora_solicitacao": datetime.now(timezone.utc).isoformat(),
        "limite_atual": current_limit,
        "novo_limite_solicitado": requested_limit,
        "status_pedido": status,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(SOLICITACOES_CSV, index=False)

    return {"success": True, "status": status}
