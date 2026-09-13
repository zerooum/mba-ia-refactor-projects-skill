import logging

from models.constants import DEFAULT_PRIORITY, DEFAULT_STATUS, TASK_STATUSES
from models.errors import NotFoundError, ValidationError
from models.task import Task
from utils.helpers import calculate_percentage, utc_now

log = logging.getLogger(__name__)

# tipos que o lookup por chave primária aceita sem estourar ("abc" continua dando 404)
ID_TYPES = (int, float, str)


class TaskService:
    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    def list_tasks(self):
        return self.tasks.list_with_relations()

    def get_task(self, task_id):
        task = self.tasks.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    def search(self, text=None, status=None, priority=None, user_id=None):
        return self.tasks.search(text=text, status=status, priority=priority, user_id=user_id)

    def create_task(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        title = Task.validate_title(data.get('title'))
        status = Task.validate_status(data.get('status', DEFAULT_STATUS))
        priority = Task.validate_priority(data.get('priority', DEFAULT_PRIORITY))
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        self._ensure_user(user_id)
        self._ensure_category(category_id)

        task = Task(
            title=title,
            description=data.get('description', ''),
            status=status,
            priority=priority,
            user_id=user_id,
            category_id=category_id,
        )
        if data.get('due_date'):
            task.due_date = Task.parse_due_date(data['due_date'])
        if data.get('tags'):
            task.tags = Task.normalize_tags(data['tags'])

        self.tasks.add(task)
        log.info('Task criada: %s - %s', task.id, task.title)
        return task

    def update_task(self, task_id, data):
        task = self.get_task(task_id)
        if not data:
            raise ValidationError('Dados inválidos')

        changes = {}
        if 'title' in data:
            changes['title'] = Task.validate_title(data['title'])
        if 'description' in data:
            changes['description'] = data['description']
        if 'status' in data:
            changes['status'] = Task.validate_status(data['status'])
        if 'priority' in data:
            changes['priority'] = Task.validate_priority(data['priority'])
        if 'user_id' in data:
            self._ensure_user(data['user_id'])
            changes['user_id'] = data['user_id']
        if 'category_id' in data:
            self._ensure_category(data['category_id'])
            changes['category_id'] = data['category_id']
        if 'due_date' in data:
            changes['due_date'] = Task.parse_due_date(data['due_date']) if data['due_date'] else None
        if 'tags' in data:
            changes['tags'] = Task.normalize_tags(data['tags'])

        for field, value in changes.items():
            setattr(task, field, value)
        # explícito: onupdate só dispara se alguma coluna mudar de valor
        task.updated_at = utc_now()

        self.tasks.save(task)
        log.info('Task atualizada: %s', task.id)
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        self.tasks.delete(task)
        log.info('Task deletada: %s', task_id)

    def stats(self):
        total = self.tasks.count()
        by_status = self.tasks.count_by_status()
        stats = {status: by_status.get(status, 0) for status in TASK_STATUSES}
        stats['total'] = total
        stats['overdue'] = self.tasks.count_overdue(utc_now())
        stats['completion_rate'] = calculate_percentage(stats['done'], total)
        return stats

    def _ensure_user(self, user_id):
        if not user_id:
            return
        if not isinstance(user_id, ID_TYPES):
            raise ValidationError('Usuário inválido')
        if not self.users.get(user_id):
            raise NotFoundError('Usuário não encontrado')

    def _ensure_category(self, category_id):
        if not category_id:
            return
        if not isinstance(category_id, ID_TYPES):
            raise ValidationError('Categoria inválida')
        if not self.categories.get(category_id):
            raise NotFoundError('Categoria não encontrada')
