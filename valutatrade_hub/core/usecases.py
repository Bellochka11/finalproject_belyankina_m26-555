from datetime import datetime, timedelta
from math import isfinite

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.core.utils import (
    load_portfolios,
    load_rates,
    load_users,
    save_portfolios,
    save_rates,
    save_users,
)
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import SettingsLoader

# Загрузчик настроек приложения.
settings = SettingsLoader()

# Время жизни кэша курсов валют в секундах.
# По умолчанию курсы считаются актуальными в течение 300 секунд.
RATE_CACHE_TTL = timedelta(seconds=settings.get("RATES_TTL_SECONDS", 300))

# Базовая валюта приложения.
# По умолчанию используется USD.
BASE_CURRENCY = settings.get("BASE_CURRENCY", "USD").upper()


def _is_cache_fresh(timestamp: str | None) -> bool:
    """
    Проверяет актуальность кеша курсов валют.
    Args:
        timestamp: Дата и время последнего обновления кеша в формате ISO 8601.
        Может быть None.
    Returns:
        True, если кеш обновлялся в течение последних 5 минут, иначе False.
    """
    if not timestamp:
        return False

    try:
        updated_at = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return False

    now = datetime.now(updated_at.tzinfo) if updated_at.tzinfo else datetime.now()

    return now - updated_at < RATE_CACHE_TTL


def _fetch_rates_from_parser() -> dict[str, float]:
    """
    Временно возвращает тестовые курсы валют относительно USD.
    В дальнейшем будет заменена запросом через Parser Service.
    """
    return {
        "USD": 1.0,
        "EUR": 1.08,
        "RUB": 0.011,
        "BTC": 59337.21,
        "ETH": 3720.00,
        "SOL": 145.50,
    }


def _get_rates() -> dict[str, float]:
    """
    Возвращает корректные курсы валют из локального хранилища.
    Исключает служебные поля, логические значения, некорректные,
    бесконечные и неположительные значения.
    Returns:
        Словарь, где ключи — коды валют, а значения — их курсы
        относительно базовой валюты USD.
    """
    data = load_rates()

    return {
        code: value
        for code, value in data.items()
        if code not in ("source", "last_refresh")
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
        and value > 0
    }


def _rate(
    from_currency: str,
    to_currency: str,
    rates: dict[str, float] | None = None,
) -> float:
    """
    Рассчитывает курс обмена между двумя валютами.
    Args:
        from_currency: Код исходной валюты.
        to_currency: Код целевой валюты.
        rates: Словарь курсов валют относительно USD.
            Если не передан, курсы загружаются из хранилища.
    Returns:
        Курс обмена одной единицы исходной валюты в целевую.
    Raises:
        ApiRequestError: Если курс одной из валют недоступен.
    """
    rates = _get_rates() if rates is None else rates

    source = from_currency.strip().upper()
    target = to_currency.strip().upper()

    if source not in rates or target not in rates:
        raise ApiRequestError(
            f"Курс {source}→{target} недоступен. Повторите попытку позже."
        )

    return rates[source] / rates[target]


def _user_from_dict(data: dict) -> User:
    """
    Создаёт объект пользователя на основе словаря.
    Args:
        data: Словарь с данными пользователя, содержащий
            идентификатор, имя, хеш пароля, соль и дату регистрации.
    Returns:
        Объект класса User с восстановленными данными пользователя.
    """
    return User(
        user_id=data["user_id"],
        username=data["username"],
        hashed_password=data["hashed_password"],
        salt=data["salt"],
        registration_date=datetime.fromisoformat(data["registration_date"]),
    )


def get_user_by_id(user_id: int) -> User:
    """
    Возвращает пользователя по его идентификатору.
    Args:
        user_id: Идентификатор пользователя.
    Returns:
        Объект пользователя.
    Raises:
        ValueError: Если пользователь не найден.
    """
    data = next(
        (item for item in load_users() if item["user_id"] == user_id),
        None,
    )

    if data is None:
        raise ValueError("Пользователь не найден")

    return _user_from_dict(data)


