import re
from datetime import datetime, timezone

EMAIL_RE = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


def utcnow():
    """UTC sem tzinfo, no mesmo formato que já está gravado no banco.

    Substitui datetime.utcnow(), deprecated no Python 3.12.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return isinstance(email, str) and bool(EMAIL_RE.match(email))


def is_valid_color(color):
    return isinstance(color, str) and len(color) == 7 and color[0] == "#"


def parse_date(value, fmt):
    try:
        return datetime.strptime(value, fmt)
    except (TypeError, ValueError):
        return None
