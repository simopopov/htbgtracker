"""CHPP sync with fetch discipline: sequential requests, at most one refresh
per object per 24h (CHPP_TECHNICAL.md §7 / Hattrick Portal precedent)."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models
from ..chpp import client as chpp_client
from ..chpp.constants import TRAINING_TYPE_TO_SKILL
from ..chpp.errors import CHPPError
from ..chpp.parse import (
    parse_economy,
    parse_playerdetails,
    parse_players,
    parse_teamdetails,
    parse_training,
    parse_worlddetails,
)
from ..config import settings

REFRESH_MIN_HOURS = 24
CURRENCY_MAX_AGE_DAYS = 7


class SyncThrottled(Exception):
    pass


class TeamChoiceRequired(Exception):
    """The user manages several teams and has not chosen one yet."""

    def __init__(self, teams: list[dict]):
        self.teams = teams
        super().__init__("team choice required")


def _can_refresh(db: Session, obj_type: str, obj_id: int, now: datetime) -> bool:
    cutoff = now - timedelta(hours=REFRESH_MIN_HOURS)
    recent = (
        db.query(models.SyncLog)
        .filter(
            models.SyncLog.obj_type == obj_type,
            models.SyncLog.obj_id == obj_id,
            models.SyncLog.fetched_at >= cutoff,
        )
        .first()
    )
    return recent is None


def _record(db: Session, obj_type: str, obj_id: int, now: datetime) -> None:
    db.add(models.SyncLog(obj_type=obj_type, obj_id=obj_id, fetched_at=now))


def _client_for(db: Session, user: models.User):
    if settings.chpp_mock:
        return chpp_client.get_client()
    token = (
        db.query(models.OAuthToken)
        .filter(models.OAuthToken.user_id == user.id, models.OAuthToken.revoked_at.is_(None))
        .order_by(models.OAuthToken.created_at.desc())
        .first()
    )
    if token is None:
        raise CHPPError(0, "no active OAuth token for this user")
    return chpp_client.get_client(token.token, token.token_secret)


def _currency_for(db: Session, chpp, league_id: int | None, now: datetime):
    """Cached currency info for a league (CHPP money is SEK; local = SEK/rate).

    Rates are effectively static, so worlddetails is refreshed at most every
    CURRENCY_MAX_AGE_DAYS. On fetch failure the stale cache (or None) is used.
    """
    if league_id is None:
        return None
    info = (
        db.query(models.CurrencyInfo)
        .filter(models.CurrencyInfo.league_id == league_id)
        .first()
    )
    if info is not None and (now - info.fetched_at).days < CURRENCY_MAX_AGE_DAYS:
        return info
    try:
        data = parse_worlddetails(chpp.fetch("worlddetails", "1.9"), league_id)
    except CHPPError:
        return info
    if not data or not data["currency_rate"]:
        return info
    if info is None:
        info = models.CurrencyInfo(league_id=league_id)
        db.add(info)
    info.currency_name = data["currency_name"]
    info.currency_rate = data["currency_rate"]
    info.fetched_at = now
    return info


def _to_local(value, currency):
    if value is None or currency is None or not currency.currency_rate:
        return value
    return round(value / currency.currency_rate)


def coach_level_from_squad(squad: list[dict]):
    """Coach skill on the denomination scale, from the coach's TrainerData.

    The modern coach scale is 1–5 (TrainerSkillLevel); it corresponds to the
    old denominations 4–8 (weak … excellent), so it is normalised with +3.
    The old denominated TrainerSkill (viewOldCoaches) is used verbatim.
    """
    for p in squad:
        if p.get("trainer_skill"):
            return p["trainer_skill"]
        if p.get("trainer_skill_level"):
            return p["trainer_skill_level"] + 3
    return None


def fetch_user_teams(db: Session, user: models.User) -> list[dict]:
    """All (non-bot) senior teams the user manages — for the team chooser."""
    chpp = _client_for(db, user)
    td = parse_teamdetails(chpp.fetch("teamdetails", "3.9", userID=user.ht_user_id))
    return [t for t in td["teams"] if not t["is_bot"]] or td["teams"]


def sync_trainer(
    db: Session,
    user: models.User,
    force: bool = False,
    team_id: int | None = None,
) -> models.TrainerProfile:
    """Refresh the fact side of a trainer's registry entry from CHPP.

    Never touches declarations — those are intentions, not facts. A user with
    several teams must pick one (TeamChoiceRequired) — never guess for them.
    """
    now = datetime.utcnow()
    if not force and not _can_refresh(db, "trainer", user.ht_user_id, now):
        raise SyncThrottled()

    chpp = _client_for(db, user)

    td = parse_teamdetails(chpp.fetch("teamdetails", "3.9", userID=user.ht_user_id))
    teams = [t for t in td["teams"] if not t["is_bot"]] or td["teams"]
    if not teams:
        raise CHPPError(-1, "user has no teams")

    if team_id is not None:
        primary = next((t for t in teams if t["team_id"] == team_id), None)
        if primary is None:
            raise CHPPError(-1, "team does not belong to this user")
    elif user.trainer_profile is not None:
        primary = next(
            (t for t in teams if t["team_id"] == user.trainer_profile.team_id), None
        )
        if primary is None:
            raise CHPPError(-1, "the connected team no longer belongs to this user")
    elif len(teams) > 1:
        raise TeamChoiceRequired(teams)
    else:
        primary = teams[0]
    team_id = primary["team_id"]

    tr = parse_training(chpp.fetch("training", "2.2", teamId=team_id))
    ec = parse_economy(chpp.fetch("economy", "1.4", teamId=team_id))
    squad = parse_players(chpp.fetch("players", "2.8", teamID=team_id))

    profile = user.trainer_profile
    if profile is None:
        profile = models.TrainerProfile(user_id=user.id, team_id=team_id)
        db.add(profile)
        user.trainer_profile = profile

    profile.team_id = team_id
    profile.team_name = primary["team_name"] or ""
    profile.is_bot = bool(primary["is_bot"])
    profile.ht_last_login = td["user"]["last_login"]
    tt = tr["training_type_id"]
    profile.training_type = TRAINING_TYPE_TO_SKILL.get(tt, "other") if tt is not None else "other"
    profile.training_intensity = tr["training_level"]
    profile.stamina_share = tr["stamina_part"]
    # Coach level: training.xml carries none (only TrainerID/Name), so the
    # real source is the coach's TrainerData in players.xml.
    profile.coach_level = tr["coach_level"] or coach_level_from_squad(squad)
    profile.assistant_level = tr["assistant_level"]

    # CHPP money is SEK — convert to the league's local currency.
    currency = _currency_for(db, chpp, primary["league_id"], now)
    profile.league_id = primary["league_id"]
    profile.currency_name = currency.currency_name if currency else None
    profile.currency_rate = currency.currency_rate if currency else None
    profile.cash = _to_local(ec["cash"], currency)
    profile.expected_cash = _to_local(ec["expected_cash"], currency)
    profile.last_sync = now

    # Replace the squad snapshot, preserving owner-marked training flags.
    trained_flags = {p.ht_player_id: p.in_trained_position for p in profile.squad}
    profile.squad.clear()
    for p in squad:
        profile.squad.append(
            models.SquadPlayer(
                ht_player_id=p["ht_player_id"],
                name=f"{p['first_name']} {p['last_name']}".strip(),
                age_years=p["age_years"],
                age_days=p["age_days"],
                specialty_id=p["specialty_id"] or 0,
                tsi=p["tsi"],
                salary=_to_local(p["salary"], currency),
                skills=p["skills"],
                in_trained_position=trained_flags.get(p["ht_player_id"], False),
            )
        )

    _record(db, "trainer", user.ht_user_id, now)
    db.commit()
    return profile


def sync_tracked_player(db: Session, player: models.TrackedPlayer, actor: models.User, force: bool = False) -> None:
    """Refresh public playerdetails data for a registry player."""
    now = datetime.utcnow()
    if not force and not _can_refresh(db, "player", player.ht_player_id, now):
        raise SyncThrottled()

    chpp = _client_for(db, actor)
    data = parse_playerdetails(chpp.fetch("playerdetails", "3.2", playerID=player.ht_player_id))

    # Money fields are SEK — convert via the owner league's currency.
    currency = _currency_for(db, chpp, data["owner_league_id"], now)

    full_name = f"{data['first_name']} {data['last_name']}".strip()
    if full_name:
        player.name = full_name
    player.age_years = data["age_years"]
    player.age_days = data["age_days"]
    player.tsi = data["tsi"]
    player.salary = _to_local(data["salary"], currency)
    player.specialty_id = data["specialty_id"]
    player.owner_team_id = data["owner_team_id"]
    player.owner_team_name = data["owner_team_name"]
    player.caps = data["caps"]
    player.caps_u20 = data["caps_u20"]
    player.national_team_id = data["national_team_id"]
    player.national_team_name = data["national_team_name"]
    player.currency_name = currency.currency_name if currency else None
    if data["transfer_listed"]:
        player.market_status = "listed"
        player.asking_price = _to_local(data["asking_price"], currency)
        player.deadline = data["deadline"]
    player.last_public_sync = now

    _record(db, "player", player.ht_player_id, now)
    db.commit()
