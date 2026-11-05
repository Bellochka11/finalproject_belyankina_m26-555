import logging
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from inspect import signature
from typing import Any

logger = logging.getLogger("valutatrade.actions")


def _format_value(value: Any) -> str:
    """
    Форматирует значение для записи в лог.
    Вещественные числа округляет до четырёх знаков после запятой,
    остальные значения преобразует в строковое представление
    с помощью repr().
    Args:
        value (Any): Значение для форматирования.
    Returns:
        str: Отформатированное строковое представление значения.
    """
    if isinstance(value, float):
        return f"{value:.4f}"
    return repr(value)


def log_action(
    action: str | None = None,
    *,
    verbose: bool = False,
) -> Callable:
    """
    Создаёт декоратор для логирования результатов доменных операций.
    Записывает информацию о выполненной операции: временную метку,
    название действия, пользователя, валюту, сумму и результат.
    При возникновении исключения записывает его тип и сообщение,
    после чего повторно возбуждает исключение.
    Поддерживает дополнительное подробное логирование балансов
    до и после операции.
    Args:
        action (str | None): Пользовательское название операции.
            Если None, используется имя декорируемой функции.
        verbose (bool): Включает подробное логирование дополнительных
            данных, полученных из результата операции.
            По умолчанию False.
    Returns:
        Callable: Декоратор для применения к доменной функции.
    """

    def decorator(func: Callable) -> Callable:
        """
        Подготавливает функцию к логированию.
        Определяет название операции, получает сигнатуру
        декорируемой функции и создаёт обёртку для перехвата
        результатов её выполнения.
        Args:
            func (Callable): Декорируемая доменная функция.
        Returns:
            Callable: Обёрнутая функция с логированием.
        """
        operation = (action or func.__name__).upper()
        func_signature = signature(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Выполняет доменную операцию и записывает её результат в лог.
            Получает аргументы функции, исключает секретные данные
            из логирования, формирует информацию об операции
            и записывает результат её выполнения.
            При успешном выполнении записывает статус OK.
            При возникновении исключения записывает статус ERROR,
            тип и сообщение ошибки, после чего повторно возбуждает
            исключение.
            При включённом verbose дополнительно записывает
            информацию о балансах и контексте операции.
            Args:
                *args (Any): Позиционные аргументы функции.
                **kwargs (Any): Именованные аргументы функции.
            Returns:
                Any: Результат выполнения декорируемой функции.
            Raises:
                Exception: Повторно возбуждает любое исключение,
                    возникшее при выполнении декорируемой функции.
            """
            bound = func_signature.bind(*args, **kwargs)
            bound.apply_defaults()
            params = bound.arguments

            # Не логируем пароли и другие секретные аргументы.
            user = params.get("username", params.get("user_id", "unknown"))
            currency = params.get("currency", params.get("currency_code"))
            amount = params.get("amount")

            fields = {
                "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                "action": operation,
                "user": user,
                "currency": currency,
                "amount": amount,
            }

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                fields.update(
                    {
                        "result": "ERROR",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    }
                )
                logger.info(
                    " ".join(
                        f"{key}={_format_value(value)}"
                        for key, value in fields.items()
                        if value is not None
                    )
                )
                raise

            fields["result"] = "OK"

            if isinstance(result, dict):
                for key in ("rate", "base"):
                    if result.get(key) is not None:
                        fields[key] = result[key]

                if verbose:
                    balance_fields = {
                        "balance_before": "old_balance",
                        "balance_after": "balance",
                        "context": "context",
                    }

                    for log_key, result_key in balance_fields.items():
                        if result.get(result_key) is not None:
                            fields[log_key] = result[result_key]

            logger.info(
                " ".join(
                    f"{key}={_format_value(value)}"
                    for key, value in fields.items()
                    if value is not None
                )
            )
            return result

        return wrapper

    return decorator
