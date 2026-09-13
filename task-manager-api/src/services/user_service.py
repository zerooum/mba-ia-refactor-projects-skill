import logging

from models.constants import DEFAULT_ROLE
from models.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from models.user import User

log = logging.getLogger(__name__)


class UserService:
    def __init__(self, users, tasks):
        self.users = users
        self.tasks = tasks

    def list_users(self):
        """[(usuário, nº de tasks)] — contagem agregada numa query só."""
        counts = self.tasks.count_by_user()
        return [(user, counts.get(user.id, (0, 0))[0]) for user in self.users.list_all()]

    def get_user(self, user_id):
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    def get_user_tasks(self, user_id):
        self.get_user(user_id)
        return self.tasks.list_by_user(user_id)

    def create_user(self, data, actor=None):
        """Cadastro é público; só um admin autenticado pode criar usuário com role diferente do padrão."""
        if not data:
            raise ValidationError('Dados inválidos')

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', DEFAULT_ROLE)

        self._require(name, 'Nome é obrigatório')
        self._require(email, 'Email é obrigatório')
        self._require(password, 'Senha é obrigatória')
        User.validate_email(email)
        User.validate_password(password)
        if self.users.get_by_email(email):
            raise ConflictError('Email já cadastrado')
        User.validate_role(role)
        if role != DEFAULT_ROLE and not self._is_admin(actor):
            raise ForbiddenError('Apenas administradores podem definir role')

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        self.users.add(user)
        log.info('Usuário criado: %s - %s', user.id, user.name)
        return user

    def update_user(self, user_id, data, actor):
        user = self.get_user(user_id)
        self._authorize_owner_or_admin(user, actor)
        if not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            self._require(data['name'], 'Nome é obrigatório')
        if 'email' in data:
            self._require(data['email'], 'Email é obrigatório')
            User.validate_email(data['email'])
            existing = self.users.get_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
        if 'password' in data:
            self._require(data['password'], 'Senha é obrigatória')
            User.validate_password(data['password'])
        if 'role' in data:
            User.validate_role(data['role'])
            if data['role'] != user.role and not self._is_admin(actor):
                raise ForbiddenError('Apenas administradores podem alterar role')
        if 'active' in data:
            User.validate_active(data['active'])

        for field in ('name', 'email', 'role', 'active'):
            if field in data:
                setattr(user, field, data[field])
        if 'password' in data:
            user.set_password(data['password'])

        self.users.save(user)
        return user

    def delete_user(self, user_id, actor):
        user = self.get_user(user_id)
        self._authorize_owner_or_admin(user, actor)
        self.users.delete_with_tasks(user)
        log.info('Usuário deletado: %s', user_id)

    @staticmethod
    def _is_admin(actor):
        return actor is not None and actor.is_admin()

    def _authorize_owner_or_admin(self, user, actor):
        if not (self._is_admin(actor) or (actor is not None and actor.id == user.id)):
            raise ForbiddenError('Acesso negado')

    @staticmethod
    def _require(value, message):
        if not value:
            raise ValidationError(message)
