import pandas as pd

from app.config import ERROS_SISTEMA_CSV
from app.schemas.tables import SystemErrorLog
from db.migrate_csv import ensure_schema


def create(row: SystemErrorLog) -> None:
    ensure_schema(ERROS_SISTEMA_CSV, SystemErrorLog)
    pd.DataFrame([row.model_dump()]).to_csv(ERROS_SISTEMA_CSV, mode="a", header=False, index=False)
