class StatusCodeError(Exception):
    """Код запроса отличается."""
    pass

class NotForSend(Exception):
    """Исключение не для пересылки в telegram."""
    pass
