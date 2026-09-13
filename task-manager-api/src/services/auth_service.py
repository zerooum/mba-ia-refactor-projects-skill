import logging

from itsdangerous import BadSignature, URLSafeTimedSerializer

from models.errors import ForbiddenError, UnauthorizedError, ValidationError

log = logging.getLogger(__name__)

TOKEN_SALT = 'auth-token'


class AuthService:
    def __init__(self, users, secret_key, token_max_age):
        self.users = users
        self.token_max_age = token_max_age
        self.serializer = URLSafeTimedSerializer(secret_key, salt=TOKEN_SALT)

    def login(self, data):
        """Devolve (usuário, token assinado)."""
        if not data:
            raise ValidationError('Dados inválidos')

        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')
        if not isinstance(email, str) or not isinstance(password, str):
            raise ValidationError('Email e senha devem ser texto')

        user = self.users.get_by_email(email)
        if not user or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        if user.has_legacy_hash():
            user.set_password(password)
            self.users.save(user)
            log.info('Hash de senha legado migrado: usuário %s', user.id)

        return user, self.serializer.dumps({'uid': user.id})

    def authenticate(self, token):
        """Usuário dono do token; UnauthorizedError se o token for inválido, expirado ou de usuário inativo."""
        try:
            payload = self.serializer.loads(token, max_age=self.token_max_age)
        except BadSignature:  # inclui SignatureExpired
            raise UnauthorizedError('Token inválido ou expirado') from None

        user = self.users.get(payload.get('uid')) if isinstance(payload, dict) else None
        if not user or not user.active:
            raise UnauthorizedError('Token inválido ou expirado')
        return user
