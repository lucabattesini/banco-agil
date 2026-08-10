import logging

from langgraph.prebuilt.tool_node import ToolInvocationError

logger = logging.getLogger("banco_agil.tools")


class InvalidInputError(Exception):
    """Raised by a tool when it receives malformed input that a schema constraint can't express.
    The message is safe to show the customer."""


TOOL_ERROR_POLICY = """## Tratamento de erros de ferramentas
- Se uma tool retornar uma mensagem começando com "[ERRO DE SISTEMA]": não tente a mesma tool de novo nesta rodada. Informe o cliente, sem revelar detalhes técnicos, que há uma instabilidade nessa funcionalidade específica, peça desculpas e sugira tentar novamente mais tarde.
- Se uma tool retornar uma mensagem começando com "[ENTRADA INVÁLIDA]": se o dado incorreto foi você quem formulou (ex. formatação), corrija e tente novamente — no máximo uma vez. Se o dado veio do cliente, explique o problema a ele com clareza e peça a correção."""


def handle_tool_errors(e: Exception) -> str:
    if isinstance(e, InvalidInputError):
        logger.warning("Entrada inválida em tool: %s", e)
        return f"[ENTRADA INVÁLIDA] {e}"

    if isinstance(e, ToolInvocationError):
        logger.warning("Argumentos inválidos para tool: %s", e)
        return f"[ENTRADA INVÁLIDA] {e.message}"

    logger.error("Falha inesperada em uma tool", exc_info=True)
    return (
        "[ERRO DE SISTEMA] Uma ferramenta interna falhou. Explique ao cliente, sem detalhes técnicos, "
        "que há uma instabilidade nesta funcionalidade e peça desculpas."
    )
