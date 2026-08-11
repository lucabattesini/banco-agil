import pandas as pd

from app.config import SOLICITACOES_CSV
from app.schemas.tables import LimitIncreaseRequest


def create(request: LimitIncreaseRequest) -> None:
    df = pd.read_csv(SOLICITACOES_CSV, dtype={"cpf_cliente": str})
    df = pd.concat([df, pd.DataFrame([request.model_dump()])], ignore_index=True)
    df.to_csv(SOLICITACOES_CSV, index=False)
