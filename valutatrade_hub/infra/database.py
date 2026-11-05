import json
from pathlib import Path
from typing import Any

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """Единая точка доступа к JSON-хранилищам приложения.

    Реализует паттерн Singleton: все части приложения
    используют один экземпляр менеджера базы данных.
    """

    _instance = None

    def __new__(cls):
        """Создаёт единственный экземпляр класса."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Инициализирует пути к хранилищам один раз."""
        if getattr(self, "_initialized", False):
            return

        self.settings = SettingsLoader()

        self.files = {
            "users": Path(self.settings.get("USERS_FILE")),
            "portfolios": Path(self.settings.get("PORTFOLIOS_FILE")),
            "rates": Path(self.settings.get("RATES_FILE")),
            "exchange_rates": Path(self.settings.get("EXCHANGE_RATES_FILE")),
        }

        self.defaults = {
            "users": [],
            "portfolios": [],
            "rates": {
                "USD": 1.0,
                "source": "local",
                "last_refresh": None,
            },
            "exchange_rates": [],
        }

        self._initialized = True

    def read(self, name: str) -> Any:
        """Читает данные из выбранного JSON-хранилища.

        Если файл отсутствует, возвращает начальные данные
        соответствующего хранилища и создаёт файл.

        Args:
            name: Название хранилища.

        Returns:
            Данные, прочитанные из JSON-файла.

        Raises:
            ValueError: Если хранилище неизвестно.
            json.JSONDecodeError: Если файл содержит некорректный JSON.
        """
        if name not in self.files:
            raise ValueError(f"Неизвестное хранилище: {name}")

        file_path = self.files[name]

        if not file_path.exists():
            data = self.defaults[name]
            self.write(name, data)
            return data.copy() if isinstance(data, (dict, list)) else data

        with file_path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)

    def write(self, name: str, data: Any) -> None:
        """Атомарно записывает данные в выбранное JSON-хранилище.

        Сначала данные записываются во временный файл,
        затем он заменяет основной файл.

        Args:
            name: Название хранилища.
            data: Данные для сохранения.

        Raises:
            ValueError: Если хранилище неизвестно.
        """
        if name not in self.files:
            raise ValueError(f"Неизвестное хранилище: {name}")

        file_path = self.files[name]
        file_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = file_path.with_suffix(file_path.suffix + ".tmp")

        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        temporary_path.replace(file_path)
