"""Exceções de domínio. O error handler traduz cada uma para HTTP."""


class AppError(Exception):
    """Erro de domínio. `extra` entra no corpo da resposta junto com "erro"."""

    status = 400

    def __init__(self, message, **extra):
        super().__init__(message)
        self.message = message
        self.extra = extra


class ValidationError(AppError):
    status = 400


class BusinessRuleError(AppError):
    status = 400


class NotFoundError(AppError):
    status = 404


class UnauthorizedError(AppError):
    status = 401
