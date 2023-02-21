import logging
import logging.config
import os
import sys
import time

from dotenv import load_dotenv
import requests
import telegram

from exceptions import (CustomKeyError, CustomNoTlgError, CustomRequestError,
                        CustomTlgError, CustomTlgSendMessageError,
                        CustomTokenValidationError, CustomTypeError)
from logger_config import logger_config

load_dotenv()

logger = logging.getLogger('bot')

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

ENDPOINT = os.getenv('ENDPOINT')
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
RETRY_TIME = 600


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в телеграм."""

    logger.debug('Message sending started.')

    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as err:
        raise CustomTlgSendMessageError(err)
    else:
        logger.debug('Successful message sending.')


def get_api_answer(current_timestamp: int) -> dict:
    """Отправка запроса к API Яндекс.Практикума."""

    logger.debug('API requesting started.')

    params = {'from_date': current_timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        err_message = (
            f'''Error while API requesting:
            endpoint: {ENDPOINT},
            headers: {HEADERS},
            params: {params},
            error: {err}
            '''
        )

        raise CustomRequestError(err_message)
    else:
        logger.debug('Successful API requesting.')

        return response.json()


def check_response(response: dict) -> list:
    """Проверка ответа API Яндекс.Практикума."""

    logger.debug('API answer checking started.')

    homeworks = response.get('homeworks')

    if not isinstance(response, dict):
        raise CustomTypeError('API response is not a dictionary.')
    if 'homeworks' not in response:
        raise CustomKeyError('Key "homeworks" is missing from response.')
    if 'current_date' not in response:
        raise CustomKeyError('Key "current_date" is missing from response.')
    if not isinstance(homeworks, list):
        raise CustomTypeError('Object "homeworks" is not a list.')

    return homeworks


def parse_status(homework: dict) -> str:
    """Получение имени и статуса домашней работы."""

    logger.debug('Homework\'s name and status parsing started.')

    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if not isinstance(homework, dict):
        raise CustomTypeError('Object homework is not a dictionary.')
    if 'homework_name' not in homework:
        raise CustomKeyError('Key "homework_name" is missing from homework.')
    if 'status' not in homework:
        raise CustomKeyError('Key "status" is missing from homework.')
    if homework_status not in HOMEWORK_STATUSES:
        raise CustomKeyError('Undocumented homework status.')

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> None:
    """Проверяет необходимые переменные окружения перед запуском приложения."""

    logger.debug('Token validation started.')

    tokens = (PRACTICUM_TOKEN, ENDPOINT, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

    if not all(tokens):
        raise CustomTokenValidationError('Token validation failed.')


def main():
    logging.config.dictConfig(logger_config)

    logger.info('Bot started!')

    try:
        check_tokens()
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
    except (CustomTokenValidationError, telegram.error.InvalidToken) as err:
        logger.critical(err, exc_info=True)
        sys.exit()

    current_timestamp = 0
    previous_error = None

    while True:
        try:
            logger.info('New pooling cycle.')

            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)

            if homeworks:
                for homework in homeworks:
                    homework_status = parse_status(homework)
                    send_message(bot, homework_status)
            else:
                logger.debug('Nothing new.')

            current_timestamp = response.get('current_date', int(time.time()))

        except CustomNoTlgError as err:
            logger.error(err, exc_info=True)
        except CustomTlgError as err:
            logger.error(err, exc_info=True)

            if err != previous_error:
                previous_error = err
                send_message(bot, err)
        except Exception as err:
            logger.critical(err, exc_info=True)

            message = (
                f'Unexpected exception, error: {err}'
            )
            send_message(bot, message)

            sys.exit()
        finally:
            logger.info('Pooling cycle finished.')

            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped!')
