class ServiceError(Exception):
    """Domain error surfaced to GraphQL clients as a clean message."""


class NotAuthenticated(ServiceError):
    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message)


class NotFound(ServiceError):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message)


class Conflict(ServiceError):
    pass


class InvalidInput(ServiceError):
    pass
