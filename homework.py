import json
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException
from telegram import Bot, TelegramError

from exceptions import NotTwoHundred, JSONError
logger = logging.getLogger(__name__)
load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f'{message}',
        )
        logger.info('Сообщение отправлено')
    except TelegramError:
        logger.error('Ошибка отправки')


def get_api_answer(current_timestamp):
    """Получение информации о домашних работах."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params,
        )
    except RequestException:
        raise RequestException('Ошибка запроса')
    if response.status_code == HTTPStatus.OK:
        try:
            return response.json()
        except json.JSONDecodeError:
            raise JSONError('Ошибка кодировки')
    else:
        raise NotTwoHundred


def check_response(response):
    """Проверка запроса."""
    if not isinstance(response, dict):
        raise TypeError('Ошибка типа')
    elif 'homeworks' not in response:
        raise KeyError('Ошибка ключа')
    elif isinstance(response['homeworks'], list):
        return response['homeworks']


def parse_status(homework):
    """Проверка статуса."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError:
        raise KeyError('Ошибка ключа')


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    old_message = ''
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
        handlers=[
            logging.FileHandler('main.log', 'w', 'UTF-8'),
            logging.StreamHandler(stream=sys.stdout)
        ]
    )
    if not check_tokens():
        sys.exit('Отсутствие переменных окружения')
    while True:
        try:
            response = get_api_answer(current_timestamp=current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
            if old_message != message:
                send_message(bot, message)
                old_message = message
            else:
                logger.debug('Статус не изменился')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
