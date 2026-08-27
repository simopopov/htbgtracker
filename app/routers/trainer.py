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
from ..services.matching import declaration_active, plan_skills, renew
from ..services.sync import (
    SyncThrottled,
    TeamChoiceRequired,
    fetch_user_teams,
    sync_trainer,
)
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
        "player_skills": models.PLAYER_SKILLS,
        "specialty_ids": models.SPECIALTY_IDS,
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
    except TeamChoiceRequired:
        security.flash(request, "fl_choose_team")
        return RedirectResponse("/me/teams", status_code=303)
    except SyncThrottled:
        security.flash(request, "fl_throttled")
    except CHPPError as e:
        security.flash(request, "fl_sync_failed", err=str(e.message or e.code))
    return RedirectResponse("/me", status_code=303)


def _purge_profile(db: Session, profile: models.TrainerProfile) -> None:
    """Remove a connected team: null claim references, drop the profile
    (cascades squad, declarations and interests — they belong to that team)."""
    for claim in db.query(models.Claim).filter(models.Claim.trainer_profile_id == profile.id).all():
        claim.trainer_profile_id = None
    user = profile.user
    user.trainer_profile = None
    db.delete(profile)
    db.flush()


@router.get("/me/teams")
def my_teams(request: Request, db: Session = Depends(get_db)):
    user, resp = _guard(request, db)
    if resp:
        return resp
    try:
        teams = fetch_user_teams(db, user)
    except CHPPError as e:
        security.flash(request, "fl_sync_failed", err=str(e.message or e.code))
        return RedirectResponse("/me", status_code=303)
    current = user.trainer_profile.team_id if user.trainer_profile else None
    return render(request, "teams_choice.html", {
        "teams": teams,
        "current_team_id": current,
    })


@router.post("/me/team")
def choose_team(request: Request, team_id: int = Form(...), db: Session = Depends(get_db)):
    user, resp = _guard(request, db)
    if resp:
        return resp
    profile = user.trainer_profile
    if profile is not None and profile.team_id == team_id:
        return RedirectResponse("/me", status_code=303)
    if profile is not None:
        _purge_profile(db, profile)
    try:
        sync_trainer(db, user, force=True, team_id=team_id)
        security.flash(request, "fl_synced")
    except CHPPError as e:
        db.rollback()
        security.flash(request, "fl_sync_failed", err=str(e.message or e.code))
        return RedirectResponse("/me/teams", status_code=303)
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

def _clamp(value, low, high):
    return None if value is None else max(low, min(value, high))


@router.post("/declarations")
async def declaration_create(request: Request, db: Session = Depends(get_db)):
    user, resp = _guard(request, db)
    if resp:
        return resp
    profile = user.trainer_profile
    if profile is None:
        security.flash(request, "fl_need_profile")
        return RedirectResponse("/me", status_code=303)

    form = await request.form()
    slot_type = form.get("slot_type", "any")
    timing = form.get("timing", "immediate")
    days = parse_int(form.get("valid_days")) or models.DEFAULT_DECLARATION_DAYS

    # Optional per-skill requirements: req_min_<skill> / req_max_<skill>.
    skill_reqs = {}
    for skill in models.PLAYER_SKILLS:
        lo = _clamp(parse_int(form.get(f"req_min_{skill}")), 1, 20)
        hi = _clamp(parse_int(form.get(f"req_max_{skill}")), 1, 20)
        if lo is not None or hi is not None:
            skill_reqs[skill] = {"min": lo, "max": hi}

    specialty = parse_int(form.get("specialty"))
    if specialty not in models.SPECIALTY_IDS:
        specialty = None

    db.add(models.Declaration(
        profile_id=profile.id,
        slot_type=slot_type if slot_type in models.TRAINING_SKILLS + ["any"] else "any",
        training_weeks=_clamp(parse_int(form.get("training_weeks")), 1, 500),
        timing=timing if timing in models.DECLARATION_TIMINGS else "immediate",
        max_price=parse_money(form.get("max_price")),
        min_age=_clamp(parse_int(form.get("min_age")), 15, 45),
        max_age=_clamp(parse_int(form.get("max_age")), 15, 45),
        specialty_id=specialty,
        skill_reqs=skill_reqs or None,
        note=(form.get("note") or "").strip(),
        valid_until=datetime.utcnow() + timedelta(days=max(1, min(days, 112))),
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
        skills = plan_skills(p)
        if only_mine and profile is not None and profile.training_type not in skills:
            continue
        mine = None
        if profile is not None:
            mine = next((i for i in p.interests if i.profile_id == profile.id and i.status in ("open", "accepted")), None)
        claim = next((c for c in p.claims if c.status == "active"), None)
        rows.append({
            "player": p,
            "skills": skills,
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
