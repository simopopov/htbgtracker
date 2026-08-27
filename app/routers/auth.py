from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models, security
from ..chpp import client as chpp_client
from ..chpp.parse import parse_teamdetails
from ..config import settings
from ..db import get_db
from ..render import render

router = APIRouter()


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    security.get_user(request, db)
    personas = []
    if settings.chpp_mock:
        personas = db.query(models.User).order_by(models.User.role, models.User.login_name).all()
    return render(request, "login.html", {
        "personas": personas,
        "oauth_ready": bool(settings.chpp_consumer_key) and not settings.chpp_mock,
    })


@router.post("/auth/mock")
def mock_login(request: Request, ht_user_id: int = Form(...), db: Session = Depends(get_db)):
    if not settings.chpp_mock:
        raise HTTPException(status_code=404)
    user = db.query(models.User).filter(models.User.ht_user_id == ht_user_id).first()
    if user is None:
        security.flash(request, "fl_unknown_persona")
        return RedirectResponse("/login", status_code=303)
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/lang/{code}")
def set_lang(request: Request, code: str):
    if code in ("en", "bg"):
        request.session["locale"] = code
    target = request.headers.get("referer") or "/"
    return RedirectResponse(target, status_code=303)


@router.get("/auth/chpp/start")
def chpp_start(request: Request):
    if settings.chpp_mock or not settings.chpp_consumer_key:
        security.flash(request, "fl_oauth_unavailable")
        return RedirectResponse("/login", status_code=303)
    tokens = chpp_client.oauth_request_token(f"{settings.base_url}/auth/chpp/callback")
    request.session["rt"] = tokens["oauth_token"]
    request.session["rts"] = tokens["oauth_token_secret"]
    return RedirectResponse(chpp_client.oauth_authorize_url(tokens["oauth_token"]), status_code=303)


@router.get("/auth/chpp/callback")
def chpp_callback(request: Request, oauth_token: str = "", oauth_verifier: str = "", db: Session = Depends(get_db)):
    rt = request.session.pop("rt", None)
    rts = request.session.pop("rts", None)
    if not rt or not oauth_verifier:
        security.flash(request, "fl_oauth_unavailable")
        return RedirectResponse("/login", status_code=303)
    access = chpp_client.oauth_access_token(rt, rts, oauth_verifier)

    chpp = chpp_client.get_client(access["oauth_token"], access["oauth_token_secret"])
    td = parse_teamdetails(chpp.fetch("teamdetails", "3.9"))
    ht_user_id = td["user"]["ht_user_id"]
    login_name = td["user"]["login_name"] or f"user-{ht_user_id}"

    user = db.query(models.User).filter(models.User.ht_user_id == ht_user_id).first()
    if user is None:
        # Bootstrap: the very first user of a fresh database becomes head
        # coach — otherwise nobody could ever reach /admin to assign roles.
        # Everyone after that starts as a trainer; the head coach and master
        # scouts promote people from /admin.
        first_user = db.query(models.User).first() is None
        role = models.ROLE_HEAD_COACH if first_user else models.ROLE_TRAINER
        user = models.User(ht_user_id=ht_user_id, login_name=login_name, role=role)
        db.add(user)
        db.flush()
    else:
        user.login_name = login_name

    db.add(models.OAuthToken(
        user_id=user.id,
        token=access["oauth_token"],
        token_secret=access["oauth_token_secret"],
    ))
    db.commit()
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)
