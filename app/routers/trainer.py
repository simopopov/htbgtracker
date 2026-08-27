from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from .. import models, security
from ..chpp.errors import CHPPError
from ..db import get_db
from ..render import render
from ..services import outreach
from ..services.matching import declaration_active, renew
from ..services.sync import SyncThrottled, sync_trainer
from ..util import parse_int, parse_money

router = APIRouter()


def _guard(request: Request, db: Session):
    user = security.get_user(request, db)
    if user is None:
        return None, RedirectResponse("/login", status_code=303)
    return user, None


# --- Own team ----------------------------------------------------------------

@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user, resp = _guard(request, db)
    if resp:
        return resp
    profile = user.trainer_profile
    now = datetime.utcnow()
    declarations = []
    if profile is not None:
        declarations = sorted(profile.declarations, key=lambda d: d.created_at, reverse=True)
    return render(request, "trainer_me.html", {
        "profile": profile,
        "declarations": declarations,
        "declaration_active": {d.id: declaration_active(d, now) for d in declarations},
        "training_skills": models.TRAINING_SKILLS,
        "timings": models.DECLARATION_TIMINGS,
        "default_days": models.DEFAULT_DECLARATION_DAYS,
    })


@router.post("/me/sync")
def me_sync(request: Request, db: Session = Depends(get_db)):
    user, resp = _guard(request, db)
    if resp:
        return resp
    try:
        # force=True: an explicit owner-initiated refresh of their own team,
        # like Portal's manual refresh. Automated flows keep the 24h throttle.
        sync_trainer(db, user, force=True)
        security.flash(request, "fl_synced")
    except SyncThrottled:
        security.flash(request, "fl_throttled")
    except CHPPError as e:
        security.flash(request, "fl_sync_failed", err=str(e.message or e.code))
    return RedirectResponse("/me", status_code=303)


@router.post("/me/revoke")
def me_revoke(request: Request, db: Session = Depends(get_db)):
    """Trainer disconnects: revoke tokens, purge derived data (PRODUCT.md §7)."""
    user, resp = _guard(request, db)
    if resp:
        return resp
    now = datetime.utcnow()
    for token in user.tokens:
        if token.revoked_at is None:
            token.revoked_at = now
    profile = user.trainer_profile
    if profile is not None:
        for claim in db.query(models.Claim).filter(models.Claim.trainer_profile_id == profile.id).all():
            claim.trainer_profile_id = None
        db.delete(profile)
    db.commit()
    security.flash(request, "fl_revoked")
    return RedirectResponse("/me", status_code=303)


@router.post("/me/trained/{sp_id}")
def toggle_trained(request: Request, sp_id: int, db: Session = Depends(get_db)):
    user, resp = _guard(request, db)
    if resp:
        return resp
    sp = db.get(models.SquadPlayer, sp_id)
    if sp is not None and user.trainer_profile is not None and sp.profile_id == user.trainer_profile.id:
        sp.in_trained_position = not sp.in_trained_position
        db.commit()
    return RedirectResponse("/me", status_code=303)


# --- Declarations ------------------------------------------------------------

@router.post("/declarations")
def declaration_create(
    request: Request,
    slot_type: str = Form(...),
    quality_threshold: str = Form(""),
    training_weeks: str = Form(""),
    player_to_move: str = Form(""),
    expected_sale_price: str = Form(""),
    timing: str = Form("immediate"),
    conditional_on_sale: str = Form(""),
    note: str = Form(""),
    valid_days: str = Form(""),
    db: Session = Depends(get_db),
):
    user, resp = _guard(request, db)
    if resp:
        return resp
    profile = user.trainer_profile
    if profile is None:
        security.flash(request, "fl_need_profile")
        return RedirectResponse("/me", status_code=303)
    days = parse_int(valid_days) or models.DEFAULT_DECLARATION_DAYS
    days = max(1, min(days, 112))
    threshold = parse_int(quality_threshold)
    if threshold is not None:
        threshold = max(1, min(threshold, 20))
    weeks = parse_int(training_weeks)
    if weeks is not None:
        weeks = max(1, min(weeks, 500))
    db.add(models.Declaration(
        profile_id=profile.id,
        slot_type=slot_type if slot_type in models.TRAINING_SKILLS + ["any"] else "any",
        quality_threshold=threshold,
        training_weeks=weeks,
        player_to_move=player_to_move.strip(),
        expected_sale_price=parse_money(expected_sale_price),
        timing=timing if timing in models.DECLARATION_TIMINGS else "immediate",
        conditional_on_sale=bool(conditional_on_sale),
        note=note.strip(),
        valid_until=datetime.utcnow() + timedelta(days=days),
    ))
    db.commit()
    security.flash(request, "fl_decl_created")
    return RedirectResponse("/me", status_code=303)


