import pandas as pd
import pytest

import app.repositories.clientes_repository as clientes_repo
import app.repositories.erros_sistema_repository as erros_repo
import app.repositories.score_limite_repository as score_limite_repo
import app.repositories.solicitacoes_repository as solicitacoes_repo
from app.schemas.tables import LimitIncreaseRequest, SystemErrorLog

CUSTOMERS = [
    {"cpf": "11111111111", "nome": "Ana Silva", "data_nascimento": "1990-05-12", "score": 750, "limite_credito": 5000.0},
    {"cpf": "22222222222", "nome": "Bruno Costa", "data_nascimento": "1985-11-30", "score": 420, "limite_credito": 1500.0},
]

SCORE_LIMITS = [
    {"score_min": 0, "score_max": 200, "limite_maximo": 500.0},
    {"score_min": 201, "score_max": 400, "limite_maximo": 1500.0},
    {"score_min": 401, "score_max": 600, "limite_maximo": 3000.0},
    {"score_min": 601, "score_max": 800, "limite_maximo": 6000.0},
    {"score_min": 801, "score_max": 1000, "limite_maximo": 12000.0},
]


@pytest.fixture
def tmp_csvs(tmp_path, monkeypatch):
    clientes_csv = tmp_path / "clientes.csv"
    score_limite_csv = tmp_path / "score_limite.csv"
    solicitacoes_csv = tmp_path / "solicitacoes_aumento_limite.csv"
    erros_csv = tmp_path / "erros_sistema.csv"

    pd.DataFrame(CUSTOMERS).to_csv(clientes_csv, index=False)
    pd.DataFrame(SCORE_LIMITS).to_csv(score_limite_csv, index=False)
    pd.DataFrame(columns=list(LimitIncreaseRequest.model_fields.keys())).to_csv(solicitacoes_csv, index=False)
    pd.DataFrame(columns=list(SystemErrorLog.model_fields.keys())).to_csv(erros_csv, index=False)

    monkeypatch.setattr(clientes_repo, "CLIENTES_CSV", clientes_csv)
    monkeypatch.setattr(score_limite_repo, "SCORE_LIMITE_CSV", score_limite_csv)
    monkeypatch.setattr(solicitacoes_repo, "SOLICITACOES_CSV", solicitacoes_csv)
    monkeypatch.setattr(erros_repo, "ERROS_SISTEMA_CSV", erros_csv)

    return {
        "clientes": clientes_csv,
        "score_limite": score_limite_csv,
        "solicitacoes": solicitacoes_csv,
        "erros_sistema": erros_csv,
    }
