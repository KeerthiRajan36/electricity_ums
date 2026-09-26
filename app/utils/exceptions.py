class AppException(Exception):
    """Base class for all handled application errors."""
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundException(AppException):
    status_code = 404


class ConflictException(AppException):
    """Raised on unique-constraint style business rule violations (duplicates)."""
    status_code = 409


class BadRequestException(AppException):
    status_code = 400


class UnauthorizedException(AppException):
    status_code = 401


class ForbiddenException(AppException):
    status_code = 403
