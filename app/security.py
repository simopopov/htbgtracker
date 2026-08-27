from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from . import models
from .i18n import t

SCOUT_ROLES = {
    models.ROLE_HEAD_COACH,
    models.ROLE_ASSISTANT_COACH,
    models.ROLE_MASTER_SCOUT,
    models.ROLE_POSITION_SCOUT,
}
# Exact finances: head coach + master scout per PRODUCT.md §2 (assistant coach
# has full visibility except admin settings, so exact figures included).
EXACT_FINANCE_ROLES = {
    models.ROLE_HEAD_COACH,
    models.ROLE_ASSISTANT_COACH,
    models.ROLE_MASTER_SCOUT,
}


def get_user(request: Request, db: Session) -> models.User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        request.state.user = None
        return None
    user = db.get(models.User, user_id)
    request.state.user = user
    return user


def is_scout(user: models.User | None) -> bool:
    return user is not None and user.role in SCOUT_ROLES


def can_see_exact(user: models.User | None) -> bool:
    return user is not None and user.role in EXACT_FINANCE_ROLES


def locale_of(request: Request) -> str:
    return request.session.get("locale", "en")


def flash(request: Request, key: str, **params) -> None:
    request.session["flash"] = t(locale_of(request), key, **params)
