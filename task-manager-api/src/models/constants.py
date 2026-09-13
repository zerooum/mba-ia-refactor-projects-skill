"""Constantes de domínio. Tuplas (não sets) para `in` funcionar com valor não-hashable vindo do JSON."""

TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
DEFAULT_STATUS = 'pending'
DONE_STATUS = 'done'
CLOSED_STATUSES = ('done', 'cancelled')  # task fechada nunca conta como atrasada

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2  # prioridade <= 2 conta como "alta" nos relatórios
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
DUE_DATE_FORMAT = '%Y-%m-%d'

USER_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
ADMIN_ROLE = 'admin'
PASSWORD_MIN_LENGTH = 4

DEFAULT_COLOR = '#000000'

RECENT_ACTIVITY_DAYS = 7
