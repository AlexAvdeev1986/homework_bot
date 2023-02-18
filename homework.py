import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from api_error import APIError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def log_raise_error(error_message):
    """Логи и вызов исключения."""
    message = f'Программа "{error_message}" не работает'
    logger.error(message)
    raise APIError(message)


def send_message(bot, message):
    """Отправляет сообщение в чат TELEGRAM_CHAT_ID."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except telegram.TelegramError:
        error_message = f'Не получилось отправить сообщение "{message}".'
        log_raise_error(error_message)
    logger.info(f'Бот отправил сообщение "{message}"')


def get_api_answer(current_timestamp):
    """Запрос эндпоинта APIсервиса и преобразование к типам данных Python."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except requests.exceptions.RequestException:
        error_message = f'Сбой обращения к "{ENDPOINT}"'
        log_raise_error(error_message)
    if homework_statuses.status_code != HTTPStatus.OK.value:
        error_message = (f'"{ENDPOINT}" недоступен. '
                         f'Код ответа API: "{homework_statuses.status_code}"'
                         )
        log_raise_error(error_message)
    return homework_statuses.json()


def check_response(response):
    """Проверка ответ API на корректность, возврат списка домашних работ."""
    api_homeworks_key = 'homeworks'
    try:
        homeworks = response[api_homeworks_key]
        time_stamp = response['current_date']
    except KeyError as error:
        error_message = f'Ключа "{error}" нет в ответе API'
        log_raise_error(error_message)
    if not isinstance(homeworks, list):
        error_message = (
            f'Под ключом "{api_homeworks_key}" в ответе API '
            f'содержится некорректный тип: "{type(homeworks)}"')
        log_raise_error(error_message)
    if not homeworks:
        logger.debug(
            ('Статус домашней работы не изменился '
                f'с времени UNIX-time: "{time_stamp}"')
        )
    return homeworks


def parse_status(homework):
    """Извлечение статуса д/р, возврат вердикт словаря HOMEWORK_STATUSES."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    except KeyError:
        raise KeyError('Статус работы не документирован')
    if homework_status not in HOMEWORK_STATUSES:
        error_message = (f'Статус "{homework_status}" '
                         f'работы "{homework_name}" не найден')
        log_raise_error(error_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    data = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for token_key, token_value in data.items():
        if not token_value:
            logger.critical(f'Нет обязательной переменной "{token_key}"')
            return False
    return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previous_error = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            check_tokens()
            for homework in homeworks:
                verdict = parse_status(homework)
                send_message(bot, verdict)
        except APIError as error:
            try:
                if error.message != previous_error:
                    send_message(bot, error.message)
            except APIError as error:
                error_message = f'Сбой в работе программы: "{error}"'
                logger.error(error_message)
            else:
                previous_error = error.message
        except Exception as error:
            error_message = f'Базовая ошибка: "{error}"'
            logger.error(error_message)
        else:
            current_timestamp = response['current_date']
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
