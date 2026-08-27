from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from . import security
from .config import settings
from .i18n import LEVEL_NAMES, t

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _money(v):
    if v is None:
        return "—"
    return f"{v:,}".replace(",", " ")


def _date(v):
    if not isinstance(v, datetime):
        return "—"
    return v.strftime("%Y-%m-%d")


templates.env.filters["money"] = _money
templates.env.filters["date"] = _date


def render(request: Request, name: str, ctx: dict | None = None, status_code: int = 200):
    locale = security.locale_of(request)
    user = getattr(request.state, "user", None)

    def T(key, **params):
        return t(locale, key, **params)

    def TT(pair):
        return t(locale, pair[0], **pair[1])

    def level_name(n):
        names = LEVEL_NAMES.get(locale, LEVEL_NAMES["en"])
        if n is None or not (1 <= n <= len(names)):
            return "—"
        return names[n - 1]

    base = {
        "T": T,
        "TT": TT,
        "level_name": level_name,
        "locale": locale,
        "user": user,
        "settings": settings,
        "flash": request.session.pop("flash", None),
        "is_scout": security.is_scout(user),
        "can_see_exact": security.can_see_exact(user),
        "now": datetime.utcnow(),
    }
    base.update(ctx or {})
    return templates.TemplateResponse(request, name, base, status_code=status_code)
