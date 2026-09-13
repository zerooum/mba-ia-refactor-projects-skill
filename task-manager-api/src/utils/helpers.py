import re
from datetime import datetime, timezone

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def utc_now():
    """Agora em UTC, sem tzinfo: mesmo valor e formato que o `datetime.utcnow()` deprecado gravava."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return bool(EMAIL_PATTERN.match(email))
