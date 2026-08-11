import pandas as pd

from app.repositories import solicitacoes_repository
from app.schemas.tables import LimitIncreaseRequest


def test_create_appends_a_row(tmp_csvs):
    request = LimitIncreaseRequest(
        cpf_cliente="11111111111",
        data_hora_solicitacao="2026-01-01T00:00:00+00:00",
        limite_atual=5000.0,
        novo_limite_solicitado=6000.0,
        status_pedido="aprovado",
    )

    solicitacoes_repository.create(request)

    df = pd.read_csv(tmp_csvs["solicitacoes"], dtype={"cpf_cliente": str})
    assert len(df) == 1
    assert df.iloc[0]["cpf_cliente"] == "11111111111"
    assert df.iloc[0]["status_pedido"] == "aprovado"