@router.post("/declarations/{did}/renew")
def declaration_renew(request: Request, did: int, db: Session = Depends(get_db)):
    user, resp = _guard(request, db)
    if resp:
        return resp
    decl = db.get(models.Declaration, did)
    if decl is not None and user.trainer_profile is not None and decl.profile_id == user.trainer_profile.id:
        renew(decl, datetime.utcnow())
        db.commit()
        security.flash(request, "fl_decl_renewed")
    return RedirectResponse("/me", status_code=303)


@router.post("/declarations/{did}/withdraw")
def declaration_withdraw(request: Request, did: int, db: Session = Depends(get_db)):
    user, resp = _guard(request, db)
    if resp:
        return resp
    decl = db.get(models.Declaration, did)
    if decl is not None and user.trainer_profile is not None and decl.profile_id == user.trainer_profile.id:
        decl.status = "withdrawn"
        db.commit()
        security.flash(request, "fl_decl_withdrawn")
    return RedirectResponse("/me", status_code=303)


# --- Market pipeline (what scouts plan to bring to market) -------------------

@router.get("/market")
def market(request: Request, only_mine: str = "", db: Session = Depends(get_db)):
    user, resp = _guard(request, db)
    if resp:
        return resp
    profile = user.trainer_profile
    q = (
        db.query(models.TrackedPlayer)
        .options(
            selectinload(models.TrackedPlayer.interests),
            selectinload(models.TrackedPlayer.claims).selectinload(models.Claim.scout),
        )
        .filter(models.TrackedPlayer.market_status.in_(["planned", "listed"]))
    )
    players = q.order_by(models.TrackedPlayer.expected_listing.is_(None), models.TrackedPlayer.expected_listing).all()
    rows = []
    for p in players:
        if only_mine and profile is not None and p.target_skill != profile.training_type:
            continue
        mine = None
        if profile is not None:
            mine = next((i for i in p.interests if i.profile_id == profile.id and i.status in ("open", "accepted")), None)
        claim = next((c for c in p.claims if c.status == "active"), None)
        rows.append({
            "player": p,
            "my_interest": mine,
            "claim": claim,
            "scout_compose": outreach.compose_url(claim.scout.ht_user_id) if claim else None,
            "url": outreach.player_url(p.ht_player_id),
        })
    return render(request, "market.html", {
        "rows": rows,
        "profile": profile,
        "f_only_mine": bool(only_mine),
    })


@router.post("/players/{pid}/interest")
def express_interest(
    request: Request,
    pid: int,
    note: str = Form(""),
    max_bid: str = Form(""),
    db: Session = Depends(get_db),
):
    user, resp = _guard(request, db)
    if resp:
        return resp
    profile = user.trainer_profile
    if profile is None:
        security.flash(request, "fl_need_profile")
        return RedirectResponse("/me", status_code=303)
    player = db.get(models.TrackedPlayer, pid)
    if player is None:
        return RedirectResponse("/market", status_code=303)
    existing = next(
        (i for i in player.interests if i.profile_id == profile.id and i.status in ("open", "accepted")),
        None,
    )
    if existing is not None:
        security.flash(request, "fl_interest_exists")
    else:
        db.add(models.Interest(
            player_id=player.id,
            profile_id=profile.id,
            note=note.strip(),
            max_bid=parse_money(max_bid),
        ))
        db.commit()
        security.flash(request, "fl_interest_sent")
    return RedirectResponse("/market", status_code=303)


@router.post("/interests/{iid}/withdraw")
def withdraw_interest(request: Request, iid: int, db: Session = Depends(get_db)):
    user, resp = _guard(request, db)
    if resp:
        return resp
    interest = db.get(models.Interest, iid)
    profile = user.trainer_profile
    if interest is not None and profile is not None and interest.profile_id == profile.id and interest.status == "open":
        interest.status = "withdrawn"
        interest.decided_at = datetime.utcnow()
        db.commit()
        security.flash(request, "fl_interest_withdrawn")
    return RedirectResponse("/market", status_code=303)
