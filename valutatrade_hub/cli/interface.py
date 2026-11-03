import argparse
import shlex

# from prettytable import PrettyTable
from valutatrade_hub.core import usecases
from valutatrade_hub.core.models import User


current_user: User | None = None

def build_parser():
    """
    Создаёт и настраивает парсер аргументов командной строки.
    Регистрирует доступные команды приложения и их параметры:
    регистрацию и авторизацию, работу с портфелем, покупку и продажу
    валют, получение и обновление курсов, а также служебные команды.
    Returns:
        argparse.ArgumentParser: Настроенный парсер команд.
    """
    parser = argparse.ArgumentParser(
        prog="valutatrade",
        description="Симулятор торговли валютами",
    )
    commands = parser.add_subparsers(dest="command")

    register = commands.add_parser("register")
    register.add_argument("--username", required=True)
    register.add_argument("--password", required=True)

    login = commands.add_parser("login")
    login.add_argument("--username", required=True)
    login.add_argument("--password", required=True)

    commands.add_parser("logout")

    portfolio = commands.add_parser("show-portfolio")
    portfolio.add_argument("--base", default="USD")

    buy = commands.add_parser("buy")
    buy.add_argument("--currency", required=True)
    buy.add_argument("--amount", required=True, type=float)

    sell = commands.add_parser("sell")
    sell.add_argument("--currency", required=True)
    sell.add_argument("--amount", required=True, type=float)

    rate = commands.add_parser("get-rate")
    rate.add_argument("--from", dest="from_currency", required=True)
    rate.add_argument("--to", dest="to_currency", required=True)

    commands.add_parser("change_password")
    commands.add_parser("help")
    commands.add_parser("exit")

    return parser


def print_help():
    """
    Выводит список доступных команд приложения и примеры их использования.
    Информация включает команды регистрации, авторизации,
    управления портфелем, работы с валютами и завершения программы.
    """
    print("""
Доступные команды:

  register --username alice --password 1234
  login --username alice --password 1234
  logout
  change_password
  show-portfolio
  show-portfolio --base EUR
  buy --currency BTC --amount 0.05
  sell --currency BTC --amount 0.01
  get-rate --from EUR --to USD
  help
  exit
""")


