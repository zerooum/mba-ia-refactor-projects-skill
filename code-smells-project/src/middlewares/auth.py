import hmac
from functools import wraps

from flask import request

from src.models.errors import UnauthorizedError

HEADER_ADMIN_TOKEN = "X-Admin-Token"


def requer_token_admin(token_esperado):
    """Exige o header X-Admin-Token igual ao ADMIN_TOKEN configurado. Sem token configurado, nega sempre."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            recebido = request.headers.get(HEADER_ADMIN_TOKEN, "")
            if not token_esperado or not hmac.compare_digest(recebido.encode(), token_esperado.encode()):
                raise UnauthorizedError("Não autorizado")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
