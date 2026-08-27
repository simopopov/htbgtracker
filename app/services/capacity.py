"""Budget banding — the privacy layer from PRODUCT.md §2.

Position scouts see bands, never raw numbers. Exact figures are for the head
coach, assistant coach and master scout only (and for the trainer themselves).
"""
from __future__ import annotations

# (upper bound exclusive or None for open-ended, i18n key)
BANDS = [
    (500_000, "band_0"),
    (2_000_000, "band_1"),
    (5_000_000, "band_2"),
    (10_000_000, "band_3"),
    (None, "band_4"),
]


def budget_band(amount: int | None) -> str:
    """Return the i18n key of the band covering `amount`."""
    if amount is None:
        return "band_unknown"
    for upper, key in BANDS:
        if upper is None or amount < upper:
            return key
    return "band_unknown"


def covers(amount: int | None, price: int | None) -> bool:
    if amount is None or price is None:
        return False
    return amount >= price