def execute(args):
    """
    Выполняет команду, переданную пользователем через командную строку.
    В зависимости от выбранной команды вызывает соответствующие функции
    бизнес-логики, проверяет авторизацию пользователя и выводит
    результаты выполнения или сообщения об ошибках.
    Args:
        args (argparse.Namespace): Пространство имён с командой
            и переданными пользователем аргументами.
    Returns:
        bool | None: False, если выбрана команда завершения приложения;
            True — если выполнение команды завершено;
            None — если выполнение команды прервано досрочно.
    """
    global current_user

    if args.command == "register":
        user = usecases.register(args.username, args.password)
        print(
            f"Пользователь '{user.username}' зарегистрирован "
            f"(id={user.user_id}). Войдите: login --username "
            f"{user.username} --password ****"
        )

    elif args.command == "login":
        current_user = usecases.login(args.username, args.password)
        print(f"Вы вошли как '{current_user.username}'")

    elif args.command == "logout":
        if current_user is None:
            print("Вы не авторизованы")
        else:
            current_user = None
            print("Вы вышли из аккаунта")

    elif args.command == "show-portfolio":
        if current_user is None:
            print("Сначала выполните login")
            return

        data = usecases.show_portfolio(
            current_user.user_id,
            args.base,
        )

        print(
            f"Портфель пользователя '{data['username']}' "
            f"(база: {data['base']}):"
        )

        if not data["wallets"]:
            print("Портфель пуст")
            return

        print(f"{'Валюта':<10} {'Баланс':>18} "
          f"{'Стоимость (' + data['base'] + ')':>22}")
        for item in data["wallets"]:
            balance = f"{item['balance']:.8f}".rstrip("0").rstrip(".")
            value = f"{item['value']:.2f}"
            print(f"{item['currency']:<10} {balance:>18} {value:>22}")
        print(f"\nИТОГО: {data['total']:.2f} {data['base']}")

        # table = PrettyTable()
        # table.field_names = [
        #     "Валюта", "Баланс", f"Стоимость ({data['base']})"
        # ]

        # for item in data["wallets"]:
        #     table.add_row([
        #         item["currency"],
        #         f"{item['balance']:.8f}".rstrip("0").rstrip("."),
        #         f"{item['value']:.2f}",
        #     ])

        # print(table)
        # print(f"ИТОГО: {data['total']:.2f} {data['base']}")

    # elif args.command == "show-portfolio":
    #     if current_user is None:
    #         print("Сначала выполните login")
    #         return

    #     data = usecases.show_portfolio(
    #         current_user.user_id,
    #         args.base,
    #     )

    #     print(
    #         f"\nПортфель пользователя '{data['username']}' "
    #         f"(база: {data['base']}):"
    #     )

    #     if not data["wallets"]:
    #         print("Портфель пуст")
    #         return

    #     table = PrettyTable()

    #     table.field_names = [
    #         "Валюта",
    #         "Баланс",
    #         f"Стоимость ({data['base']})",
    #     ]

    #     table.align["Валюта"] = "l"
    #     table.align["Баланс"] = "r"
    #     table.align[f"Стоимость ({data['base']})"] = "r"

    #     for item in data["wallets"]:
    #         balance = (
    #             f"{item['balance']:.8f}".rstrip("0").rstrip(".")
    #         )
    #         value = f"{item['value']:,.2f}"

    #         table.add_row([
    #             item["currency"],
    #             balance,
    #             value,
    #         ])

    #     print(table)

    #     print(
    #         f"\nИТОГО: {data['total']:,.2f} {data['base']}"
    #     )

    elif args.command == "buy":
        if current_user is None:
            print("Сначала выполните login")
            return
        try:
            result = usecases.buy(
                current_user.user_id,
                args.currency,
                args.amount,
            )

            print(
                f"Покупка выполнена: {result['amount']:.4f} "
                f"{result['currency']} по курсу "
                f"{result['rate']:.2f} USD/{result['currency']}"
            )
            print("Изменения в портфеле:")
            print(
                f"- {result['currency']}: было "
                f"{result['old_balance']:.4f} → стало "
                f"{result['balance']:.4f}"
            )
            print(
                f"Оценочная стоимость покупки: "
                f"{result['cost']:,.2f} USD"
            )
        except ValueError as exc:
            print(f"Не удалось выполнить покупку: {exc}")

    
    elif args.command == "sell":
        if current_user is None:
            print("Сначала выполните login")
            return
        try:
            result = usecases.sell(
                current_user.user_id,
                args.currency,
                args.amount,
            )

            print(
                f"Продажа выполнена: {result['amount']:.4f} "
                f"{result['currency']} по курсу "
                f"{result['rate']:.2f} USD/{result['currency']}"
            )
            print("Изменения в портфеле:")
            print(
                f"- {result['currency']}: было "
                f"{result['old_balance']:.4f} → стало "
                f"{result['balance']:.4f}"
            )
            print(
                f"Оценочная выручка: "
                f"{result['revenue']:,.2f} USD"
            )
        except ValueError as exc:
            print(f"Не удалось выполнить продажу: {exc}")


    elif args.command == "get-rate": 
        try:
            result = usecases.get_rate(
                args.from_currency,
                args.to_currency,
            )
            print(
                f"Курс {result['from']}→{result['to']}: "
                f"{result['rate']:.8f}"
            )
            print(
                f"Обратный курс {result['to']}→{result['from']}: "
                f"{result['reverse_rate']:.8f}"
            )
            print(f"Время кеша: {result['updated_at']}")
        except ValueError as exc:
            print(f"Некорректные параметры: {exc}")

    
    elif args.command == "change_password":
        if current_user is None:
            print("Сначала войдите в систему.")
            return
        new_password = input("Введите новый пароль: ")
        usecases.change_password(current_user.user_id, new_password)
        print("Пароль успешно изменён.")

    elif args.command == "help":
        print_help()

    elif args.command == "exit":
        return False

    return True


def run():
    """
    Запускает интерактивный интерфейс командной строки приложения.
    Создаёт парсер команд, отображает приветственное сообщение
    и запускает основной цикл обработки пользовательского ввода.
    Разбирает введённые команды, передаёт их функции execute()
    и обрабатывает возникающие исключения.
    Завершает работу при вводе команды exit или прерывании
    выполнения пользователем.
    """
    parser = build_parser()
    print("ValutaTrade Hub. Введите help для списка команд.")

    while True:
        try:
            command = input("valutatrade> ").strip()

            if not command:
                continue

            args = parser.parse_args(shlex.split(command))

            if execute(args) is False:
                print("До свидания!")
                break

        except SystemExit:
            continue
        except (ValueError, KeyError, OSError) as exc:
            print(f"Ошибка: {exc}")
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания!")
            break
