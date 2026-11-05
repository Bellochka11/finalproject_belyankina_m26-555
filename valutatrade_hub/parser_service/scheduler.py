import time

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import UPDATE_INTERVAL_SECONDS
from valutatrade_hub.parser_service.updater import RatesUpdater


class RateScheduler:
    """
    Планировщик периодического обновления курсов валют.
    Запускает обновление курсов через заданные промежутки времени
    с использованием RatesUpdater. Обрабатывает ошибки обновления,
    не прерывая дальнейшую работу планировщика.
    Attributes:
        interval (int): Интервал между обновлениями в секундах.
        updater (RatesUpdater): Объект для получения и сохранения курсов.
    """

    def __init__(self, interval: int = UPDATE_INTERVAL_SECONDS):
        """
        Инициализирует планировщик обновления курсов.
        Создаёт экземпляр RatesUpdater и устанавливает интервал
        между автоматическими обновлениями.
        Args:
            interval: Интервал обновления курсов в секундах.
                По умолчанию используется значение из конфигурации.
        Raises:
            ValueError: Если интервал обновления меньше или равен нулю.
        """
        if interval <= 0:
            raise ValueError("Интервал обновления должен быть положительным")

        self.interval = interval
        self.updater = RatesUpdater()

    def run(self):
        """
        Запускает бесконечный цикл периодического обновления курсов.
        Выполняет обновление курсов через RatesUpdater, выводит
        информацию о результатах и обрабатывает ошибки API.
        Между обновлениями ожидает заданное количество секунд.
        При получении сигнала KeyboardInterrupt завершает работу
        планировщика.
        """
        print(f"Планировщик запущен. Интервал обновления: {self.interval} секунд.")

        try:
            while True:
                try:
                    print("\nЗапуск автоматического обновления курсов...")
                    self.updater.run_update()
                except ApiRequestError as exc:
                    print(f"Ошибка обновления курсов: {exc}")

                print(f"Следующее обновление через {self.interval} секунд.")
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\nПланировщик остановлен.")


if __name__ == "__main__":
    # Создание и запуск планировщика обновления курсов.
    scheduler = RateScheduler()
    scheduler.run()