def _user_to_dict(user: User) -> dict:
    """
    Преобразует объект пользователя в словарь для сохранения в JSON.
    Args:
        user: Объект пользователя.
    Returns:
        Словарь с идентификатором, именем пользователя,
        датой регистрации, хешем пароля и солью.
    """
    return {
        **user.get_user_info(),
        "hashed_password": user.hashed_password,
        "salt": user.salt,
    }


def _portfolio_to_dict(portfolio: Portfolio) -> dict:
    """
    Преобразует объект портфеля в словарь для сохранения в JSON.
    Args:
        portfolio: Объект портфеля пользователя.
    Returns:
        Словарь с идентификатором пользователя и данными его кошельков.
    """
    return {
        "user_id": portfolio.user_id,
        "wallets": {
            code: wallet.get_balance_info()
            for code, wallet in portfolio.wallets.items()
        },
    }


def _portfolio_from_dict(data: dict, user: User | None = None) -> Portfolio:
    """
    Создаёт объект портфеля на основе словаря.
    Args:
        data: Словарь с идентификатором пользователя и данными кошельков.
        user: Объект пользователя, которому принадлежит портфель.
            По умолчанию None.
    Returns:
        Объект класса Portfolio с восстановленными кошельками.
    """
    wallets = {
        code: Wallet(
            currency_code=info.get("currency_code", code),
            balance=info["balance"],
        )
        for code, info in data.get("wallets", {}).items()
    }

    return Portfolio(data["user_id"], wallets, user)


def _save_portfolio(portfolio: Portfolio):
    """
    Сохраняет портфель пользователя в JSON-хранилище.
    Если портфель пользователя уже существует, обновляет его данные.
    Если портфель отсутствует, добавляет новую запись.
    Args:
        portfolio: Объект портфеля для сохранения.
    """
    portfolios = load_portfolios()
    data = _portfolio_to_dict(portfolio)

    for index, item in enumerate(portfolios):
        if item["user_id"] == portfolio.user_id:
            portfolios[index] = data
            break
    else:
        portfolios.append(data)

    save_portfolios(portfolios)


def _get_portfolio(user_id: int) -> Portfolio:
    """
    Возвращает портфель указанного пользователя.
    Загружает данные пользователя и его портфель из хранилища.
    Если портфель ещё не существует, создаёт и сохраняет новый.
    Args:
        user_id: Идентификатор пользователя.
    Returns:
        Объект портфеля пользователя.
    Raises:
        ValueError: Если пользователь не найден.
    """
    user = next(
        (_user_from_dict(item) for item in load_users() if item["user_id"] == user_id),
        None,
    )

    if user is None:
        raise ValueError("Пользователь не найден")

    data = next(
        (item for item in load_portfolios() if item["user_id"] == user_id),
        None,
    )

    if data is None:
        portfolio = Portfolio(user_id, user=user)
        _save_portfolio(portfolio)
        return portfolio

    return _portfolio_from_dict(data, user)


@log_action("REGISTER")
def register(username: str, password: str) -> User:
    """
    Регистрирует нового пользователя и создаёт его портфель.
    Проверяет корректность имени и пароля, а также отсутствие
    пользователя с таким именем в хранилище.
    Args:
        username: Имя нового пользователя.
        password: Пароль нового пользователя.
    Returns:
        Созданный объект пользователя.
    Raises:
        ValueError: Если имя пустое, пароль короче 4 символов
            или пользователь с таким именем уже существует.
    """
    if not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    users = load_users()

    if any(
        user["username"].casefold() == username.strip().casefold() for user in users
    ):
        raise ValueError(f"Такой пользователь '{username}' уже существует")

    user_id = (
        max(
            (user["user_id"] for user in users),
            default=0,
        )
        + 1
    )

    user = User.create(user_id, username, password)
    users.append(_user_to_dict(user))
    save_users(users)

    portfolios = load_portfolios()
    portfolios.append({"user_id": user_id, "wallets": {}})
    save_portfolios(portfolios)

    return user


