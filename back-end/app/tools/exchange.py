import httpx

from app.errors import InvalidInputError
from app.schemas.validators import CurrencyCodeField

AWESOMEAPI_BASE_URL = "https://economia.awesomeapi.com.br/last"


def get_exchange_rate(currency: CurrencyCodeField, compare_to: CurrencyCodeField = "BRL") -> str:
    """Look up the current exchange rate of one currency against another.

    currency is the 3-letter ISO code of the currency being priced (e.g. USD). compare_to defaults
    to BRL — only pass a different value when the customer explicitly asks to compare against
    another currency (e.g. "dollar compared to euro").
    """
    pair = f"{currency}{compare_to}"
    response = httpx.get(f"{AWESOMEAPI_BASE_URL}/{currency}-{compare_to}", timeout=10)

    if response.status_code == 404:
        raise InvalidInputError(f"Par de moedas '{currency}/{compare_to}' não encontrado ou indisponível.")
    response.raise_for_status()

    quote = response.json()[pair]
    return f"1 {currency} = {quote['bid']} {compare_to} (atualizado em {quote['create_date']})"
