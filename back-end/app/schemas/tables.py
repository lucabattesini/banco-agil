from typing import Literal

from pydantic import BaseModel


class Customer(BaseModel):
    cpf: str
    nome: str
    data_nascimento: str
    score: int
    limite_credito: float


class ScoreLimitRange(BaseModel):
    score_min: int
    score_max: int
    limite_maximo: float


class LimitIncreaseRequest(BaseModel):
    cpf_cliente: str
    data_hora_solicitacao: str
    limite_atual: float
    novo_limite_solicitado: float
    status_pedido: Literal["pendente", "aprovado", "rejeitado"]


class SystemErrorLog(BaseModel):
    timestamp: str
    tool: str
    exception_type: str
    message: str
