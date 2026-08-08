import pandas as pd

from app.config import CLIENTES_CSV


def update_customer_score(cpf: str, new_score: int) -> dict:
    df = pd.read_csv(CLIENTES_CSV, dtype={"cpf": str})

    if cpf not in df["cpf"].values:
        return {"success": False, "error": "not_found"}

    df.loc[df["cpf"] == cpf, "score"] = new_score
    df.to_csv(CLIENTES_CSV, index=False)

    return {"success": True}
