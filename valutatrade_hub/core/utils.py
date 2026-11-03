import json
from pathlib import Path
from typing import Any


# Корневая папка проекта
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
RATES_FILE = DATA_DIR / "rates.json"



import json
from pathlib import Path
from typing import Any


# Корневая папка проекта
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
RATES_FILE = DATA_DIR / "rates.json"


def save_json(path: Path, data: Any) -> None:
    """
    Сохраняет данные в JSON-файл.

    Перед записью создаёт родительскую директорию.
    Использует временный файл, чтобы снизить риск повреждения
    данных при прерывании записи.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    temporary_path.replace(path)


def load_json(path: Path, default: Any) -> Any:
    """
    Загружает данные из JSON-файла.

    Если файл отсутствует, создаёт его с начальными данными.
    Поддерживает UTF-8 с BOM.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        save_json(path, default)
        return default

    try:
        with path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Файл {path.name} содержит некорректный JSON"
        ) from exc


def load_users() -> list[dict]:
    """Загружает список пользователей."""
    data = load_json(USERS_FILE, [])

    if not isinstance(data, list):
        raise ValueError("Файл users.json должен содержать список")

    return data


def save_users(users: list[dict]) -> None:
    """Сохраняет список пользователей."""
    save_json(USERS_FILE, users)


def load_portfolios() -> list[dict]:
    """Загружает список портфелей пользователей."""
    data = load_json(PORTFOLIOS_FILE, [])

    if not isinstance(data, list):
        raise ValueError("Файл portfolios.json должен содержать список")

    return data


def save_portfolios(portfolios: list[dict]) -> None:
    """Сохраняет список портфелей пользователей."""
    save_json(PORTFOLIOS_FILE, portfolios)


def load_rates() -> dict:
    """
    Загружает курсы валют и метаданные.

    При первом запуске создаёт файл с базовым курсом USD.
    """
    default_rates = {
        "USD": 1.0,
        "source": "local",
        "last_refresh": None,
    }

    data = load_json(RATES_FILE, default_rates)

    if not isinstance(data, dict):
        raise ValueError("Файл rates.json должен содержать словарь")

    return data


def save_rates(rates: dict) -> None:
    """Сохраняет курсы валют и метаданные."""
    if not isinstance(rates, dict):
        raise ValueError("Курсы валют должны быть представлены словарём")

    save_json(RATES_FILE, rates)
