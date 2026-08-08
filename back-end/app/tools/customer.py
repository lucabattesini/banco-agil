import pandas as pd

from app.config import CLIENTES_CSV


def validate_customer(cpf: str, birth_date: str) -> dict:
    df = pd.read_csv(CLIENTES_CSV, dtype={"cpf": str})
    match = df[df["cpf"] == cpf]

    if match.empty:
        return {"success": False, "error": "cpf_not_found"}

    customer = match.iloc[0]
    if str(customer["data_nascimento"]) != birth_date:
        return {"success": False, "error": "birth_date_mismatch"}

    return {"success": True, "customer": customer.to_dict()}
