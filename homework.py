import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Dict, List, Union

import requests
import telegram
from dotenv import load_dotenv

from exceptions import CantSendMessageError

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

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s - %(levelname)s - "
    "%(funcName)s - %(lineno)d - %(message)s",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def check_tokens() -> None:
    """Проверяет, что токены получены.

    Райзит исключение при потере какого-либо токена.
    """
    required_tokens = (
        "PRACTICUM_TOKEN",
        "TELEGRAM_TOKEN",
        "TELEGRAM_CHAT_ID",
    )
    if all(
        token in globals() and globals().get(token) is not None
        for token in required_tokens
    ):
        logging.info("All required tokens are present.")
        return True
    else:
        missing_tokens = [
            token
            for token in required_tokens
            if token not in globals() or globals().get(token) is None
        ]
        logging.critical("Missing required tokens: %s", *missing_tokens)
        return False


def send_message(bot: telegram.Bot, text: str) -> None:
    """Бот отправляет текст сообщения в телеграм.
    При неудачной попытке отправки сообщения логируется исключение
    TelegramError и выбрасывается исключение об невозможности
    отправить сообщение в Telegram.
    """
    try:
        bot.send_message(
            TELEGRAM_CHAT_ID,
            text=text,
        )
    except telegram.error.TelegramError:
        logging.exception("Cбой при отправке сообщения в Telegram")
        raise CantSendMessageError(
            "Невозможно отправить сообщение в Telegram"
        )
    logging.debug("Сообщение о статусе домашки отправлено")


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


def check_response(
    response: Dict[str, Union[List[Dict[str, Union[int, str]]], int]]
) -> List[Dict[str, Union[int, str]]]:
    """Проверяет, соответствует ли тип входных данных ожидаемому.
    Проверяет наличие всех ожидаемых ключей в ответе.
    Райзит TypeError при несоответствии типа данных,
    KeyError - при отсутствии ожидаемого ключа.
    """
    if (
        isinstance(response, dict)
        and all(key for key in ("current_date", "homeworks"))
        and isinstance(response.get("homeworks"), list)
    ):
        logging.info(
            'Все ключи из "response" получены и соответствуют норме'
        )
        return response["homeworks"]
    raise TypeError("Структура данных не соответствует ожиданиям")


def parse_status(homework):
    """Проверяет статус домашней работы.
    При наличии возвращает сообщение для отправки в Telegram.
    При отсутствии статуса или получении недокументированного статуса
    райзит исключение.
    """
    current_status = ("rejected", "reviewing", "approved", "denied")
    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")
    if homework_name in (None, "") or homework_status not in current_status:
        logger.error(
            (
                f"Переменная homework_name - {homework_name}, "
                f"переменная homework_status - {homework_status}, "
                f"ошибка в переменной!!!"
            ),
            exc_info=True,
        )
        return "Неверный ответ сервера"
    elif homework_status == "rejected":
        verdict = "К сожалению, в работе нашлись ошибки."
    elif homework_status == "reviewing":
        verdict = "Работа взята в ревью. Ждите вердикта!"
    else:
        verdict = "Ревьюеру всё понравилось, работа зачтена!"
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


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
