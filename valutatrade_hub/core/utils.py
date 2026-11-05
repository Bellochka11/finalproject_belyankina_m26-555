from valutatrade_hub.infra.database import DatabaseManager

database = DatabaseManager()


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
