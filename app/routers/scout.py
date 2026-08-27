from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from .. import models, security
from ..chpp.errors import CHPPError
from ..i18n import t
from ..db import get_db
from ..render import render
from ..services import outreach
from ..services.capacity import budget_band
from ..services.matching import declaration_active, rank_trainers
from ..services.sync import SyncThrottled, sync_tracked_player
from ..util import parse_date, parse_int, parse_money, u21_until

router = APIRouter()


def _guard_scout(request: Request, db: Session):
    user = security.get_user(request, db)
    if user is None:
        return None, RedirectResponse("/login", status_code=303)
    if not security.is_scout(user):
        security.flash(request, "fl_no_access")
        return user, RedirectResponse("/", status_code=303)
    return user, None


def _clamp(value, low, high):
    return None if value is None else max(low, min(value, high))


def _skills_from_form(raw: dict[str, str]) -> dict | None:
    """Build the {skill: 1–20} dict from the per-skill form fields."""
    skills = {}
    for skill, value in raw.items():
        parsed = _clamp(parse_int(value), 1, 20)
        if parsed is not None:
            skills[skill] = parsed
    return skills or None


def _profiles(db: Session) -> list[models.TrainerProfile]:
    return (
        db.query(models.TrainerProfile)
        .options(selectinload(models.TrainerProfile.declarations), selectinload(models.TrainerProfile.user))
        .all()
    )


# --- Capacity registry -------------------------------------------------------

# Fixed thresholds aligned with the budget bands, so the filter leaks no
# more than the banded display position scouts already see.
BUDGET_THRESHOLDS = [500_000, 2_000_000, 5_000_000, 10_000_000]


@router.get("/trainers")
def trainers_list(
    request: Request,
    training_type: str = "",
    only_free: str = "",
    include_stale: str = "",
    min_budget: str = "",
    slot_skill: str = "",
    slot_timing: str = "",
    db: Session = Depends(get_db),
):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    now = datetime.utcnow()
    threshold = parse_int(min_budget)
    if threshold not in BUDGET_THRESHOLDS:
        threshold = None
    if slot_skill not in models.TRAINING_SKILLS:
        slot_skill = ""
    if slot_timing not in models.DECLARATION_TIMINGS:
        slot_timing = ""
    rows = []
    for profile in _profiles(db):
        active = [d for d in profile.declarations if declaration_active(d, now)]
        # Declaration filters narrow both the row set and the shown slots:
        # a declaration for "any" skill matches every skill filter.
        shown = active
        if slot_skill:
            shown = [d for d in shown if d.slot_type in (slot_skill, "any")]
        if slot_timing:
            shown = [d for d in shown if d.timing == slot_timing]
        stale = profile.is_bot or (
            profile.ht_last_login is not None and (now - profile.ht_last_login).days > 45
        )
        if not include_stale and stale:
            continue
        if training_type and profile.training_type != training_type:
            continue
        if only_free and not active:
            continue
        if (slot_skill or slot_timing) and not shown:
            continue
        if threshold is not None:
            budget = profile.expected_cash if profile.expected_cash is not None else profile.cash
            if budget is None or budget < threshold:
                continue
        rows.append({
            "profile": profile,
            "active": shown,
            "band": budget_band(profile.expected_cash if profile.expected_cash is not None else profile.cash),
            "trained": sum(1 for p in profile.squad if p.in_trained_position),
            "squad_size": len(profile.squad),
            "stale": stale,
            "compose": outreach.compose_url(profile.user.ht_user_id),
        })
    rows.sort(key=lambda r: (-len(r["active"]), -(r["profile"].expected_cash or 0)))
    return render(request, "trainers_list.html", {
        "rows": rows,
        "f_training_type": training_type,
        "f_only_free": bool(only_free),
        "f_include_stale": bool(include_stale),
        "f_min_budget": threshold,
        "f_slot_skill": slot_skill,
        "f_slot_timing": slot_timing,
        "budget_thresholds": BUDGET_THRESHOLDS,
        "training_skills": models.TRAINING_SKILLS,
        "timings": models.DECLARATION_TIMINGS,
    })


