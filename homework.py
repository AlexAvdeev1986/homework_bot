import sys
from http import HTTPStatus
import logging
import time
import os
import json

import requests
import telegram
from dotenv import load_dotenv

from endpoint import ENDPOINT


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TELEGRAM_RETRY_TIME = 600
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправляем сообщение."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.info(f'Сообщение {message} отправлено.')
    except Exception:
        error = 'Сообщение не было отправлено.'
        raise telegram.error.TelegramError(error)


def get_api_answer(current_timestamp):
    """Получаем ответ от API Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logger.info('Отправляем запрос к API Практикума')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        error = 'Проблемы с подключением к серверу'
        raise ConnectionError(error)
    if response.status_code != HTTPStatus.OK:
        error = (
            f'Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {response.status_code}'
        )
        raise Exception(error)
    try:
        return response.json()
    except Exception:
        error = "Формат не соответствует формату JSON"
        raise json.decoder.JSONDecodeError(error)


def check_response(response):
    """Проверка ответа от API на корректность."""
    logger.info('Начинаем проверку ответа сервера')
    if not isinstance(response, dict):
        raise TypeError('response не является словарем')
    homeworks = response.get('homeworks')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('В словаре отсутствует необходимый ключ.')
    if not isinstance(homeworks, list):
        raise TypeError('"homeworks" должен иметь тип list')
    return homeworks


def parse_status(homework):
    """Получаем статус последней домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('В словаре отсутствует ключ "homework_name"')
    homework_name = homework['homework_name']
    if 'status' not in homework:
        raise KeyError('В словаре отсутствует ключ "status"')
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError('Недокументированный статус работы')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logger.critical('Отсутствует обязательная переменная окружения.')
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствует обязательная переменная окружения.')
        sys.exit()
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previous_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if message != previous_message:
                    send_message(bot, message)
                    previous_message = message
            else:
                logger.debug('В ответе отсутствует новый статус.')
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != previous_message:
                send_message(bot, message)
                previous_message = message
        finally:
            time.sleep(TELEGRAM_RETRY_TIME)


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(handler)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] -function %(funcName)s- '
        '-line %(lineno)d- %(message)s'
    )
    handler.setFormatter(formatter)
    main()
