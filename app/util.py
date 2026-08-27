from __future__ import annotations

from datetime import datetime, timedelta

# Hattrick ages: a year is 112 days; U21 eligibility ends at the player's
# 22nd birthday (wiki: "players below 22 years of age").
HT_YEAR_DAYS = 112
U21_LIMIT_DAYS = 22 * HT_YEAR_DAYS


def u21_until(age_years, age_days, as_of: datetime | None) -> datetime | None:
    """The date the player turns 22 and loses U21 eligibility.

    Computed from the age snapshot (years + days) taken at `as_of` — HT ages
    tick one day per real day, so the projection is exact.
    """
    if age_years is None or age_days is None or as_of is None:
        return None
    remaining = U21_LIMIT_DAYS - (age_years * HT_YEAR_DAYS + age_days)
    return as_of + timedelta(days=remaining)


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
