class NotTwoHundred(Exception):
    pass


def not_two_hundred(value):
    if value != 200:
        raise NotTwoHundred('Ошибка соединения')


class JSONError(Exception):
    pass


def JSONError(value):
    raise JSONError('Ошибка кодировки')
