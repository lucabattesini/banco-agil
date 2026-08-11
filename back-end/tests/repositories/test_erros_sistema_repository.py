import pandas as pd

from app.repositories import erros_sistema_repository
from app.schemas.tables import SystemErrorLog

ROW = SystemErrorLog(
    timestamp="2026-01-01T00:00:00+00:00",
    tool="some_tool",
    exception_type="FileNotFoundError",
    message="arquivo não encontrado",
)


def test_create_appends_a_row(tmp_csvs):
    erros_sistema_repository.create(ROW)

    df = pd.read_csv(tmp_csvs["erros_sistema"])
    assert len(df) == 1
    assert df.iloc[0]["tool"] == "some_tool"


def test_create_self_heals_when_file_does_not_exist_yet(tmp_path, monkeypatch):
    missing_csv = tmp_path / "does_not_exist_yet.csv"
    monkeypatch.setattr(erros_sistema_repository, "ERROS_SISTEMA_CSV", missing_csv)

    assert not missing_csv.exists()

    erros_sistema_repository.create(ROW)

    df = pd.read_csv(missing_csv)
    assert len(df) == 1
    assert list(df.columns) == list(SystemErrorLog.model_fields.keys())