@log_action("LOGIN")
def login(username: str, password: str) -> User:
    """
    Выполняет авторизацию пользователя.
    Находит пользователя по имени и проверяет правильность пароля.
    Args:
        username: Имя пользователя.
        password: Пароль пользователя.
    Returns:
        Объект авторизованного пользователя.
    Raises:
        ValueError: Если пользователь не найден или пароль неверный.
    """
    data = next(
        (
            item
            for item in load_users()
            if item["username"].casefold() == username.casefold()
        ),
        None,
    )

    if data is None:
        raise ValueError(f"Пользователь '{username}' не найден")

    user = _user_from_dict(data)

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    return user


def get_rate(from_currency: str, to_currency: str) -> dict:
    """
    Возвращает курс обмена между двумя валютами.
    Проверяет коды валют, загружает курсы из кеша и при необходимости
    обновляет их через Parser Service.
    Args:
        from_currency: Код исходной валюты.
        to_currency: Код целевой валюты.
    Returns:
        Словарь с исходной и целевой валютами, курсом обмена,
        временем последнего обновления и обратным курсом.
    Raises:
        ValueError: Если код валюты не указан или полученные данные
            имеют некорректный формат.
        CurrencyNotFoundError: Если указанная валюта не поддерживается.
        ApiRequestError: Если не удалось получить или обновить курсы.
    """
    if not isinstance(from_currency, str) or not from_currency.strip():
        raise ValueError("Не указан код исходной валюты")

    if not isinstance(to_currency, str) or not to_currency.strip():
        raise ValueError("Не указан код целевой валюты")

    source = from_currency.strip().upper()
    target = to_currency.strip().upper()

    get_currency(source)
    get_currency(target)

    data = load_rates()

    cached_rates = {
        code: value
        for code, value in data.items()
        if code not in ("source", "last_refresh")
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
        and value > 0
    }
    timestamp = data.get("last_refresh")

    if not _is_cache_fresh(timestamp):
        try:
            new_rates = _fetch_rates_from_parser()

            if not isinstance(new_rates, dict):
                raise ValueError("Parser вернул некорректные данные")

            validated_rates = {}
            for code, value in new_rates.items():
                if not isinstance(code, str) or not code.strip():
                    continue

                if (
                    isinstance(value, (int, float))
                    and not isinstance(value, bool)
                    and isfinite(value)
                    and value > 0
                ):
                    validated_rates[code.strip().upper()] = float(value)

            if validated_rates.get(BASE_CURRENCY) != 1.0:
                raise ValueError(
                    f"Курсы должны быть выражены относительно {BASE_CURRENCY}"
                )

            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            data = {
                **validated_rates,
                "source": "parser",
                "last_refresh": timestamp,
            }

            save_rates(data)
            cached_rates = validated_rates

        except (ApiRequestError, ValueError, OSError) as exc:
            raise ApiRequestError(f"Не удалось обновить курсы валют: {exc}") from exc

    rate = _rate(source, target, cached_rates)

    return {
        "from": source,
        "to": target,
        "rate": rate,
        "updated_at": timestamp,
        "reverse_rate": 1 / rate,
    }


def show_portfolio(user_id: int, base_currency: str = "USD") -> dict:
    """
    Возвращает информацию о портфеле пользователя.
    Рассчитывает стоимость каждого кошелька и общую стоимость
    портфеля в указанной базовой валюте.
    Args:
        user_id: Идентификатор пользователя.
        base_currency: Базовая валюта для расчёта стоимости.
            По умолчанию USD.
    Returns:
        Словарь с именем пользователя, базовой валютой,
        списком кошельков и общей стоимостью портфеля.
    """
    user = get_user_by_id(user_id)
    portfolio = _get_portfolio(user_id)
    rates = _get_rates()
    base = base_currency.strip().upper()
    get_currency(base)

    total = portfolio.get_total_value(base, rates)

    result = []

    for code, wallet in portfolio.wallets.items():
        value = wallet.balance * rates[code] / rates[base]

        result.append(
            {
                "currency": code,
                "balance": wallet.balance,
                "value": value,
            }
        )

    return {
        "username": user.username,
        "base": base,
        "wallets": result,
        "total": total,
    }


