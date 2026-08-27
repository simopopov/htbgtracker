from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models, security
from ..db import get_db
from ..render import render

router = APIRouter()


ADMIN_ROLES = {models.ROLE_HEAD_COACH, models.ROLE_MASTER_SCOUT}


def _guard_admin(request: Request, db: Session):
    user = security.get_user(request, db)
    if user is None:
        return None, RedirectResponse("/login", status_code=303)
    if user.role not in ADMIN_ROLES:
        security.flash(request, "fl_no_access")
        return user, RedirectResponse("/", status_code=303)
    return user, None


@router.get("/admin")
def admin(request: Request, db: Session = Depends(get_db)):
    user, resp = _guard_admin(request, db)
    if resp:
        return resp
    users = db.query(models.User).order_by(models.User.role, models.User.login_name).all()
    return render(request, "admin.html", {"users": users, "roles": models.ROLES})


@router.post("/admin/users")
def add_user(
    request: Request,
    ht_user_id: int = Form(...),
    login_name: str = Form(""),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    """Pre-provision a user by Hattrick ID: when they log in via OAuth for
    the first time, they keep this role instead of the trainer default."""
    user, resp = _guard_admin(request, db)
    if resp:
        return resp
    if role not in models.ROLES:
        role = models.ROLE_TRAINER
    if role == models.ROLE_HEAD_COACH and user.role != models.ROLE_HEAD_COACH:
        security.flash(request, "fl_no_access")
        return RedirectResponse("/admin", status_code=303)
    existing = db.query(models.User).filter(models.User.ht_user_id == ht_user_id).first()
    if existing is not None:
        security.flash(request, "fl_user_exists")
        return RedirectResponse("/admin", status_code=303)
    db.add(models.User(
        ht_user_id=ht_user_id,
        login_name=login_name.strip() or f"user-{ht_user_id}",
        role=role,
    ))
    db.commit()
    security.flash(request, "fl_user_added")
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/roles")
def set_role(request: Request, user_id: int = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    user, resp = _guard_admin(request, db)
    if resp:
        return resp
    target = db.get(models.User, user_id)
    if target is None or role not in models.ROLES:
        return RedirectResponse("/admin", status_code=303)
    # Only the head coach may grant or revoke the head-coach role — otherwise
    # a master scout could promote themselves or demote the селекционер.
    touches_head_coach = models.ROLE_HEAD_COACH in (role, target.role)
    if touches_head_coach and user.role != models.ROLE_HEAD_COACH:
        security.flash(request, "fl_no_access")
        return RedirectResponse("/admin", status_code=303)
    target.role = role
    db.commit()
    security.flash(request, "fl_role_saved")
    return RedirectResponse("/admin", status_code=303)
