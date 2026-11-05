class InsufficientFundsError(ValueError):
    """
    Исключение, возникающее при недостаточном балансе кошелька
    для выполнения финансовой операции.
    Attributes:
        available (float): Количество доступных средств.
        required (float): Количество средств, необходимое для операции.
        code (str): Код валюты кошелька.
    """

    def __init__(
        self,
        available: float,
        required: float,
        code: str,
    ) -> None:
        """
        Инициализирует исключение с информацией о нехватке средств.
        Args:
            available: Текущий доступный баланс.
            required: Требуемая сумма.
            code: Код валюты, в которой выполняется операция.
        """
        self.available = available
        self.required = required
        self.code = code.upper()

        super().__init__(
            f"Недостаточно средств: доступно {available:.4f} "
            f"{self.code}, требуется {required:.4f} {self.code}"
        )


class CurrencyNotFoundError(LookupError):
    """
    Исключение, возникающее при обращении к неподдерживаемой валюте.
    Attributes:
        code (str): Нормализованный код неизвестной валюты.
    """

    def __init__(self, code: str) -> None:
        """
        Инициализирует исключение с кодом неизвестной валюты.
        Args:
            code: Код валюты, которая не найдена в реестре.
        """
        self.code = code.strip().upper()
        super().__init__(f"Неизвестная валюта '{self.code}'")


class ApiRequestError(RuntimeError):
    """
    Исключение, возникающее при ошибках получения или обработки
    данных от внешних API.
    Attributes:
        reason (str): Описание причины возникновения ошибки.
    """

    def __init__(self, reason: str) -> None:
        """
        Инициализирует исключение с описанием причины ошибки.
        Args:
            reason: Причина неудачного обращения к внешнему API.
        """
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
