from sqlalchemy import delete, func, select

from infra.database import transaction
from models.task import Task
from models.user import User


class UserRepository:
    def __init__(self, session):
        self.session = session

    def get(self, user_id):
        return self.session.get(User, user_id)

    def get_by_email(self, email):
        return self.session.scalars(select(User).filter_by(email=email)).first()

    def list_all(self):
        return self.session.scalars(select(User).order_by(User.id)).all()

    def count(self):
        return self.session.scalar(select(func.count()).select_from(User))

    def add(self, user):
        with transaction(self.session):
            self.session.add(user)
        return user

    def save(self, user):
        with transaction(self.session):
            pass
        return user

    def delete_with_tasks(self, user):
        """Apaga o usuário e as tasks dele numa transação só (um DELETE em massa, não um por task)."""
        with transaction(self.session):
            self.session.execute(delete(Task).where(Task.user_id == user.id))
            self.session.delete(user)
