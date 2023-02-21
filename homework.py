import telegram
import requests
import time

from typing import Any
from http import HTTPStatus

import exceptions
from consts import (
    PRACTICUM_TOKEN,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
    HEADERS,
    RETRY_TIME,
    ENDPOINT,
    HOMEWORK_STATUSES
)
from log_func import log_runner

logging = log_runner('MyLogger').getChild(__name__)


def send_message(bot, message) -> None:
    """Отправка сообщения в Telegram чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp) -> Any:
    """Отправка запросf к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except exceptions.APIAnswerException as error:
        logging.error('Ошибка при запросе к основному API: %s', error)
        raise exceptions.APIAnswerException(
            f'Ошибка при запросе к основному API: {error}'
        )
    if response.status_code != HTTPStatus.OK:
        logging.error(
            'Ошибка в работе API кода: %s',
            response.status_code,
            response.text
        )
        raise exceptions.APIAnswerException(
            f'Ошибка в работе API кода {response.status_code}'
        )
    return response.json()


def check_response(response) -> list:
    """Проверка ответа API на корректность."""
    try:
        homework_list = response['homeworks']
    except KeyError as error:
        raise exceptions.CheckAPIException(f'Ошибка доступа по ключу {error}')
    if homework_list is None:
        raise exceptions.CheckAPIException('Списка домашних заданий нет')
    if not isinstance(homework_list, list):
        raise exceptions.CheckAPIException(
            'Ответ от API не является списком')
    if len(homework_list) == 0:
        raise exceptions.CheckAPIException(
            'Домашнего задания нет за данный промежуток времени')
    return homework_list


def parse_status(homework) -> str:
    """Извлечение из информации о конкретной домашней работе."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        raise KeyError(
            'Отсутствует название домашней работы'
        )
    if homework_status is None:
        raise exceptions.ParseStatusException(
            'Отсутствует статус домашней работы'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        raise exceptions.ParseStatusException(
            'Статус домашней работы неизвестен'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка доступности переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует один или более токен.')
        raise exceptions.CheсkTokensException(
            'Отсутствует один или более токен.'
        )
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework_list = check_response(response)
            current_timestamp = response.get('current_date')
            homework = homework_list[0]
            message = parse_status(homework)
            send_message(bot, message)
            logging.info('Сообщение отправлено: %s', message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error('Ошибка: %s', message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
