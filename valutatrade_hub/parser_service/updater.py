import logging

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.storage import RatesStorage

logger = logging.getLogger(__name__)


class RatesUpdater:
    """
    Сервис обновления курсов валют из внешних API.
    Получает курсы фиатных валют через ExchangeRate-API,
    а курсы криптовалют через CoinGecko.
    Объединяет полученные данные, сохраняет актуальные курсы
    и добавляет новые записи в историю изменений.
    Поддерживает обновление из одного или нескольких источников,
    а также частичное обновление при недоступности одного из API.
    Attributes:
        exchange_client (ExchangeRateApiClient | None):
            Клиент для получения курсов фиатных валют.
        coingecko_client (CoinGeckoClient | None):
            Клиент для получения курсов криптовалют.
        clients (list): Список клиентов внешних API с их именами.
        storage (RatesStorage): Объект для хранения актуальных
            курсов и истории изменений.
        errors (list[str]): Список ошибок, возникших при получении
            курсов из внешних API во время последнего обновления.
    """

    def __init__(self, clients=None, storage=None):
        """
        Инициализирует сервис обновления курсов валют.
        Если список клиентов не передан, создаёт стандартные
        клиенты ExchangeRate-API и CoinGecko.
        Если объект хранилища не передан, создаёт RatesStorage.
        Args:
            clients (list | None): Список пар, содержащих имя
                источника и соответствующий API-клиент.
                Если None, используются стандартные клиенты.
            storage (RatesStorage | None): Объект для сохранения
                курсов и истории. Если None, создаётся RatesStorage.
        """
        if clients is None:
            self.exchange_client = ExchangeRateApiClient()
            self.coingecko_client = CoinGeckoClient()

            self.clients = [
                ("exchangerate", self.exchange_client),
                ("coingecko", self.coingecko_client),
            ]
        else:
            self.clients = clients
            clients_by_name = dict(clients)

            self.exchange_client = clients_by_name.get("exchangerate")
            self.coingecko_client = clients_by_name.get("coingecko")

        self.storage = storage if storage is not None else RatesStorage()
        self.errors = []

    def run_update(self, source: str = "all") -> dict[str, float]:
        """
        Получает курсы валют из выбранных внешних API и сохраняет их.
        В зависимости от параметра source запускает обновление
        из одного или обоих источников. Полученные курсы объединяются,
        после чего сохраняются в хранилище и добавляются в историю.
        Если один из источников недоступен, сервис продолжает работу
        с данными другого источника. Ошибки отдельных API сохраняются
        в атрибуте errors.
        Args:
            source (str): Источник обновления:
                "all" — оба API;
                "exchangerate" — только ExchangeRate-API;
                "coingecko" — только CoinGecko.
                По умолчанию "all".
        Returns:
            dict[str, float]: Словарь полученных валютных пар
                и соответствующих курсов.
        Raises:
            ValueError: Если указан неподдерживаемый источник.
            ApiRequestError: Если не удалось получить курсы
                ни из одного выбранного источника.
        """
        logger.info("Запуск обновления курсов")

        if source not in {"all", "exchangerate", "coingecko"}:
            raise ValueError("Источник должен быть all, exchangerate или coingecko")

        updated_rates = {}
        successful_sources = []
        errors = []

        selected_clients = [
            (name, client)
            for name, client in self.clients
            if source == "all" or name == source
        ]

        for source_name, client in selected_clients:
            try:
                rates = client.fetch_rates()
                updated_rates.update(rates)
                successful_sources.append(source_name)

                logger.info(
                    "%s: получено курсов — %s",
                    source_name,
                    len(rates),
                )

            except ApiRequestError as exc:
                errors.append(str(exc))
                logger.error(
                    "%s: ошибка получения курсов — %s",
                    source_name,
                    exc,
                )
        self.errors = errors
        if not updated_rates:
            raise ApiRequestError(
                "Не удалось получить курсы ни из одного источника. " + "; ".join(errors)
            )

        logger.info("Сохранение актуальных курсов")

        self.storage.save_current_rates(
            updated_rates,
            source="+".join(successful_sources),
        )

        logger.info("Сохранение истории курсов")

        self.storage.append_history(
            updated_rates,
            source="+".join(successful_sources),
        )

        logger.info(
            "Обновление завершено. Всего получено курсов: %s",
            len(updated_rates),
        )

        return updated_rates
