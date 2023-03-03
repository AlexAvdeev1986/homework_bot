class InvalidTokens(Exception):
    pass


class EndpointFailureResponseCodes(Exception):
    pass


class ResponseFormatFailure(Exception):
    pass


class WrongStatusInResponse(Exception):
    pass

class SendMessageError(Exception):
    """Собственное исключение."""
    pass