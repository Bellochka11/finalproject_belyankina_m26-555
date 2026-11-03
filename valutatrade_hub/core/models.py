import hashlib
import hmac
import secrets


from datetime import datetime

class User:
    """
    Представляет пользователя приложения.
    Хранит идентификатор, имя пользователя, хеш пароля, соль
    и дату регистрации. Поддерживает создание пользователя,
    проверку и изменение пароля.
    Attributes:
        _user_id (int): Уникальный идентификатор пользователя.
        _username (str): Имя пользователя.
        _hashed_password (str): Хеш пароля.
        _salt (str): Соль, используемая при хешировании пароля.
        _registration_date (datetime): Дата и время регистрации.
    """
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ):
        """
        Инициализирует объект пользователя.
        Args:
            user_id: Уникальный идентификатор пользователя.
            username: Имя пользователя.
            hashed_password: Хеш пароля.
            salt: Соль для хеширования пароля.
            registration_date: Дата и время регистрации.
        """
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self):
        """Возвращает уникальный идентификатор пользователя."""
        return self._user_id

    @property
    def username(self):
        """Возвращает имя пользователя."""
        return self._username 

    @username.setter
    def username(self, value):
        """
        Устанавливает новое имя пользователя.
        Args:
            value: Новое имя пользователя.
        Raises:
            ValueError: Если имя пользователя пустое.
        """
        if not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def hashed_password(self):
        """Возвращает хеш пароля пользователя."""
        return self._hashed_password

    @property
    def salt(self):
        """Возвращает соль, используемую для хеширования пароля."""
        return self._salt

    @property
    def registration_date(self):
        """Возвращает дату и время регистрации пользователя."""
        return self._registration_date

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """
        Вычисляет SHA-256 хеш пароля с использованием соли.
        Args:
            password: Пароль пользователя.
            salt: Уникальная соль для хеширования.
        Returns:
            str: Шестнадцатеричное представление хеша пароля.
        """
        return hashlib.sha256(
            (password + salt).encode("utf-8")
        ).hexdigest()

    @classmethod
    def create(cls, user_id: int, username: str, password: str):
        """
        Создаёт нового пользователя с автоматически сгенерированной солью.
        Хеширует пароль и устанавливает текущую дату регистрации.
        Args:
            user_id: Уникальный идентификатор пользователя.
            username: Имя пользователя.
            password: Пароль в открытом виде.
        Returns:
            User: Созданный объект пользователя.
        """
        salt = secrets.token_hex(16)
        hashed_password = cls.hash_password(password, salt)

        return cls(
            user_id=user_id,
            username=username.strip(),
            hashed_password=hashed_password,
            salt=salt,
            registration_date=datetime.now(),
        )

    def verify_password(self, password: str) -> bool:
        """
        Проверяет соответствие введённого пароля сохранённому хешу.
        Args:
            password: Пароль для проверки.
        Returns:
            bool: True, если пароль совпадает, иначе False.
        """
        candidate = self.hash_password(password, self._salt)
        return hmac.compare_digest(candidate, self._hashed_password)

    def change_password(self, new_password: str):
        """
        Изменяет пароль пользователя и генерирует новую соль.
        Args:
            new_password: Новый пароль пользователя.
        Raises:
            ValueError: Если длина нового пароля меньше 4 символов.
        """
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        self._salt = secrets.token_hex(16)
        self._hashed_password = self.hash_password(
            new_password, self._salt
        )

    def get_user_info(self) -> dict:
        """
        Возвращает основную информацию о пользователе.
        Пароль и соль не включаются в возвращаемые данные.
        Returns:
            dict: Словарь с идентификатором, именем пользователя
                и датой регистрации в формате ISO 8601.
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }


class Wallet:
    """
    Представляет кошелёк пользователя для хранения определённой валюты.
    Позволяет пополнять баланс, списывать средства и получать
    информацию о состоянии кошелька.
    Attributes:
        _currency_code (str): Код валюты кошелька.
        _balance (float): Текущий баланс кошелька.
    """
    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Инициализирует кошелёк с указанной валютой и начальным балансом.
        Args:
            currency_code: Код валюты кошелька.
            balance: Начальный баланс. По умолчанию равен 0.0.
        """
        self._currency_code = currency_code.strip().upper()
        self.balance = balance

    @property
    def currency_code(self):
        """Возвращает код валюты кошелька."""
        return self._currency_code

    @property
    def balance(self):
        """Возвращает текущий баланс кошелька."""
        return self._balance

    @balance.setter
    def balance(self, value):
        """
        Устанавливает новый баланс кошелька.
        Args:
            value: Новое значение баланса.
        Raises:
            ValueError: Если баланс не является числом
                или имеет отрицательное значение.
        """
        if not isinstance(value, (int, float)):
            raise ValueError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")

        self._balance = float(value)

    @staticmethod
    def _validate_amount(amount):
        """
        Проверяет корректность суммы финансовой операции.
        Args:
            amount: Сумма пополнения или списания.
        Raises:
            ValueError: Если сумма не является положительным числом.
        """
        if (not isinstance(amount, (int, float))
            or amount <= 0
        ):
            raise ValueError("'amount' должен быть положительным числом")

    def deposit(self, amount: float):
        """
        Пополняет баланс кошелька на указанную сумму.
        Args:
            amount: Сумма пополнения.
        Raises:
            ValueError: Если сумма некорректна.
        """
        self._validate_amount(amount)
        self.balance = self._balance + amount

    def withdraw(self, amount: float):
        """
        Списывает указанную сумму с баланса кошелька.
        Args:
            amount: Сумма списания.
        Raises:
            ValueError: Если сумма некорректна.
            InsufficientFundsError: Если доступного баланса
                недостаточно для списания.
        """
        self._validate_amount(amount)

        if amount > self.balance:
            raise ValueError(
                f"Недостаточно средств: доступно {self.balance} "
                f"{self.currency_code}, требуется {amount} {self.currency_code}"
            )
        
        self.balance = self._balance - amount

    def get_balance_info(self) -> dict:
        """
        Возвращает информацию о состоянии кошелька.
        Returns:
            dict: Словарь с кодом валюты и текущим балансом.
        """
        return {
            "currency_code": self._currency_code,
            "balance": self._balance,
        }


