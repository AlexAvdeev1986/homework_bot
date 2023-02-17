"""Класс исключений бота"""
class APIError(Exception):
    """Для ожидаемых базовых ошибок API"""
    def __init__(self, message):
        """Конструктор"""
        self.message = message
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Исключение"""
        return self.message