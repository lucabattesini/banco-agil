from typing import Optional

import pandas as pd

from app.config import CLIENTES_CSV
from app.schemas.tables import Customer


def find_by_cpf(cpf: str) -> Optional[Customer]:
    df = pd.read_csv(CLIENTES_CSV, dtype={"cpf": str})
    match = df[df["cpf"] == cpf]
    return Customer(**match.iloc[0].to_dict()) if not match.empty else None


def update_score(cpf: str, new_score: int) -> bool:
    df = pd.read_csv(CLIENTES_CSV, dtype={"cpf": str})

    if cpf not in df["cpf"].values:
        return False

    df.loc[df["cpf"] == cpf, "score"] = new_score
    df.to_csv(CLIENTES_CSV, index=False)

    return True
