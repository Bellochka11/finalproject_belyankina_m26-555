import json
from datetime import UTC, datetime
from pathlib import Path

from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.parser_service.config import (
    BASE_FIAT_CURRENCY,
    CRYPTO_CURRENCIES,
    EXCHANGE_RATES_FILE,
    FIAT_CURRENCIES,
    RATES_FILE,
)


class RatesStorage:
    """
    Хранилище актуальных курсов валют и истории их изменений.
    Обеспечивает загрузку и сохранение текущих курсов,
    а также добавление новых записей в историю изменений.
    Для работы со стандартными JSON-хранилищами использует
    DatabaseManager, а для переданных путей обеспечивает
    самостоятельную загрузку и атомарное сохранение JSON.
    Attributes:
        rates_file (Path): Путь к файлу с актуальными курсами валют.
        history_file (Path): Путь к файлу истории изменения курсов.
    """

    def __init__(
        self,
        rates_file: Path = RATES_FILE,
        history_file: Path = EXCHANGE_RATES_FILE,
    ) -> None:
        """
        Инициализирует хранилище курсов валют.
        Args:
            rates_file: Путь к файлу с актуальными курсами.
                По умолчанию используется RATES_FILE.
            history_file: Путь к файлу истории курсов.
                По умолчанию используется EXCHANGE_RATES_FILE.
        """
        self.rates_file = Path(rates_file)
        self.history_file = Path(history_file)
        self.database = DatabaseManager()

    @staticmethod
    def _get_timestamp() -> str:
        """
        Возвращает текущую дату и время в формате ISO 8601 (UTC).
        Returns:
            str: Временная метка с точностью до секунд и указанием
                часового пояса UTC.
        """
        return datetime.now(UTC).isoformat(timespec="seconds")

    def _load_storage(self, name: str, path: Path, default):
        """Загружает данные через DatabaseManager или по переданному пути."""
        if path == self.database.files[name]:
            return self.database.read(name)

        if not path.exists():
            return default

        with path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)

    def _save_storage(self, name: str, path: Path, data) -> None:
        """Сохраняет данные через DatabaseManager или по переданному пути."""
        if path == self.database.files[name]:
            self.database.write(name, data)
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(path.suffix + ".tmp")

        try:
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

            temporary_path.replace(path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def load_current_rates(self) -> dict:
        """
        Загружает актуальные курсы валют из JSON-файла.
        Если файл отсутствует, возвращает значения по умолчанию:
        базовая валюта, источник данных и время последнего обновления.
        Returns:
            dict: Словарь с актуальными курсами и метаданными.
        Raises:
            ValueError: Если содержимое файла не является словарём.
            OSError: При ошибке чтения файла.
        """
        data = self._load_storage(
            "rates",
            self.rates_file,
            {
                BASE_FIAT_CURRENCY: 1.0,
                "source": "local",
                "last_refresh": None,
            },
        )

        if not isinstance(data, dict):
            raise ValueError("Некорректный формат rates.json")

        return data

    def save_current_rates(
        self,
        pair_rates: dict[str, float],
        source: str = "parser_service",
    ) -> None:
        """
        Сохраняет актуальные курсы валют в JSON-файл.
        Принимает курсы в формате валютных пар, проверяет их
        корректность и сохраняет только курсы относительно
        базовой фиатной валюты.
        Перед сохранением загружает предыдущие значения,
        чтобы сохранить курсы валют, отсутствующие в новом ответе API.
        Обновляет источник данных и время последнего обновления.
        Args:
            pair_rates: Словарь валютных пар и соответствующих курсов.
                Например: {"EUR_USD": 1.08, "BTC_USD": 59337.21}.
            source: Источник полученных курсов.
                По умолчанию "parser_service".
        Returns:
            None
        """
        allowed_currencies = FIAT_CURRENCIES | CRYPTO_CURRENCIES

        current_rates = self.load_current_rates()
        current_rates[BASE_FIAT_CURRENCY] = 1.0

        for pair, rate in pair_rates.items():
            currencies = pair.split("_")

            if len(currencies) != 2:
                continue

            from_currency, to_currency = currencies

            if (
                to_currency != BASE_FIAT_CURRENCY
                or from_currency not in allowed_currencies
                or isinstance(rate, bool)
                or not isinstance(rate, (int, float))
                or rate <= 0
            ):
                continue

            current_rates[from_currency] = float(rate)

        current_rates["source"] = source
        current_rates["last_refresh"] = self._get_timestamp()

        self._save_storage("rates", self.rates_file, current_rates)

    def append_history(
        self,
        pair_rates: dict[str, float],
        source: str,
    ) -> None:
        """
        Добавляет новые курсы валют в историю изменений.
        Загружает существующие записи из JSON-файла,
        проверяет корректность валютных пар и значений курсов,
        после чего добавляет новые записи с временной меткой,
        источником данных и дополнительными метаданными.
        Существующие записи истории сохраняются.
        Args:
            pair_rates: Словарь валютных пар и соответствующих курсов.
                Например: {"EUR_USD": 1.08, "USD_EUR": 0.93}.
            source: Источник полученных курсов.
        Raises:
            ValueError: Если содержимое файла истории не является списком.
            OSError: При ошибке чтения или записи файла.
        Returns:
            None
        """
        history = self._load_storage("exchange_rates", self.history_file, [])

        if not isinstance(history, list):
            raise ValueError("Некорректный формат exchange_rates.json")

        timestamp = self._get_timestamp()

        for pair, rate in pair_rates.items():
            currencies = pair.split("_")

            if len(currencies) != 2:
                continue

            from_currency, to_currency = currencies

            if (
                isinstance(rate, bool)
                or not isinstance(rate, (int, float))
                or rate <= 0
            ):
                continue

            history.append(
                {
                    "id": f"{from_currency}_{to_currency}_{timestamp}",
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "rate": float(rate),
                    "timestamp": timestamp,
                    "source": source,
                    "meta": {},
                }
            )

        self._save_storage("exchange_rates", self.history_file, history)
