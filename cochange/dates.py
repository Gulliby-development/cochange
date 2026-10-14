import re
from datetime import date

_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def valid_date(text: str) -> bool:
    """Return whether text is a real Gregorian date in YYYY-MM-DD form."""
    if _DATE_PATTERN.fullmatch(text) is None:
        return False

    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True
