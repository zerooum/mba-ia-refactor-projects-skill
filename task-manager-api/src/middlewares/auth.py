from functools import wraps

from flask import g, request

from models.errors import UnauthorizedError


class AuthMiddleware:
    """Guards de rota: `required` exige Bearer token válido; `optional` identifica o usuário se houver token."""

    def __init__(self, auth_service):
        self.auth_service = auth_service

    def required(self, view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            token = self._bearer_token()
            if token is None:
                raise UnauthorizedError('Token de autenticação ausente')
            g.current_user = self.auth_service.authenticate(token)
            return view(*args, **kwargs)
        return wrapper

    def optional(self, view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            token = self._bearer_token()
            g.current_user = self.auth_service.authenticate(token) if token else None
            return view(*args, **kwargs)
        return wrapper

    @staticmethod
    def _bearer_token():
        scheme, _, token = request.headers.get('Authorization', '').partition(' ')
        token = token.strip()
        return token if scheme.lower() == 'bearer' and token else None
