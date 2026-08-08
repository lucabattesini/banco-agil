from pathlib import Path

import pandas as pd

from app.config import CLIENTES_CSV, DATA_DIR, SCORE_LIMITE_CSV, SOLICITACOES_CSV
from app.schemas.tables import Customer, LimitIncreaseRequest, ScoreLimitRange


def _ensure_schema(path: Path, model: type) -> None:
    if path.exists() and path.stat().st_size > 0:
        return

    columns = list(model.model_fields.keys())
    pd.DataFrame(columns=columns).to_csv(path, index=False)


def migrate() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_schema(CLIENTES_CSV, Customer)
    _ensure_schema(SCORE_LIMITE_CSV, ScoreLimitRange)
    _ensure_schema(SOLICITACOES_CSV, LimitIncreaseRequest)


if __name__ == "__main__":
    migrate()
