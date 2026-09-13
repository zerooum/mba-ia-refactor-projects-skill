from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import joinedload

from infra.database import transaction
from models.constants import CLOSED_STATUSES, DONE_STATUS
from models.task import Task


class TaskRepository:
    def __init__(self, session):
        self.session = session

    def get(self, task_id):
        return self.session.get(Task, task_id)

    def list_all(self):
        return self.session.scalars(select(Task).order_by(Task.id)).all()

    def list_with_relations(self):
        """Tasks com usuário e categoria carregados no mesmo SELECT (sem N+1)."""
        stmt = select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
        return self.session.scalars(stmt).all()

    def list_by_user(self, user_id):
        return self.session.scalars(select(Task).filter_by(user_id=user_id).order_by(Task.id)).all()

    def search(self, text=None, status=None, priority=None, user_id=None):
        stmt = select(Task)
        if text:
            stmt = stmt.where(or_(Task.title.like(f'%{text}%'), Task.description.like(f'%{text}%')))
        if status:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        return self.session.scalars(stmt.order_by(Task.id)).all()

    def count(self, **filters):
        return self.session.scalar(select(func.count()).select_from(Task).filter_by(**filters))

    def count_by_status(self):
        return dict(self.session.execute(select(Task.status, func.count()).group_by(Task.status)).all())

    def count_by_priority(self):
        return dict(self.session.execute(select(Task.priority, func.count()).group_by(Task.priority)).all())

    def count_by_category(self):
        rows = self.session.execute(select(Task.category_id, func.count()).group_by(Task.category_id))
        return dict(rows.all())

    def count_by_user(self):
        """{user_id: (total, concluídas)} numa query só."""
        done = func.sum(case((Task.status == DONE_STATUS, 1), else_=0))
        rows = self.session.execute(select(Task.user_id, func.count(), done).group_by(Task.user_id))
        return {user_id: (total, int(completed or 0)) for user_id, total, completed in rows}

    def _overdue(self, now):
        return (
            Task.due_date.is_not(None),
            Task.due_date < now,
            or_(Task.status.is_(None), Task.status.not_in(CLOSED_STATUSES)),
        )

    def list_overdue(self, now):
        return self.session.scalars(select(Task).where(*self._overdue(now)).order_by(Task.id)).all()

    def count_overdue(self, now):
        return self.session.scalar(select(func.count()).select_from(Task).where(*self._overdue(now)))

    def count_created_since(self, since):
        return self.session.scalar(select(func.count()).select_from(Task).where(Task.created_at >= since))

    def count_done_since(self, since):
        return self.session.scalar(
            select(func.count()).select_from(Task).where(Task.status == DONE_STATUS, Task.updated_at >= since)
        )

    def add(self, task):
        with transaction(self.session):
            self.session.add(task)
        return task

    def save(self, task):
        with transaction(self.session):
            pass
        return task

    def delete(self, task):
        with transaction(self.session):
            self.session.delete(task)
