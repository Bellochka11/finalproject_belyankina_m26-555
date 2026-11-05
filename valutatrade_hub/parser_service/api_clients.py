from abc import ABC, abstractmethod
from math import isfinite
from typing import Any

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import (
    BASE_FIAT_CURRENCY,
    COINGECKO_API_URL,
    CRYPTO_ID_MAP,
    EXCHANGE_RATE_API_KEY,
    EXCHANGE_RATE_API_URL,
    FIAT_CURRENCIES,
    REQUEST_TIMEOUT,
)


def _get_response(
    url: str,
    service_name: str,
    params: dict | None = None,
) -> requests.Response:
    """Выполняет HTTP-запрос и обрабатывает типовые ошибки API."""

    try:
        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.Timeout as exc:
        raise ApiRequestError(
            f"{service_name}: превышено время ожидания ответа ({REQUEST_TIMEOUT} сек.)"
        ) from exc
    except requests.ConnectionError as exc:
        raise ApiRequestError(
            f"{service_name}: не удалось установить соединение"
        ) from exc
    except requests.RequestException as exc:
        raise ApiRequestError(f"{service_name}: ошибка HTTP-запроса") from exc

    status = response.status_code

    if status == 401:
        message = "ошибка авторизации: проверьте API-ключ"
    elif status == 403:
        message = "доступ к API запрещён"
    elif status == 404:
        message = "запрашиваемый ресурс не найден"
    elif status == 429:
        message = "превышен лимит запросов, попробуйте позже"
    elif 500 <= status <= 599:
        message = "внутренняя ошибка сервера API"
    elif status != 200:
        message = "неожиданный HTTP-статус"
    else:
        return response

    raise ApiRequestError(f"{service_name}: {message} (HTTP {status})")


class BaseApiClient(ABC):
    """
    Абстрактный базовый класс для клиентов внешних API.
    Определяет общий интерфейс получения курсов валют.
    Конкретные клиенты должны реализовать метод fetch_rates().
    """

    @abstractmethod
    def fetch_rates(self) -> dict[str, float]:
        """
        Получает курсы валют из внешнего API.
        Абстрактный метод, реализация которого определяется
        в дочерних классах.
        Returns:
            dict[str, float]: Словарь с валютными парами
                и соответствующими курсами.
        Raises:
            ApiRequestError: При ошибке получения или обработки данных.
        """
        pass


class ExchangeRateApiClient(BaseApiClient):
    """
    Клиент ExchangeRate-API для получения курсов фиатных валют.
    Выполняет HTTP-запрос к ExchangeRate-API, проверяет ответ,
    фильтрует неподдерживаемые и некорректные значения курсов,
    а также рассчитывает обратные курсы валют.
    """

    def fetch_rates(self) -> dict[str, float]:
        """
        Получает курсы фиатных валют через ExchangeRate-API.
        Использует API-ключ и базовую валюту из конфигурации.
        Проверяет HTTP-статус, корректность JSON-ответа,
        статус запроса и соответствие базовой валюты.
        Возвращает прямые и обратные курсы только
        для поддерживаемых фиатных валют.
        Returns:
            dict[str, float]: Словарь валютных пар и курсов,
                например USD_EUR и EUR_USD.
        Raises:
            ApiRequestError: Если API-ключ не задан, запрос завершился
                ошибкой, ответ имеет некорректный формат или не содержит
                корректных курсов валют.
        """
        if not EXCHANGE_RATE_API_KEY:
            raise ApiRequestError("Не задан ключ EXCHANGE_RATE_API_KEY")

        url = (
            f"{EXCHANGE_RATE_API_URL}/"
            f"{EXCHANGE_RATE_API_KEY}/latest/"
            f"{BASE_FIAT_CURRENCY}"
        )
        response = _get_response(url, "ExchangeRate-API")
        try:
            data: dict[str, Any] = response.json()
            if not isinstance(data, dict):
                raise ApiRequestError(
                    "ExchangeRate-API вернул данные неверного формата"
                )
        except ValueError as exc:
            raise ApiRequestError("ExchangeRate-API вернул некорректный JSON") from exc

        if data.get("result") != "success":
            raise ApiRequestError(
                f"ExchangeRate-API: {data.get('error-type', 'неизвестная ошибка')}"
            )

        base_currency = data.get("base_code")
        conversion_rates = data.get("conversion_rates")

        if base_currency != BASE_FIAT_CURRENCY:
            raise ApiRequestError(f"Ожидалась базовая валюта {BASE_FIAT_CURRENCY}")

        if not isinstance(conversion_rates, dict):
            raise ApiRequestError("В ответе отсутствует conversion_rates")

        rates: dict[str, float] = {}

        for currency, value in conversion_rates.items():
            if not isinstance(currency, str):
                continue
            if currency not in FIAT_CURRENCIES or currency == BASE_FIAT_CURRENCY:
                continue
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or value <= 0
            ):
                continue

            rate = float(value)

            rates[f"{base_currency}_{currency}"] = rate
            rates[f"{currency}_{base_currency}"] = 1 / rate

        if not rates:
            raise ApiRequestError("ExchangeRate-API не вернул корректных курсов")
        return rates


class CoinGeckoClient(BaseApiClient):
    """
    Клиент CoinGecko для получения курсов криптовалют.
    Выполняет HTTP-запрос к CoinGecko, получает стоимость
    поддерживаемых криптовалют относительно базовой фиатной
    валюты и рассчитывает обратные курсы.
    """

    def fetch_rates(self) -> dict[str, float]:
        """
        Получает курсы криптовалют через CoinGecko.
        Формирует параметры HTTP-запроса на основе реестра
        поддерживаемых криптовалют, проверяет ответ API
        и фильтрует отсутствующие или некорректные значения.
        Для каждой полученной валюты рассчитывает прямой
        и обратный курсы относительно базовой фиатной валюты.
        Returns:
            dict[str, float]: Словарь валютных пар и курсов,
                например BTC_USD и USD_BTC.
        Raises:
            ApiRequestError: Если запрос завершился ошибкой,
                ответ имеет некорректный формат или API
                не вернул корректных курсов.
        """
        params = {
            "ids": ",".join(CRYPTO_ID_MAP.values()),
            "vs_currencies": BASE_FIAT_CURRENCY.lower(),
        }
        response = _get_response(
            COINGECKO_API_URL,
            "CoinGecko",
            params=params,
        )
        try:
            data: dict[str, Any] = response.json()
            if not isinstance(data, dict):
                raise ApiRequestError("CoinGecko вернул данные неверного формата")
        except ValueError as exc:
            raise ApiRequestError("CoinGecko вернул некорректный JSON") from exc

        rates: dict[str, float] = {}

        for ticker, coin_id in CRYPTO_ID_MAP.items():
            coin_data = data.get(coin_id)

            if not isinstance(coin_data, dict):
                continue

            value = coin_data.get(BASE_FIAT_CURRENCY.lower())

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or value <= 0
            ):
                continue

            rate = float(value)

            rates[f"{ticker}_{BASE_FIAT_CURRENCY}"] = rate
            rates[f"{BASE_FIAT_CURRENCY}_{ticker}"] = 1 / rate

        if not rates:
            raise ApiRequestError("CoinGecko не вернул корректных курсов")

        return rates
