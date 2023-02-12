import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    StatusCodeError,
    NotForSend,
)

load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


TOKEN_ERROR = "Oшибка переменных окружения"


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f"Сообщение в чат {TELEGRAM_CHAT_ID}: {message}")
    except Exception as error:
        raise SystemError("Ошибка отправки сообщения в Telegramm") from error


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    params = {"from_date": current_timestamp}
    try:
        hw_status = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if hw_status.status_code != HTTPStatus.OK:
            raise StatusCodeError(f"Ошибка {hw_status.status_code}")
        return hw_status.json()
    except Exception as error:
        raise SystemError(f"Ошибка при запросе: {error}")


def check_response(response):
    """Проверяет ответ API на корректность."""
    logging.info("Проверка ответа от API")
    if not isinstance(response, dict):
        raise TypeError("Ответ API не является словарем")
    if "homeworks" not in response or "current_date" not in response:
        raise KeyError("Отсутствует ключ")
    homeworks = response["homeworks"]
    if not isinstance(homeworks, list):
        raise TypeError("Ответ API не является листом")
    return homeworks


def parse_status(homework):
    """Извлекает из информации о  домашней работе."""
    if "homework_name" not in homework:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    if "status" not in homework:
        raise KeyError('Отсутствует ключ "status" в ответе API')
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    if homework_status not in HOMEWORK_STATUSES:
        raise Exception(f"Неизвестный статус работы: {homework_status}")
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Функция main в ней описана основная логика работы программы."""
    if not check_tokens():
        message = "Отсутствует токен. Бот остановлен!"
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    start_message = "Бот начал работу"
    send_message(bot, start_message)
    logging.info(start_message)
    prev_msg = ""

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get("current_date", int(time.time()))
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
            else:
                message = "Нет новых статусов"
            if message != prev_msg:
                send_message(bot, message)
                prev_msg = message
            else:
                logging.info(message)

        except NotForSend as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(message, exc_info=True)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(message, exc_info=True)
            if message != prev_msg:
                send_message(bot, message)
                prev_msg = message

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        filename="homework.log",
        format="%(asctime)s, %(levelname)s, %(name)s, %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(handler)
    main()
