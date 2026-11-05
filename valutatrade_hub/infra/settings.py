import tomllib
from pathlib import Path
from typing import Any

# Корневая директория проекта.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Настройки приложения по умолчанию.
# Используются, если соответствующие параметры отсутствуют в pyproject.toml.
DEFAULT_SETTINGS = {
    "DATA_DIR": PROJECT_ROOT / "data",
    "USERS_FILE": PROJECT_ROOT / "data" / "users.json",
    "PORTFOLIOS_FILE": PROJECT_ROOT / "data" / "portfolios.json",
    "RATES_FILE": PROJECT_ROOT / "data" / "rates.json",
    "EXCHANGE_RATES_FILE": PROJECT_ROOT / "data" / "exchange_rates.json",
    "RATES_TTL_SECONDS": 300,
    "BASE_CURRENCY": "USD",
    "LOG_FILE": PROJECT_ROOT / "logs" / "valutatrade.log",
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": ("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
}


class SettingsLoader:
    """
    Единый загрузчик конфигурации приложения.
    Реализует паттерн Singleton: при повторном создании
    возвращается один и тот же экземпляр класса.
    Загружает настройки по умолчанию и переопределяет их
    значениями из секции [tool.valutatrade] файла pyproject.toml.
    Attributes:
        _settings (dict): Словарь текущих настроек приложения.
    """

    _instance = None

    def __new__(cls):
        """
        Создаёт единственный экземпляр загрузчика настроек.
        При первом создании инициализирует словарь настроек
        значениями по умолчанию и загружает конфигурацию
        из pyproject.toml.
        При последующих вызовах возвращает уже существующий экземпляр.
        Returns:
            SettingsLoader: Единственный экземпляр класса.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = DEFAULT_SETTINGS.copy()
            cls._instance.reload()

        return cls._instance

    def reload(self) -> None:
        """
        Перезагружает конфигурацию приложения из pyproject.toml.
        Сначала восстанавливает настройки по умолчанию,
        затем считывает параметры из секции [tool.valutatrade]
        и переопределяет соответствующие значения.
        Пути к файлам и директориям преобразуются в объекты Path.
        Если pyproject.toml отсутствует, используются
        настройки по умолчанию.
        Raises:
            OSError: Если возникла ошибка при открытии или чтении файла.
            tomllib.TOMLDecodeError: Если файл содержит некорректный TOML.
        """
        self._settings = DEFAULT_SETTINGS.copy()

        config_path = PROJECT_ROOT / "pyproject.toml"

        if not config_path.exists():
            return

        with config_path.open("rb") as file:
            config = tomllib.load(file)

        project_settings = config.get("tool", {}).get("valutatrade", {})

        for key, value in project_settings.items():
            if key in self._settings:
                self._settings[key] = value

        for key in (
            "DATA_DIR",
            "USERS_FILE",
            "PORTFOLIOS_FILE",
            "RATES_FILE",
            "EXCHANGE_RATES_FILE",
            "LOG_FILE",
        ):
            self._settings[key] = Path(self._settings[key])

    def get(self, key: str, default: Any = None) -> Any:
        """
        Возвращает значение настройки по её ключу.
        Args:
            key: Название параметра конфигурации.
            default: Значение, возвращаемое при отсутствии ключа.
                По умолчанию None.
        Returns:
            Any: Значение настройки или default,
                если указанный ключ не найден.
        """
        return self._settings.get(key, default)
