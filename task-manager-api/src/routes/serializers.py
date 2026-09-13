"""JSON público de cada entidade. Allowlist explícita: campo novo no model não vaza por acidente."""
from utils.helpers import format_date


def task_dict(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': str(task.created_at),
        'updated_at': str(task.updated_at),
        'due_date': format_date(task.due_date),
        'tags': task.tags.split(',') if task.tags else [],
    }


def task_with_overdue(task):
    return {**task_dict(task), 'overdue': task.is_overdue()}


def task_with_names(task):
    return {
        **task_with_overdue(task),
        'user_name': task.user.name if task.user else None,
        'category_name': task.category.name if task.category else None,
    }


def task_summary(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': format_date(task.due_date),
        'overdue': task.is_overdue(),
    }


def user_dict(user):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': str(user.created_at),
    }


def user_list_item(user, task_count):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': str(user.created_at),
        'task_count': task_count,
    }


def category_dict(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': str(category.created_at),
    }
