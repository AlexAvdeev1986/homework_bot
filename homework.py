import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Dict, List

import requests
import telegram
from dotenv import load_dotenv

from exceptions import APIStatusCodeError, TelegramError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        logging.info('Отправляем сообщение в телеграм')
        bot.send_message(TELEGRAM_CHAT_ID, message)

    except Exception as exc:
        raise TelegramError(
            f'Ошибка отправки сообщения в телеграм: {exc}'
        ) from exc

    else:
        logging.info('Сообщение в телеграм успешно отправлено')


def get_api_answer(current_timestamp: int) -> Dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    logging.info('Делаем запрос на Яндекс.Практикум')

    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )

    except Exception as exc:
        raise APIStatusCodeError(
            f'Неверный ответ сервера: {exc}'
        )

    if response.status_code != HTTPStatus.OK:
        raise APIStatusCodeError(
            f'Неверный ответ сервера {ENDPOINT}. '
            f'Параметры запроса: {params}'
        )

    return response.json()


def check_response(response: Dict) -> List:
    """Проверяет ответ API на корректность."""
    logging.info('Проверка ответа от API начата')

    if not isinstance(response, dict) or response is None:
        raise TypeError(
            'Ответ от API не является словарём'
        )

    response_homeworks = response.get('homeworks')
    response_current_date = response.get('current_date')

    if response_homeworks is None or response_current_date is None:
        raise KeyError(
            'Словарь ответа API не содержит ключей homeworks и/или '
            'current_date'
        )

    if not isinstance(response.get('homeworks'), list):
        raise TypeError(
            'Ключ homeworks в ответе API не содержит списка'
        )

    else:
        return response['homeworks']


def parse_status(homework: Dict) -> str:
    """Извлекает статус о конкретной домашней работе."""
    if homework.get('homework_name') is None:
        raise KeyError(
            'Словарь ответа API не содержит ключa homework_name'
        )

    homework_name = homework['homework_name']

    if homework.get('status') is None:
        raise KeyError(
            'Словарь ответа API не содержит ключa status'
        )

    homework_status = homework['status']

    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError('Недокументированный статус домашней работы')

    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения."""
    return all((
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ))


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        error_message = (
            'Отсутствуют обязательные переменные окружения: '
            'TELEGRAM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID. '
            'Программа принудительно остановлена'
        )
        logging.critical(error_message)
        sys.exit(error_message)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    prev_message = ''
    prev_error = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            homework = homework[0]
            message = parse_status(homework)

            if prev_message != message:
                send_message(bot, message)
                prev_message = message

        except Exception as exc:
            message = f'Сбой в работе программы: {exc}'
            logging.exception(message)

            if prev_error != message:
                send_message(bot, message)
                prev_error = message

        finally:
            current_timestamp = response.get('current_date', current_timestamp)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    log_format = (
        '%(asctime)s [%(levelname)s] [%(lineno)d] %(message)s'
    )
    log_file = os.path.join(BASE_DIR, 'output.log')
    log_stream = sys.stdout
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding="UTF-8"),
            logging.StreamHandler(log_stream)
        ]
    )
    main()
