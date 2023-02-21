class APIStatusCodeError(Exception):
    """Неверный ответ сервера."""
    pass


class TelegramError(Exception):
    """Ошибка отправки сообщения в телеграм."""
    pass
