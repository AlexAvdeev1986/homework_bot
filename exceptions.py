class InvalidTokens(Exception):
    pass


class EndpointFailureResponseCodes(Exception):
    pass


class ResponseFormatFailure(Exception):
    pass


class WrongStatusInResponse(Exception):
    pass


class ChatbotMessagesError(Exception):
    """Raised when there is an error in send_message function."""
    pass