@log_action("BUY", verbose=True)
def buy(user_id: int, currency: str, amount: float) -> dict:
    """
    Покупает указанное количество валюты и обновляет портфель.
    Получает текущий курс валюты, рассчитывает стоимость покупки,
    пополняет соответствующий кошелёк и сохраняет изменения.
    Args:
        user_id: Идентификатор пользователя.
        currency: Код покупаемой валюты.
        amount: Количество покупаемой валюты.
    Returns:
        Словарь с валютой, количеством, курсом, стоимостью покупки
        и балансом кошелька до и после операции.
    Raises:
        ValueError: Если код валюты не указан.
        CurrencyNotFoundError: Если валюта не поддерживается.
        ApiRequestError: Если курс валюты недоступен.
    """
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("Не указан код валюты")

    code = currency.strip().upper()
    get_currency(code)
    Wallet._validate_amount(amount)

    rate_info = get_rate(code, BASE_CURRENCY)
    rate = rate_info["rate"]
    cost = amount * rate

    portfolio = _get_portfolio(user_id)
    wallet = portfolio.get_wallet(code)

    if wallet is None:
        wallet = portfolio.add_currency(code)

    old_balance = wallet.balance
    wallet.deposit(amount)

    _save_portfolio(portfolio)

    return {
        "currency": code,
        "amount": amount,
        "rate": rate,
        "cost": cost,
        "old_balance": old_balance,
        "balance": wallet.balance,
    }


@log_action("SELL", verbose=True)
def sell(user_id: int, currency: str, amount: float) -> dict:
    """
    Продаёт указанное количество валюты и обновляет портфель.
    Получает текущий курс валюты, рассчитывает выручку,
    списывает валюту с кошелька и сохраняет изменения.
    Args:
        user_id: Идентификатор пользователя.
        currency: Код продаваемой валюты.
        amount: Количество продаваемой валюты.
    Returns:
        Словарь с валютой, количеством, курсом, выручкой
        и балансом кошелька до и после операции.
    Raises:
        ValueError: Если код валюты не указан, кошелёк отсутствует
            или на нём недостаточно средств.
        CurrencyNotFoundError: Если валюта не поддерживается.
        ApiRequestError: Если курс валюты недоступен.
    """
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("Не указан код валюты")

    code = currency.strip().upper()
    get_currency(code)
    Wallet._validate_amount(amount)

    rate_info = get_rate(code, BASE_CURRENCY)
    rate = rate_info["rate"]
    revenue = amount * rate

    portfolio = _get_portfolio(user_id)
    wallet = portfolio.get_wallet(code)

    if wallet is None:
        raise ValueError(
            f"У вас нет кошелька '{code}'. "
            "Добавьте валюту: она создаётся автоматически "
            "при первой покупке."
        )

    old_balance = wallet.balance
    wallet.withdraw(amount)
    balance_after = wallet.balance

    _save_portfolio(portfolio)

    return {
        "currency": code,
        "amount": amount,
        "rate": rate,
        "revenue": revenue,
        "old_balance": old_balance,
        "balance": balance_after,
    }


def change_password(user_id: int, new_password: str):
    """
    Изменяет пароль пользователя.
    Args:
        new_password: Новый пароль пользователя.
    Raises:
        ValueError: Если пароль короче 4 символов.
    """
    user = get_user_by_id(user_id)
    user.change_password(new_password)

    users = load_users()

    for index, item in enumerate(users):
        if item["user_id"] == user.user_id:
            users[index] = _user_to_dict(user)
            save_users(users)
            return
