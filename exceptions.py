class SendMessageException(Exception):
    """"Ошибка при при отправке в Telegram"""
    pass


class APIAnswerException(Exception):
    """"Ошибка при запросе к эндпоинту API-сервиса"""
    pass


class CheckAPIException(Exception):
    """"Ошибка при ответе от API-сервиса"""
    pass


class ParseStatusException(Exception):
    """"Ошибка при извлечении статуса домашней работы"""
    pass


class CheсkTokensException(Exception):
    """"Ошибка при отсуствие токена"""
    pass
