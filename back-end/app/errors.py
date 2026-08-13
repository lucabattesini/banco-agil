import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path

from langgraph.prebuilt.tool_node import ToolInvocationError

from app.repositories import erros_sistema_repository
from app.schemas.tables import SystemErrorLog

logger = logging.getLogger("banco_agil.tools")

_TOOLS_DIR = str(Path(__file__).resolve().parent / "tools")


class InvalidInputError(Exception):
    """Raised by a tool when it receives malformed input that a schema constraint can't express.
    The message is safe to show the customer."""


TOOL_ALTERNATIVES: dict[str, str] = {
    "get_exchange_rate": "Sugira ao cliente consultar a cotação em bcb.gov.br (Banco Central) ou Google Finance enquanto isso.",
}

TOOL_ERROR_POLICY = """## Tratamento de erros de ferramentas
- "[ERRO DE SISTEMA]": não repita a mesma tool. Peça desculpas, explique que há instabilidade (sem detalhes técnicos), repasse qualquer alternativa sugerida, e continue o atendimento normalmente.
- "[ENTRADA INVÁLIDA]": se o erro foi seu (formatação), corrija e tente de novo (só uma vez). Se foi do cliente, explique e peça a correção."""


def _extract_tool_name(e: Exception) -> str:
    for frame in reversed(traceback.extract_tb(e.__traceback__)):
        if frame.filename.startswith(_TOOLS_DIR):
            return frame.name
    return "desconhecida"


def _save_system_error(e: Exception, tool: str) -> None:
    try:
        row = SystemErrorLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool=tool,
            exception_type=type(e).__name__,
            message=str(e),
        )
        erros_sistema_repository.create(row)
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
    message = (
        "[ERRO DE SISTEMA] Uma ferramenta interna falhou. Explique ao cliente, sem detalhes técnicos, "
        "que há uma instabilidade nesta funcionalidade e peça desculpas."
    )
    alternative = TOOL_ALTERNATIVES.get(tool_name)
    if alternative:
        message += f" {alternative}"
    return message
