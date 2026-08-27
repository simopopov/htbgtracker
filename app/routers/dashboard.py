from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from .. import models, security
from ..db import get_db
from ..render import render
from ..services.matching import declaration_active

router = APIRouter()


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = security.get_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)

    now = datetime.utcnow()
    profiles = (
        db.query(models.TrainerProfile)
        .options(selectinload(models.TrainerProfile.declarations))
        .all()
    )
    active_decls = [d for p in profiles if not p.is_bot for d in p.declarations if declaration_active(d, now)]
    players = db.query(models.TrackedPlayer).all()
    pipeline = [p for p in players if p.market_status in ("planned", "listed")]

    ctx = {
        "n_trainers": sum(1 for p in profiles if not p.is_bot),
        "n_slots": len(active_decls),
        "n_players": len(players),
        "n_pipeline": len(pipeline),
        "my_claims": [],
        "open_interests": [],
        "my_declarations": [],
        "my_interests": [],
    }

    if security.is_scout(user):
        ctx["my_claims"] = (
            db.query(models.Claim)
            .options(selectinload(models.Claim.player))
            .filter(models.Claim.scout_id == user.id, models.Claim.status == "active")
            .all()
        )
        ctx["open_interests"] = (
            db.query(models.Interest)
            .options(
                selectinload(models.Interest.player),
                selectinload(models.Interest.profile).selectinload(models.TrainerProfile.user),
            )
            .filter(models.Interest.status == "open")
            .order_by(models.Interest.created_at.desc())
            .all()
        )

    profile = user.trainer_profile
    if profile is not None:
        soon = now + timedelta(days=7)
        ctx["my_declarations"] = [
            {"d": d, "active": declaration_active(d, now), "expiring": declaration_active(d, now) and d.valid_until <= soon}
            for d in sorted(profile.declarations, key=lambda d: d.valid_until, reverse=True)
        ]
        ctx["my_interests"] = (
            db.query(models.Interest)
            .options(selectinload(models.Interest.player))
            .filter(models.Interest.profile_id == profile.id)
            .order_by(models.Interest.created_at.desc())
            .all()
        )

    return render(request, "dashboard.html", ctx)
