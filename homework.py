import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Dict, List, Union

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    NoHomeworkDetectedError,
    EmptyListException,
    InvalidApiExc,
    InvalidResponseExc,
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 60 * 10  # перевод 10 минут в секунды. 10 * 60 = 600 секунд
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Проверка наличия всех токенов в переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(tokens)


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f"Бот отправил сообщение: {message}")
    except Exception as error:
        logger.error(f"Ошибка отправки сообщения: {error}")


def get_api_answer(
    timestamp: int,
) -> Dict[str, Union[List[Dict[str, Union[int, str]]], int]]:
    """Получает ответ от API.
    Райзит исключение при недоступности эндпоинта
    или других сбоях при запросе к нему.
    """
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={"from_date": timestamp},
        )
    except requests.exceptions.RequestException:
        logging.exception("Сбой при запросе к эндпоинту")
        raise requests.exceptions.RequestException(
            "Ошибка при запросе к API: %s",
            response.status_code,
        )
    logging.info("Ответ от API получен. Эндпоинт доступен.")
    if response.status_code != HTTPStatus.OK:
        logging.error(
            "Данный эндпоинт недоступен - %s. Код ошибки: %s",
            response.url,
            response.status_code,
        )
        response.raise_for_status()

    return response.json()


def check_response(response):
    """Проверка ответа API и возврат списка работ."""
    if not isinstance(response, dict):
        raise TypeError("not dict после .json() в ответе API")
    if "homeworks" and "current_date" not in response:
        raise InvalidApiExc("Некорректный ответ API")
    if not isinstance(response.get("homeworks"), list):
        raise TypeError("not list в ответе API по ключу homeworks")
    if not response.get("homeworks"):
        raise EmptyListException("Новых статусов нет")
    try:
        return response.get("homeworks")[0]
    except Exception as error:
        raise InvalidResponseExc(f"Из ответа не получен список работ: {error}")


def parse_status(homework):
    """Проверяет статус домашней работы.
    При наличии возвращает сообщение для отправки в Telegram.
    При отсутствии статуса или получении недокументированного статуса
    райзит исключение.
    """
    try:
        name, status = homework["homework_name"], homework["status"]
    except KeyError:
        logging.error("Один или оба ключа отсутствуют")
        raise NoHomeworkDetectedError("Домашней работы нет")
    try:
        return (
            f'Изменился статус проверки работы "{name}". '
            f"{HOMEWORK_VERDICTS[status]}"
        )
    except KeyError:
        logging.error("Неожиданный статус домашней работы")
        raise KeyError("Статуса %s нет в словаре", status)


def main() -> None:
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    error_message = ""
    last_message = ""
    while True:
        try:
            response = get_api_answer(timestamp=timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(response.get("homeworks")[0])

                if message != last_message:
                    send_message(bot, message)
                    last_message = message

            timestamp = response["current_date"]

        except Exception as error:
            if error != error_message:
                message = f"Сбой в работе программы: {error}"
                send_message(bot, message)
                error_message = error

        finally:
            logging.info("Спящий режим")
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
