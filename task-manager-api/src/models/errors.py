class DomainError(Exception):
    """Erro de regra de negócio. O error handler central converte `status` em código HTTP."""

    status = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    status = 400


class UnauthorizedError(DomainError):
    status = 401


class ForbiddenError(DomainError):
    status = 403


class NotFoundError(DomainError):
    status = 404


class ConflictError(DomainError):
    status = 409
