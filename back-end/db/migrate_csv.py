from pathlib import Path

import pandas as pd

from app.config import CLIENTES_CSV, DATA_DIR, ERROS_SISTEMA_CSV, SCORE_LIMITE_CSV, SOLICITACOES_CSV
from app.schemas.tables import Customer, LimitIncreaseRequest, ScoreLimitRange, SystemErrorLog


def ensure_schema(path: Path, model: type) -> None:
    if path.exists() and path.stat().st_size > 0:
        return

    columns = list(model.model_fields.keys())
    pd.DataFrame(columns=columns).to_csv(path, index=False)


def migrate() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_schema(CLIENTES_CSV, Customer)
    ensure_schema(SCORE_LIMITE_CSV, ScoreLimitRange)
    ensure_schema(SOLICITACOES_CSV, LimitIncreaseRequest)
    ensure_schema(ERROS_SISTEMA_CSV, SystemErrorLog)


if __name__ == "__main__":
    migrate()
