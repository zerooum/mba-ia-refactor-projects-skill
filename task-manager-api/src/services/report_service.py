from datetime import timedelta

from models.constants import DONE_STATUS, HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TASK_STATUSES
from models.errors import NotFoundError
from utils.helpers import calculate_percentage, format_date, utc_now


class ReportService:
    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    def summary(self):
        now = utc_now()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = self.tasks.count_by_status()
        by_priority = self.tasks.count_by_priority()
        by_user = self.tasks.count_by_user()
        overdue = self.tasks.list_overdue(now)

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': self.tasks.count(),
                'total_users': self.users.count(),
                'total_categories': self.categories.count(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in TASK_STATUSES},
            'tasks_by_priority': {label: by_priority.get(p, 0) for p, label in PRIORITY_LABELS.items()},
            'overdue': {
                'count': len(overdue),
                'tasks': [
                    {
                        'id': t.id,
                        'title': t.title,
                        'due_date': format_date(t.due_date),
                        'days_overdue': (now - t.due_date).days,
                    }
                    for t in overdue
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': self.tasks.count_created_since(since),
                'tasks_completed_last_7_days': self.tasks.count_done_since(since),
            },
            'user_productivity': [
                self._productivity(user, *by_user.get(user.id, (0, 0))) for user in self.users.list_all()
            ],
        }

    def user_report(self, user_id):
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        now = utc_now()
        tasks = self.tasks.list_by_user(user_id)
        statistics = {status: 0 for status in TASK_STATUSES}
        for t in tasks:
            if t.status in statistics:
                statistics[t.status] += 1
        statistics.update({
            'total_tasks': len(tasks),
            'overdue': sum(1 for t in tasks if t.is_overdue(now)),
            'high_priority': sum(1 for t in tasks if t.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': calculate_percentage(statistics[DONE_STATUS], len(tasks)),
        })

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': statistics,
        }

    @staticmethod
    def _productivity(user, total, completed):
        return {
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        }
