import pandas as pd

from app.repositories import clientes_repository
from app.schemas.tables import Customer


def test_find_by_cpf_returns_customer_when_found(tmp_csvs):
    customer = clientes_repository.find_by_cpf("11111111111")

    assert isinstance(customer, Customer)
    assert customer.nome == "Ana Silva"
    assert customer.score == 750


def test_find_by_cpf_returns_none_when_not_found(tmp_csvs):
    assert clientes_repository.find_by_cpf("99999999999") is None


def test_update_score_returns_false_for_unknown_cpf(tmp_csvs):
    assert clientes_repository.update_score("99999999999", 900) is False


def test_update_score_persists_new_score(tmp_csvs):
    result = clientes_repository.update_score("11111111111", 900)

    assert result is True
    df = pd.read_csv(tmp_csvs["clientes"], dtype={"cpf": str})
    assert int(df.loc[df["cpf"] == "11111111111", "score"].iloc[0]) == 900
