import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import StatusCodeError


load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

TOKEN_ERROR = "Oшибка переменных окружения"


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f"Сообщение в чат {TELEGRAM_CHAT_ID}: {message}")
    except Exception as error:
        raise SystemError("Ошибка отправки сообщения в Telegramm") from error


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    params = {"from_date": timestamp}
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
    homework_name = homework.get("homework_name")
    if not homework_name:
        raise KeyError("There is no homework_name key in the list.")
    homework_status = homework.get("status")
    homework_comment = homework.get("reviewer_comment")
    if not homework_status:
        raise KeyError("There is no status key in the list.")
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError("Unknown homework status.")
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}" . {verdict} {homework_comment}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    ERROR_CACHE_MESSAGE = ""
    if not check_tokens():
        logger.critical(TOKEN_ERROR)
        sys.exit(TOKEN_ERROR)

    while True:
        try:

            response = get_api_answer(timestamp)
            hw_list = check_response(response)
            if hw_list:
                send_message(bot, parse_status(hw_list[0]))
            else:
                logger.debug("Нет новых статусов")
                raise Exception("Нет новых статусов")

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            if message != ERROR_CACHE_MESSAGE:
                send_message(bot, message)
                ERROR_CACHE_MESSAGE = message
        finally:
            timestamp = response.get("current_date")
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
