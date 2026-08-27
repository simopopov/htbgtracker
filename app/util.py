from __future__ import annotations

from datetime import datetime


def parse_money(raw: str | None) -> int | None:
    if not raw:
        return None
    cleaned = raw.replace(" ", "").replace(",", "").replace("_", "")
    try:
        value = int(cleaned)
    except ValueError:
        return None
    return value if value >= 0 else None


def parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d")
    except ValueError:
        return None


def parse_int(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None
