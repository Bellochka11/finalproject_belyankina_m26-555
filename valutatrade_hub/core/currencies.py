from abc import ABC, abstractmethod
from math import isfinite

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """
    Абстрактный базовый класс для представления валют.
    Содержит общие атрибуты валюты и определяет интерфейс
    для получения её текстового представления.
    Attributes:
        name (str): Полное название валюты.
        code (str): Уникальный код валюты в верхнем регистре.
    """

    def __init__(self, name: str, code: str) -> None:
        """
        Инициализирует валюту и проверяет корректность её атрибутов.
        Args:
            name: Название валюты.
            code: Код валюты длиной от 2 до 5 буквенно-цифровых символов.
        Raises:
            ValueError: Если название или код валюты некорректны.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Название валюты не может быть пустым")

        if not isinstance(code, str):
            raise ValueError("Код валюты должен быть строкой")

        code = code.strip().upper()

        if not 2 <= len(code) <= 5 or not code.isalnum():
            raise ValueError("Код валюты должен содержать 2–5 символов без пробелов")

        self.name = name.strip()
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Возвращает текстовое представление валюты.
        Абстрактный метод, реализация которого определяется
        в дочерних классах.
        Returns:
            str: Строковое описание валюты.
        """
        pass


class FiatCurrency(Currency):
    """
    Представляет фиатную валюту.
    Расширяет базовый класс Currency атрибутом страны
    или валютной зоны, осуществляющей эмиссию валюты.
    Attributes:
        issuing_country (str): Страна или зона эмиссии валюты.
    """

    def __init__(
        self,
        name: str,
        code: str,
        issuing_country: str,
    ) -> None:
        """
        Инициализирует фиатную валюту.
        Args:
            name: Название валюты.
            code: Код валюты.
            issuing_country: Страна или зона эмиссии.
        Raises:
            ValueError: Если название, код или страна эмиссии
                некорректны.
        """
        super().__init__(name, code)

        if not isinstance(issuing_country, str) or not issuing_country.strip():
            raise ValueError("Страна или зона эмиссии не может быть пустой")

        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        """
        Возвращает текстовое представление фиатной валюты.
        Returns:
            str: Название, код и страна или зона эмиссии валюты.
        """
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """
    Представляет криптовалюту.
    Расширяет базовый класс Currency информацией об алгоритме
    и рыночной капитализации криптовалюты.
    Attributes:
        algorithm (str): Алгоритм, используемый криптовалютой.
        market_cap (float): Рыночная капитализация криптовалюты.
    """

    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float,
    ) -> None:
        """
        Инициализирует криптовалюту и проверяет её атрибуты.
        Args:
            name: Название криптовалюты.
            code: Код криптовалюты.
            algorithm: Алгоритм, используемый криптовалютой.
            market_cap: Рыночная капитализация.
        Raises:
            ValueError: Если название, код, алгоритм или капитализация
                имеют некорректные значения.
        """
        super().__init__(name, code)

        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ValueError("Алгоритм не может быть пустым")

        if (
            isinstance(market_cap, bool)
            or not isinstance(market_cap, (int, float))
            or not isfinite(market_cap)
            or market_cap < 0
        ):
            raise ValueError(
                "Капитализация должна быть конечным неотрицательным числом"
            )

        self.algorithm = algorithm.strip()
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        """
        Возвращает текстовое представление криптовалюты.
        Returns:
            str: Название, код, алгоритм и рыночная капитализация.
        """
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


# Реестр поддерживаемых валют
_CURRENCIES: dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
    "SOL": CryptoCurrency("Solana", "SOL", "Proof of Stake", 0.0),
}


def get_currency(code: str) -> Currency:
    """
    Возвращает объект валюты из реестра по её коду.
    Перед поиском нормализует код: удаляет пробелы по краям
    и приводит символы к верхнему регистру.
    Args:
        code: Код искомой валюты.
    Returns:
        Currency: Объект фиатной валюты или криптовалюты.
    Raises:
        ValueError: Если код валюты не указан или имеет
            некорректный тип.
        CurrencyNotFoundError: Если валюта отсутствует в реестре.
    """
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Код валюты не указан")

    normalized_code = code.strip().upper()
    try:
        return _CURRENCIES[normalized_code]
    except KeyError:
        raise CurrencyNotFoundError(normalized_code) from None
