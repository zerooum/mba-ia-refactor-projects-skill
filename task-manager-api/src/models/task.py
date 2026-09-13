from datetime import datetime

from infra.database import db
from models.constants import (
    CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_STATUS, DUE_DATE_FORMAT, PRIORITY_MAX, PRIORITY_MIN,
    TASK_STATUSES, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH,
)
from models.errors import ValidationError
from utils.helpers import utc_now


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    @staticmethod
    def validate_title(title):
        if not title:
            raise ValidationError('Título é obrigatório')
        if not isinstance(title, str):
            raise ValidationError('Título inválido')
        if len(title) < TITLE_MIN_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > TITLE_MAX_LENGTH:
            raise ValidationError('Título muito longo')
        return title

    @staticmethod
    def validate_status(status):
        if status not in TASK_STATUSES:
            raise ValidationError('Status inválido')
        return status

    @staticmethod
    def validate_priority(priority):
        if not isinstance(priority, (int, float)) or priority < PRIORITY_MIN or priority > PRIORITY_MAX:
            raise ValidationError('Prioridade deve ser entre 1 e 5')
        return priority

    @staticmethod
    def parse_due_date(value):
        try:
            return datetime.strptime(value, DUE_DATE_FORMAT)
        except (ValueError, TypeError):
            raise ValidationError('Formato de data inválido. Use YYYY-MM-DD') from None

    @staticmethod
    def normalize_tags(tags):
        """Lista de strings vira CSV; string e None passam como estão."""
        if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
            return ','.join(tags)
        if tags is None or isinstance(tags, str):
            return tags
        raise ValidationError('Tags inválidas')

    def is_overdue(self, now=None):
        if not self.due_date:
            return False
        return self.due_date < (now or utc_now()) and self.status not in CLOSED_STATUSES
