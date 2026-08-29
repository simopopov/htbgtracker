"""Scheduled refresh endpoint, driven by Vercel Cron.

Each run syncs a small batch of the least-recently-refreshed trainer teams
and tracked players. The 24h per-object throttle in services/sync.py keeps
the CHPP fetch discipline intact no matter how often the cron fires, and all
CHPP requests stay sequential.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..chpp.errors import CHPPError
from ..config import settings
from ..db import get_db
from ..services.sync import SyncThrottled, sync_tracked_player, sync_trainer

router = APIRouter()

BATCH = 8


def _authorized(request: Request) -> bool:
    if settings.cron_secret:
        header = request.headers.get("authorization", "")
        return header == f"Bearer {settings.cron_secret}"
    # No secret configured: only allow in mock/dev mode.
    return settings.chpp_mock


def _has_token(user: models.User | None) -> bool:
    if user is None:
        return False
    if settings.chpp_mock:
        return True
    return any(t.revoked_at is None for t in user.tokens)


def _actor_for(db: Session, player: models.TrackedPlayer) -> models.User | None:
    """Whose OAuth token to use for a public playerdetails refresh: the scout
    who added the player, else any user with an active token."""
    if _has_token(player.added_by):
        return player.added_by
    if settings.chpp_mock:
        return db.query(models.User).first()
    return (
        db.query(models.User)
        .join(models.OAuthToken)
        .filter(models.OAuthToken.revoked_at.is_(None))
        .first()
    )


@router.get("/cron/sync")
def cron_sync(request: Request, db: Session = Depends(get_db)):
    if not _authorized(request):
        return JSONResponse({"error": "unauthorized"}, status_code=403)

    result = {
        "trainers_ok": 0, "trainers_skipped": 0, "trainers_failed": 0,
        "players_ok": 0, "players_skipped": 0, "players_failed": 0,
    }

    profiles = (
        db.query(models.TrainerProfile)
        .options(selectinload(models.TrainerProfile.user))
        .filter(models.TrainerProfile.is_bot.is_(False))
        .order_by(models.TrainerProfile.last_sync.asc().nullsfirst())
        .limit(BATCH)
        .all()
    )
    for profile in profiles:
        try:
            sync_trainer(db, profile.user, force=False)
            result["trainers_ok"] += 1
        except SyncThrottled:
            result["trainers_skipped"] += 1
        except CHPPError as e:
            db.rollback()
            logging.warning("cron: trainer sync failed for team %s: %s", profile.team_id, e)
            result["trainers_failed"] += 1

    players = (
        db.query(models.TrackedPlayer)
        .filter(models.TrackedPlayer.market_status.in_(["watching", "planned", "listed"]))
        .order_by(models.TrackedPlayer.last_public_sync.asc().nullsfirst())
        .limit(BATCH)
        .all()
    )
    for player in players:
        actor = _actor_for(db, player)
        if actor is None:
            result["players_failed"] += 1
            continue
        try:
            sync_tracked_player(db, player, actor, force=False)
            result["players_ok"] += 1
        except SyncThrottled:
            result["players_skipped"] += 1
        except CHPPError as e:
            db.rollback()
            logging.warning("cron: player sync failed for %s: %s", player.ht_player_id, e)
            result["players_failed"] += 1

    return result