# Статический словарь курсов валют относительно USD.
# Используется как значение по умолчанию при расчёте стоимости портфеля.
EXCHANGE_RATES = {
    "USD": 1.0,
    "BTC": 59337.21,
    "EUR": 1.08,
    "RUB": 0.011,
}

class Portfolio:
    """
    Представляет валютный портфель пользователя.
    Содержит набор кошельков с различными валютами и позволяет
    управлять ими, получать информацию о балансах и рассчитывать
    общую стоимость портфеля в выбранной базовой валюте.
    Attributes:
        _user_id (int): Идентификатор владельца портфеля.
        _user (User | None): Объект владельца портфеля.
        _wallets (dict[str, Wallet]): Словарь валютных кошельков,
            где ключом является код валюты.
    """
    def __init__(
        self,
        user_id: int,
        wallets: dict[str, Wallet] | None = None,
        user: User | None = None,
    ):
        """
        Инициализирует портфель пользователя.
        Args:
            user_id: Идентификатор владельца портфеля.
            wallets: Существующие кошельки пользователя.
                По умолчанию создаётся пустой портфель.
            user: Объект пользователя. По умолчанию None.
        """
        self._user_id = user_id
        self._user = user
        self._wallets = {}

        for code, wallet in (wallets or {}).items():
            self._wallets[code.upper()] = wallet

    @property
    def user(self):
        """Возвращает объект владельца портфеля."""
        return self._user

    @property
    def user_id(self):
        """Возвращает идентификатор владельца портфеля."""
        return self._user_id

    @property
    def wallets(self):
        """
        Возвращает копию словаря валютных кошельков.
        Returns:
            dict[str, Wallet]: Словарь кошельков с кодами валют
                в качестве ключей.
        """
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """
        Добавляет новый валютный кошелёк в портфель.
        Если кошелёк для указанной валюты уже существует,
        создание повторного кошелька не допускается.
        Args:
            currency_code: Код добавляемой валюты.
        Returns:
            Wallet: Созданный валютный кошелёк.
        Raises:
            ValueError: Если кошелёк для указанной валюты уже существует.
        """
        code = currency_code.strip().upper()

        if code in self._wallets:
            raise ValueError(f"Кошелёк {code} уже существует")

        wallet = Wallet(code)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet | None:
        """
        Возвращает кошелёк по коду валюты.
        Args:
            currency_code: Код искомой валюты.
        Returns:
            Wallet | None: Объект кошелька, если он существует,
                иначе None.
        """
        return self._wallets.get(currency_code.upper())

    def get_total_value(
        self,
        base_currency: str = "USD",
        rates: dict | None = None,
    ) -> float:
        """
        Рассчитывает общую стоимость всех кошельков портфеля
        в выбранной базовой валюте.
        Если курсы не переданы, используются значения
        из словаря EXCHANGE_RATES.
        Args:
            base_currency: Код базовой валюты для расчёта.
                По умолчанию USD.
            rates: Словарь курсов валют относительно USD.
                Если не указан, используются EXCHANGE_RATES.
        Returns:
            float: Общая стоимость портфеля в базовой валюте.
        Raises:
            ValueError: Если базовая валюта отсутствует в словаре
                курсов, её курс некорректен или отсутствует курс
                одной из валют портфеля.
        """
        if rates is None:
            rates = EXCHANGE_RATES

        base = base_currency.strip().upper()

        if base not in rates:
            raise ValueError(
                f"Неизвестная базовая валюта '{base}'"
            )

        base_rate = rates[base]

        if base_rate <= 0:
            raise ValueError(
                f"Некорректный курс базовой валюты '{base}'"
            )

        total = 0.0

        for code, wallet in self._wallets.items():
            if code not in rates:
                raise ValueError(
                    f"Нет курса для валюты '{code}'"
                )

            rate = rates[code]

            if rate <= 0:
                raise ValueError(
                    f"Некорректный курс валюты '{code}'"
                )

            total += wallet.balance * rate / base_rate

        return total