# --- Player registry ---------------------------------------------------------

@router.get("/players")
def players_list(
    request: Request,
    status: str = "",
    squad: str = "",
    skill: str = "",
    db: Session = Depends(get_db),
):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    q = db.query(models.TrackedPlayer).options(
        selectinload(models.TrackedPlayer.claims).selectinload(models.Claim.scout),
        selectinload(models.TrackedPlayer.interests),
    )
    if status:
        q = q.filter(models.TrackedPlayer.market_status == status)
    if squad:
        q = q.filter(models.TrackedPlayer.squad == squad)
    if skill:
        q = q.filter(models.TrackedPlayer.target_skill == skill)
    players = q.order_by(models.TrackedPlayer.created_at.desc()).all()
    now = datetime.utcnow()
    rows = []
    for p in players:
        claim = next((c for c in p.claims if c.status == "active"), None)
        until = u21_until(p.age_years, p.age_days, p.last_public_sync or p.created_at)
        rows.append({
            "player": p,
            "claim": claim,
            "open_interests": sum(1 for i in p.interests if i.status == "open"),
            "u21_until": until,
            "u21_weeks": max(0, (until - now).days // 7) if until else None,
        })
    return render(request, "players_list.html", {
        "rows": rows,
        "f_status": status,
        "f_squad": squad,
        "f_skill": skill,
        "training_skills": models.TRAINING_SKILLS,
        "market_statuses": models.MARKET_STATUSES,
        "nt_squads": models.NT_SQUADS,
    })


@router.get("/players/new")
def player_new_form(request: Request, db: Session = Depends(get_db)):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    return render(request, "player_new.html", {
        "training_skills": models.TRAINING_SKILLS,
        "market_statuses": models.MARKET_STATUSES,
        "nt_squads": models.NT_SQUADS,
        "player_skills": models.PLAYER_SKILLS,
        "specialty_ids": models.SPECIALTY_IDS,
    })


@router.post("/players/new")
def player_new(
    request: Request,
    ht_player_id: int = Form(...),
    name: str = Form(""),
    squad: str = Form("u21"),
    target_skill: str = Form(...),
    estimated_price: str = Form(""),
    market_status: str = Form("watching"),
    expected_listing: str = Form(""),
    notes: str = Form(""),
    age_years: str = Form(""),
    age_days: str = Form(""),
    specialty: str = Form(""),
    sk_goalkeeping: str = Form(""),
    sk_defending: str = Form(""),
    sk_playmaking: str = Form(""),
    sk_winger: str = Form(""),
    sk_passing: str = Form(""),
    sk_scoring: str = Form(""),
    sk_set_pieces: str = Form(""),
    sk_stamina: str = Form(""),
    db: Session = Depends(get_db),
):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    existing = db.query(models.TrackedPlayer).filter(models.TrackedPlayer.ht_player_id == ht_player_id).first()
    if existing:
        security.flash(request, "fl_player_exists")
        return RedirectResponse(f"/players/{existing.id}", status_code=303)
    if target_skill not in models.TRAINING_SKILLS:
        target_skill = models.TRAINING_SKILLS[0]
    player = models.TrackedPlayer(
        ht_player_id=ht_player_id,
        name=name.strip(),
        squad=squad if squad in models.NT_SQUADS else "u21",
        target_skill=target_skill,
        estimated_price=parse_money(estimated_price),
        market_status=market_status if market_status in models.MARKET_STATUSES else "watching",
        expected_listing=parse_date(expected_listing),
        notes=notes.strip(),
        added_by_id=user.id,
        age_years=_clamp(parse_int(age_years), 15, 45),
        age_days=_clamp(parse_int(age_days), 0, 111),
        specialty_id=parse_int(specialty),
        skills=_skills_from_form({
            "goalkeeping": sk_goalkeeping, "defending": sk_defending,
            "playmaking": sk_playmaking, "winger": sk_winger,
            "passing": sk_passing, "scoring": sk_scoring,
            "set_pieces": sk_set_pieces, "stamina": sk_stamina,
        }),
    )
    db.add(player)
    db.commit()
    try:
        sync_tracked_player(db, player, user, force=True)
        security.flash(request, "fl_player_added")
    except CHPPError:
        security.flash(request, "fl_public_sync_failed")
    return RedirectResponse(f"/players/{player.id}", status_code=303)


@router.get("/players/{pid}")
def player_detail(request: Request, pid: int, db: Session = Depends(get_db)):
    user = security.get_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    player = db.get(models.TrackedPlayer, pid)
    if player is None:
        security.flash(request, "fl_not_found")
        return RedirectResponse("/", status_code=303)

    now = datetime.utcnow()
    claim = next((c for c in player.claims if c.status == "active"), None)
    interests = sorted(player.interests, key=lambda i: i.created_at, reverse=True)
    locale = security.locale_of(request)
    until = u21_until(player.age_years, player.age_days, player.last_public_sync or player.created_at)

    ctx = {
        "player": player,
        "claim": claim,
        "interests": interests,
        "hattrick_url": outreach.player_url(player.ht_player_id),
        "training_skills": models.TRAINING_SKILLS,
        "market_statuses": models.MARKET_STATUSES,
        "player_skills": models.PLAYER_SKILLS,
        "specialty_ids": models.SPECIALTY_IDS,
        "u21_until": until,
        "u21_weeks": max(0, (until - now).days // 7) if until else None,
        "u21_expired": bool(until and until <= now),
        "matches": [],
        "my_interest": None,
        "scout_compose": None,
    }

    def _comment_row(c):
        # Every non-trainer role gets the HT-mail button, own comments
        # included — simpler than a self-exclusion nobody asked for.
        mail = None
        if security.is_scout(user):
            mail = {
                "compose": outreach.compose_url(c.author.ht_user_id),
                "subject": player.name or f"#{player.ht_player_id}",
                "body": outreach.comment_mail_body(locale, player, c),
            }
        return {"c": c, "mail": mail}

    ctx["comments_ctx"] = [
        {**_comment_row(c), "replies": [_comment_row(r) for r in c.replies]}
        for c in player.comments
        if c.parent_id is None
    ]

    def _localize_params(pairs):
        out = []
        for key, params in pairs:
            if "skill" in params:
                params = {**params, "skill": t(locale, f"skill_{params['skill']}")}
            if key == "warn_req_price" and "limit" in params:
                params = {**params, "limit": f"{params['limit']:,}".replace(",", " ")}
            out.append((key, params))
        return out

    if security.is_scout(user):
        bundles = [(p.user, p, p.declarations) for p in _profiles(db)]
        matches = rank_trainers(player, bundles, now)[:6]
        for m in matches:
            m.reasons = _localize_params(m.reasons)
            m.warnings = _localize_params(m.warnings)
        ctx["matches"] = [
            {
                "m": m,
                "band": budget_band(m.profile.expected_cash if m.profile.expected_cash is not None else m.profile.cash),
                "compose": outreach.compose_url(m.user.ht_user_id),
                "subject": outreach.draft_subject(locale, player),
                "draft": outreach.draft_message(locale, player, m.user, user),
            }
            for m in matches
        ]
    else:
        profile = user.trainer_profile
        if profile is not None:
            ctx["my_interest"] = next(
                (i for i in interests if i.profile_id == profile.id and i.status in ("open", "accepted")),
                None,
            )
        if claim is not None:
            ctx["scout_compose"] = outreach.compose_url(claim.scout.ht_user_id)

    return render(request, "player_detail.html", ctx)


@router.post("/players/{pid}/sync")
def player_sync(request: Request, pid: int, db: Session = Depends(get_db)):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    player = db.get(models.TrackedPlayer, pid)
    if player is None:
        return RedirectResponse("/players", status_code=303)
    try:
        sync_tracked_player(db, player, user)
        security.flash(request, "fl_public_synced")
    except SyncThrottled:
        security.flash(request, "fl_throttled")
    except CHPPError:
        security.flash(request, "fl_public_sync_failed")
    return RedirectResponse(f"/players/{pid}", status_code=303)


@router.post("/players/{pid}/status")
def player_status(
    request: Request,
    pid: int,
    market_status: str = Form(...),
    estimated_price: str = Form(""),
    expected_listing: str = Form(""),
    notes: str = Form(""),
    age_years: str = Form(""),
    age_days: str = Form(""),
    specialty: str = Form(""),
    sk_goalkeeping: str = Form(""),
    sk_defending: str = Form(""),
    sk_playmaking: str = Form(""),
    sk_winger: str = Form(""),
    sk_passing: str = Form(""),
    sk_scoring: str = Form(""),
    sk_set_pieces: str = Form(""),
    sk_stamina: str = Form(""),
    db: Session = Depends(get_db),
):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    player = db.get(models.TrackedPlayer, pid)
    if player is None:
        return RedirectResponse("/players", status_code=303)
    _apply_market_status(player, market_status)
    player.estimated_price = parse_money(estimated_price)
    player.expected_listing = parse_date(expected_listing)
    player.notes = notes.strip()
    player.age_years = _clamp(parse_int(age_years), 15, 45)
    player.age_days = _clamp(parse_int(age_days), 0, 111)
    player.specialty_id = parse_int(specialty)
    player.skills = _skills_from_form({
        "goalkeeping": sk_goalkeeping, "defending": sk_defending,
        "playmaking": sk_playmaking, "winger": sk_winger,
        "passing": sk_passing, "scoring": sk_scoring,
        "set_pieces": sk_set_pieces, "stamina": sk_stamina,
    })
    db.commit()
    security.flash(request, "fl_saved")
    return RedirectResponse(f"/players/{pid}", status_code=303)


# --- Training plan -----------------------------------------------------------

@router.post("/players/{pid}/plan")
def plan_add(
    request: Request,
    pid: int,
    skill: str = Form(...),
    weeks: str = Form(""),
    stamina_share: str = Form(""),
    db: Session = Depends(get_db),
):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    player = db.get(models.TrackedPlayer, pid)
    if player is None:
        return RedirectResponse("/players", status_code=303)
    if skill not in models.TRAINING_SKILLS:
        skill = player.target_skill
    db.add(models.TrainingPlanStep(
        player_id=player.id,
        position=len(player.plan_steps) + 1,
        skill=skill,
        weeks=_clamp(parse_int(weeks), 1, 112),
        stamina_share=_clamp(parse_int(stamina_share), 0, 100),
    ))
    db.commit()
    security.flash(request, "fl_saved")
    return RedirectResponse(f"/players/{pid}", status_code=303)


@router.post("/plan/{sid}/delete")
def plan_delete(request: Request, sid: int, db: Session = Depends(get_db)):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    step = db.get(models.TrainingPlanStep, sid)
    if step is None:
        return RedirectResponse("/players", status_code=303)
    pid = step.player_id
    db.delete(step)
    db.commit()
    security.flash(request, "fl_saved")
    return RedirectResponse(f"/players/{pid}", status_code=303)


def _apply_market_status(player: models.TrackedPlayer, status: str) -> None:
    if status not in models.MARKET_STATUSES:
        return
    player.market_status = status
    # A sold player is a closed case: complete the active claim.
    if status == "transferred":
        for claim in player.claims:
            if claim.status == "active":
                claim.status = "completed"
                claim.released_at = datetime.utcnow()


@router.post("/players/{pid}/quickstatus")
def player_quickstatus(
    request: Request,
    pid: int,
    market_status: str = Form(...),
    db: Session = Depends(get_db),
):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    player = db.get(models.TrackedPlayer, pid)
    if player is not None:
        _apply_market_status(player, market_status)
        db.commit()
        security.flash(request, "fl_saved")
    return RedirectResponse("/players", status_code=303)


@router.post("/players/{pid}/delete")
def player_delete(request: Request, pid: int, db: Session = Depends(get_db)):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    player = db.get(models.TrackedPlayer, pid)
    if player is None:
        return RedirectResponse("/players", status_code=303)
    privileged = user.role in (models.ROLE_HEAD_COACH, models.ROLE_MASTER_SCOUT)
    if not privileged and player.added_by_id != user.id:
        security.flash(request, "fl_no_access")
        return RedirectResponse("/players", status_code=303)
    db.delete(player)  # cascades claims, interests and plan steps
    db.commit()
    security.flash(request, "fl_player_deleted")
    return RedirectResponse("/players", status_code=303)


# --- Comments ----------------------------------------------------------------

@router.post("/players/{pid}/comments")
def comment_add(
    request: Request,
    pid: int,
    body: str = Form(...),
    parent_id: str = Form(""),
    db: Session = Depends(get_db),
):
    user = security.get_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    player = db.get(models.TrackedPlayer, pid)
    if player is None or not body.strip():
        return RedirectResponse(f"/players/{pid}#comments", status_code=303)
    parent = None
    pid_int = parse_int(parent_id)
    if pid_int is not None:
        parent = db.get(models.Comment, pid_int)
        if parent is None or parent.player_id != player.id:
            parent = None
        elif parent.parent_id is not None:
            # Keep the thread one level deep: a reply to a reply attaches
            # to the top-level comment.
            parent = db.get(models.Comment, parent.parent_id)
    db.add(models.Comment(
        player_id=player.id,
        author_id=user.id,
        parent_id=parent.id if parent is not None else None,
        body=body.strip(),
    ))
    db.commit()
    return RedirectResponse(f"/players/{pid}#comments", status_code=303)


@router.post("/comments/{cid}/delete")
def comment_delete(request: Request, cid: int, db: Session = Depends(get_db)):
    user = security.get_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    comment = db.get(models.Comment, cid)
    if comment is None:
        return RedirectResponse("/players", status_code=303)
    player_id = comment.player_id
    privileged = user.role in (models.ROLE_HEAD_COACH, models.ROLE_MASTER_SCOUT)
    if comment.author_id == user.id or privileged:
        db.delete(comment)  # cascades replies
        db.commit()
    return RedirectResponse(f"/players/{player_id}#comments", status_code=303)


# --- Claims ------------------------------------------------------------------

@router.post("/players/{pid}/claim")
def claim_player(request: Request, pid: int, db: Session = Depends(get_db)):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    player = db.get(models.TrackedPlayer, pid)
    if player is None:
        return RedirectResponse("/players", status_code=303)
    active = next((c for c in player.claims if c.status == "active"), None)
    if active is not None:
        security.flash(request, "fl_claim_exists")
    else:
        db.add(models.Claim(player_id=player.id, scout_id=user.id))
        db.commit()
        security.flash(request, "fl_claimed")
    return RedirectResponse(f"/players/{pid}", status_code=303)


@router.post("/players/{pid}/release")
def release_claim(request: Request, pid: int, db: Session = Depends(get_db)):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    player = db.get(models.TrackedPlayer, pid)
    if player is None:
        return RedirectResponse("/players", status_code=303)
    claim = next((c for c in player.claims if c.status == "active"), None)
    privileged = user.role in (models.ROLE_HEAD_COACH, models.ROLE_MASTER_SCOUT)
    if claim is not None and (claim.scout_id == user.id or privileged):
        claim.status = "released"
        claim.released_at = datetime.utcnow()
        db.commit()
        security.flash(request, "fl_released")
    return RedirectResponse(f"/players/{pid}", status_code=303)


# --- Interest decisions (scout side) ----------------------------------------

@router.post("/interests/{iid}/decision")
def interest_decision(request: Request, iid: int, action: str = Form(...), db: Session = Depends(get_db)):
    user, resp = _guard_scout(request, db)
    if resp:
        return resp
    interest = db.get(models.Interest, iid)
    if interest is None or interest.status != "open":
        return RedirectResponse("/players", status_code=303)
    if action == "accept":
        interest.status = "accepted"
        claim = next((c for c in interest.player.claims if c.status == "active"), None)
        if claim is not None:
            claim.trainer_profile_id = interest.profile_id
    elif action == "decline":
        interest.status = "declined"
    interest.decided_at = datetime.utcnow()
    db.commit()
    security.flash(request, "fl_interest_decided")
    return RedirectResponse(f"/players/{interest.player_id}", status_code=303)
