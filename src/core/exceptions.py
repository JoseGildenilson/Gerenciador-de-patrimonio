"""Exceções de domínio e aplicação."""


class ConflictError(Exception):
    """Exceção levantada quando ocorre conflito de unicidade ou estado concorrente (HTTP 409)."""

    pass


class NotFoundError(Exception):
    """Exceção levantada quando um recurso solicitado não é encontrado (HTTP 404)."""

    pass


class BusinessRuleError(Exception):
    """Exceção para violação de regras de negócio específicas (HTTP 400)."""

    pass
