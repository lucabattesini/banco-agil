import pandas as pd

from app.config import CLIENTES_CSV

PESO_RENDA = 30
PESO_EMPREGO = {"formal": 300, "autônomo": 200, "desempregado": 0}
PESO_DEPENDENTES = {0: 100, 1: 80, 2: 60}
PESO_DEPENDENTES_3_PLUS = 30
PESO_DIVIDA_SIM = -100
PESO_DIVIDA_NAO = 100


def calculate_credit_score(
    income: float,
    employment_type: str,
    expenses: float,
    dependents: int,
    has_debt: bool,
) -> dict:
    peso_dependentes = PESO_DEPENDENTES.get(dependents, PESO_DEPENDENTES_3_PLUS)
    peso_divida = PESO_DIVIDA_SIM if has_debt else PESO_DIVIDA_NAO

    score = (
        (income / (expenses + 1)) * PESO_RENDA
        + PESO_EMPREGO[employment_type]
        + peso_dependentes
        + peso_divida
    )

    return {"score": int(max(0, min(1000, score)))}


def update_customer_score(cpf: str, new_score: int) -> dict:
    df = pd.read_csv(CLIENTES_CSV, dtype={"cpf": str})

    if cpf not in df["cpf"].values:
        return {"success": False, "error": "not_found"}

    df.loc[df["cpf"] == cpf, "score"] = new_score
    df.to_csv(CLIENTES_CSV, index=False)

    return {"success": True}
