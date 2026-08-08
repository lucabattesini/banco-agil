from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CLIENTES_CSV = DATA_DIR / "clientes.csv"


def update_customer_score(cpf: str, new_score: int) -> dict:
    df = pd.read_csv(CLIENTES_CSV, dtype={"cpf": str})

    if cpf not in df["cpf"].values:
        return {"success": False, "error": "not_found"}

    df.loc[df["cpf"] == cpf, "score"] = new_score
    df.to_csv(CLIENTES_CSV, index=False)

    return {"success": True}
