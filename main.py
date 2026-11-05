#!/usr/bin/env python3

from valutatrade_hub.cli.interface import run
from valutatrade_hub.logging_config import setup_logging


def main() -> None:
    """
    Запускает приложение ValutaTrade Hub.
    Настраивает систему логирования и запускает
    интерактивный интерфейс командной строки.
    Returns:
        None
    """
    setup_logging()
    run()


if __name__ == "__main__":
    main()
