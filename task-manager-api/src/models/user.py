import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from infra.database import db
from models.constants import ADMIN_ROLE, DEFAULT_ROLE, PASSWORD_MIN_LENGTH, USER_ROLES
from models.errors import ValidationError
from utils.helpers import utc_now, validate_email

# formato gravado antes da migração para werkzeug.security: MD5 hex, sem salt
LEGACY_MD5_HASH = re.compile(r'[0-9a-f]{32}')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        if self.has_legacy_hash():
            # só para contas antigas; o AuthService regrava o hash no primeiro login válido
            return hmac.compare_digest(self.password, hashlib.md5(pwd.encode()).hexdigest())
        return check_password_hash(self.password, pwd)

    def has_legacy_hash(self):
        return bool(LEGACY_MD5_HASH.fullmatch(self.password or ''))

    def is_admin(self):
        return self.role == ADMIN_ROLE

    @staticmethod
    def validate_email(email):
        if not isinstance(email, str) or not validate_email(email):
            raise ValidationError('Email inválido')
        return email

    @staticmethod
    def validate_password(password):
        if not isinstance(password, str):
            raise ValidationError('Senha inválida')
        if len(password) < PASSWORD_MIN_LENGTH:
            raise ValidationError('Senha deve ter no mínimo 4 caracteres')
        return password

    @staticmethod
    def validate_role(role):
        if role not in USER_ROLES:
            raise ValidationError('Role inválido')
        return role

    @staticmethod
    def validate_active(active):
        # mesma regra do tipo Boolean do SQLAlchemy, que hoje estourava 500 no commit
        if active not in (True, False, None):
            raise ValidationError('Campo active inválido')
        return active
