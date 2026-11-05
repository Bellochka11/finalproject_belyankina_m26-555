import json
from pathlib import Path

from valutatrade_hub.infra.database import DatabaseManager

database = DatabaseManager()


def save_json(path: Path, data):
    """
    Сохраняет данные в JSON-файл.
    Перед сохранением создаёт родительскую директорию,
    записывает данные во временный файл и заменяет им
    основной файл для снижения риска повреждения данных
    при прерывании записи.
    Args:
        path: Путь к JSON-файлу.
        data: Данные для сохранения.
    Raises:
        OSError: Если не удалось создать директорию,
            записать временный файл или заменить основной файл.
        TypeError: Если данные не могут быть сериализованы в JSON.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    temporary_path.replace(path)


def load_json(path: Path, default):
    """
    Загружает данные из JSON-файла.
    Если файл отсутствует, создаёт его с начальными данными
    и возвращает значение default. При чтении поддерживает
    UTF-8 с BOM.
    Args:
        path: Путь к JSON-файлу.
        default: Значение, используемое при отсутствии файла.
    Returns:
        Данные, загруженные из JSON-файла, или default,
        если файл отсутствует.
    Raises:
        ValueError: Если файл содержит некорректный JSON.
        OSError: Если произошла ошибка при работе с файлом.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        save_json(path, default)
        return default
    try:
        with path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Файл {path.name} содержит некорректный JSON") from exc


def load_users():
    """
    Загружает список зарегистрированных пользователей из JSON-файла.
    Если файл отсутствует, возвращает пустой список.
    Returns:
        list: Список пользователей.
    """
    return database.read("users")


def save_users(users):
    """
    Сохраняет список пользователей в JSON-файл.
    Args:
        users: Список пользователей для сохранения.
    """
    database.write("users", users)


def load_portfolios():
    """
    Загружает список валютных портфелей из JSON-файла.
    Если файл отсутствует, возвращает пустой список.
    Returns:
        list: Список сохранённых портфелей.
    """
    return database.read("portfolios")


def save_portfolios(portfolios):
    """
    Сохраняет список валютных портфелей в JSON-файл.
    Args:
        portfolios: Список портфелей для сохранения.
    """
    database.write("portfolios", portfolios)


def load_rates():
    """
    Загружает курсы валют и метаданные из JSON-файла.
    Если файл отсутствует, создаёт его с начальными данными,
    содержащими базовый курс USD и информацию об источнике.
    Дополнительно проверяет, что загруженные данные представлены
    в виде словаря.
    Returns:
        dict: Словарь с курсами валют, источником данных
            и временем последнего обновления.
    Raises:
        ValueError: Если содержимое файла не является словарём
            или содержит некорректный JSON.
    """
    rates = database.read("rates")

    if not isinstance(rates, dict):
        raise ValueError("Некорректный формат rates.json")

    return rates


def save_rates(rates):
    """
    Сохраняет курсы валют и метаданные в JSON-файл.
    Args:
        rates: Словарь с курсами валют и дополнительной информацией.
    """
    database.write("rates", rates)
