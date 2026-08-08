from typing import Optional


def capture_auth_data(cpf: Optional[str] = None, birth_date: Optional[str] = None) -> dict:
    return {"cpf": cpf, "birth_date": birth_date}
