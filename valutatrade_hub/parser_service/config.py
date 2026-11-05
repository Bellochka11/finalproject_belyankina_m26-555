import os
from dataclasses import dataclass, field
from pathlib import Path

from valutatrade_hub.infra.settings import SettingsLoader


@dataclass
class ParserConfig:
    """
    Хранит конфигурацию сервиса получения и обновления курсов валют.
    Содержит общие параметры HTTP-запросов, настройки внешних API,
    списки поддерживаемых фиатных и криптовалют, соответствия
    тикеров криптовалют идентификаторам CoinGecko и пути к файлам.
    Значения по умолчанию задаются непосредственно в классе,
    а переменные окружения и SettingsLoader используются
    для получения отдельных настроек.
    Attributes:
        BASE_FIAT_CURRENCY (str): Базовая фиатная валюта.
        REQUEST_TIMEOUT (int): Максимальное время ожидания HTTP-ответа
            в секундах.
        UPDATE_INTERVAL_SECONDS (int): Интервал обновления курсов
            в секундах.
        EXCHANGE_RATE_API_KEY (str | None): API-ключ ExchangeRate-API.
        EXCHANGE_RATE_API_URL (str): Базовый URL ExchangeRate-API.
        COINGECKO_API_URL (str): URL API CoinGecko.
        FIAT_CURRENCIES (set[str]): Множество поддерживаемых
            фиатных валют.
        CRYPTO_CURRENCIES (set[str]): Множество поддерживаемых
            криптовалют.
        CRYPTO_ID_MAP (dict[str, str]): Соответствие тикеров
            криптовалют их идентификаторам CoinGecko.
        PROJECT_ROOT (Path): Корневая директория проекта.
        RATES_FILE (Path): Путь к основному файлу курсов валют.
        EXCHANGE_RATES_FILE (Path): Путь к файлу курсов ExchangeRate-API.
    """

    BASE_FIAT_CURRENCY: str = "USD"
    REQUEST_TIMEOUT: int = 10
    UPDATE_INTERVAL_SECONDS: int = 300

    # Настройки ExchangeRate-API
    EXCHANGE_RATE_API_KEY: str | None = field(
        default_factory=lambda: os.getenv("EXCHANGERATE_API_KEY")
    )
    EXCHANGE_RATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Настройки CoinGecko
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3/simple/price"

    # Поддерживаемые валюты
    FIAT_CURRENCIES: set[str] = field(
        default_factory=lambda: {"USD", "EUR", "GBP", "RUB"}
    )
    CRYPTO_CURRENCIES: set[str] = field(default_factory=lambda: {"BTC", "ETH", "SOL"})
    CRYPTO_ID_MAP: dict[str, str] = field(
        default_factory=lambda: {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
        }
    )

    # Пути к файлам
    PROJECT_ROOT: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
    )
    RATES_FILE: Path = field(init=False)
    EXCHANGE_RATES_FILE: Path = field(init=False)

    def __post_init__(self):
        """
        Выполняет дополнительную инициализацию конфигурации.
        Создаёт загрузчик общих настроек приложения и получает
        из него путь к основному файлу курсов валют.
        Формирует путь к файлу курсов ExchangeRate-API
        относительно корневой директории проекта.
        """
        settings = SettingsLoader()

        self.RATES_FILE = Path(settings.get("RATES_FILE"))
        self.EXCHANGE_RATES_FILE = Path(settings.get("EXCHANGE_RATES_FILE"))


# Создание единого объекта конфигурации Parser Service.
config = ParserConfig()


# Экспорт настроек в виде отдельных констант
# для использования в остальных модулях проекта.
BASE_FIAT_CURRENCY = config.BASE_FIAT_CURRENCY
REQUEST_TIMEOUT = config.REQUEST_TIMEOUT
UPDATE_INTERVAL_SECONDS = config.UPDATE_INTERVAL_SECONDS

EXCHANGE_RATE_API_KEY = config.EXCHANGE_RATE_API_KEY
EXCHANGE_RATE_API_URL = config.EXCHANGE_RATE_API_URL
COINGECKO_API_URL = config.COINGECKO_API_URL

FIAT_CURRENCIES = config.FIAT_CURRENCIES
CRYPTO_CURRENCIES = config.CRYPTO_CURRENCIES
CRYPTO_ID_MAP = config.CRYPTO_ID_MAP

PROJECT_ROOT = config.PROJECT_ROOT
RATES_FILE = config.RATES_FILE
EXCHANGE_RATES_FILE = config.EXCHANGE_RATES_FILE


if __name__ == "__main__":  # ПОТОМ УДАЛИТЬ ЭТО
    print("API-ключ загружен:", bool(EXCHANGE_RATE_API_KEY))
