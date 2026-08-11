import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from langgraph.prebuilt.tool_node import ToolInvocationError

from app.config import ERROS_SISTEMA_CSV
from app.schemas.tables import SystemErrorLog
from db.migrate_csv import ensure_schema

logger = logging.getLogger("banco_agil.tools")

_TOOLS_DIR = str(Path(__file__).resolve().parent / "tools")


class InvalidInputError(Exception):
    """Raised by a tool when it receives malformed input that a schema constraint can't express.
    The message is safe to show the customer."""


TOOL_ERROR_POLICY = """## Tratamento de erros de ferramentas
- Se uma tool retornar uma mensagem começando com "[ERRO DE SISTEMA]": não tente a mesma tool de novo nesta rodada. Informe o cliente, sem revelar detalhes técnicos, que há uma instabilidade nessa funcionalidade específica, peça desculpas e sugira tentar novamente mais tarde.
- Se uma tool retornar uma mensagem começando com "[ENTRADA INVÁLIDA]": se o dado incorreto foi você quem formulou (ex. formatação), corrija e tente novamente — no máximo uma vez. Se o dado veio do cliente, explique o problema a ele com clareza e peça a correção."""


def _extract_tool_name(e: Exception) -> str:
    for frame in reversed(traceback.extract_tb(e.__traceback__)):
        if frame.filename.startswith(_TOOLS_DIR):
            return frame.name
    return "desconhecida"


def _save_system_error(e: Exception, tool: str) -> None:
    try:
        ensure_schema(ERROS_SISTEMA_CSV, SystemErrorLog)
        row = SystemErrorLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool=tool,
            exception_type=type(e).__name__,
            message=str(e),
        )
        pd.DataFrame([row.model_dump()]).to_csv(ERROS_SISTEMA_CSV, mode="a", header=False, index=False)
    except Exception:
        logger.error("Falha ao gravar histórico de erros de sistema", exc_info=True)


def handle_tool_errors(e: Exception) -> str:
    if isinstance(e, InvalidInputError):
        logger.warning("Entrada inválida em tool: %s", e)
        return f"[ENTRADA INVÁLIDA] {e}"

    if isinstance(e, ToolInvocationError):
        logger.warning("Argumentos inválidos para tool: %s", e)
        return f"[ENTRADA INVÁLIDA] {e.message}"

    tool_name = _extract_tool_name(e)
    logger.error("Falha inesperada na tool '%s'", tool_name, exc_info=True)
    _save_system_error(e, tool_name)
    return (
        "[ERRO DE SISTEMA] Uma ferramenta interna falhou. Explique ao cliente, sem detalhes técnicos, "
        "que há uma instabilidade nesta funcionalidade e peça desculpas."
    )
