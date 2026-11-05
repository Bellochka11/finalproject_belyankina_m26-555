import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging() -> None:
    """
    Настраивает систему логирования приложения.

    Загружает параметры логирования из SettingsLoader,
    создаёт директорию для файла логов и настраивает
    RotatingFileHandler для записи сообщений всех модулей.

    При достижении размера файла 5 МБ создаётся резервная
    копия. Хранится не более пяти резервных файлов.
    """
    settings = SettingsLoader()

    log_file = Path(settings.get("LOG_FILE"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(
        getattr(
            logging,
            str(settings.get("LOG_LEVEL", "INFO")).upper(),
            logging.INFO,
        )
    )

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
