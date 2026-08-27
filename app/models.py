from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

ROLE_HEAD_COACH = "head_coach"
ROLE_ASSISTANT_COACH = "assistant_coach"
ROLE_MASTER_SCOUT = "master_scout"
ROLE_POSITION_SCOUT = "position_scout"
ROLE_TRAINER = "trainer"
ROLES = [ROLE_HEAD_COACH, ROLE_ASSISTANT_COACH, ROLE_MASTER_SCOUT, ROLE_POSITION_SCOUT, ROLE_TRAINER]

TRAINING_SKILLS = ["goalkeeping", "defending", "playmaking", "winger", "passing", "scoring", "set_pieces"]
# Skills a scout can record on a tracked player (owner-only in CHPP, so these
# are manual entries from what the current owner shared).
PLAYER_SKILLS = TRAINING_SKILLS + ["stamina"]
SPECIALTY_IDS = [0, 1, 2, 3, 4, 5, 6, 8]
DECLARATION_TIMINGS = ["immediate", "after_cycle", "after_age"]
MARKET_STATUSES = ["watching", "planned", "listed", "transferred"]
NT_SQUADS = ["senior", "u21"]
DEFAULT_DECLARATION_DAYS = 28


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    ht_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    login_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(30), default=ROLE_TRAINER)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    trainer_profile: Mapped[Optional[TrainerProfile]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    tokens: Mapped[list[OAuthToken]] = relationship(back_populates="user", cascade="all, delete-orphan")
    claims: Mapped[list[Claim]] = relationship(back_populates="scout")


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(String(200))
    token_secret: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="tokens")


class TrainerProfile(Base):
    """Facts about a trainer's team, refreshed from CHPP. Never hand-edited."""

    __tablename__ = "trainer_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    team_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    team_name: Mapped[str] = mapped_column(String(120), default="")
    training_type: Mapped[str] = mapped_column(String(30), default="other")
    training_intensity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stamina_share: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    coach_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assistant_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # CHPP returns money in SEK (Hattrick's internal currency); sync converts
    # to the team's local currency via the worlddetails CurrencyRate, and the
    # rate/name used are recorded here.
    cash: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    expected_cash: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    league_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency_name: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    currency_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    ht_last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="trainer_profile")
    squad: Mapped[list[SquadPlayer]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    declarations: Mapped[list[Declaration]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    interests: Mapped[list[Interest]] = relationship(back_populates="profile", cascade="all, delete")


class SquadPlayer(Base):
    __tablename__ = "squad_players"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("trainer_profiles.id"), index=True)
    ht_player_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    age_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    age_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    specialty_id: Mapped[int] = mapped_column(Integer, default=0)
    tsi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Owner-marked flag: which squad members occupy a trained slot.
    in_trained_position: Mapped[bool] = mapped_column(Boolean, default=False)

    profile: Mapped[TrainerProfile] = relationship(back_populates="squad")


class Declaration(Base):
    """A trainer's intention: a slot they are willing to free, under conditions.

    Declared, never derived. Expires after valid_until and disappears from
    scout queries until renewed (PRODUCT.md §3).
    """

    __tablename__ = "declarations"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("trainer_profiles.id"), index=True)
    slot_type: Mapped[str] = mapped_column(String(30))  # a TRAINING_SKILLS entry or "any"
    quality_threshold: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # denomination 1–20
    # How many more weeks the trainer commits to this training type;
    # NULL = indefinitely ("ще съм на разиграване безсрочно").
    training_weeks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    player_to_move: Mapped[str] = mapped_column(String(200), default="")
    expected_sale_price: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    timing: Mapped[str] = mapped_column(String(20), default="immediate")
    conditional_on_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(Text, default="")
    valid_until: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | withdrawn
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    renewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    profile: Mapped[TrainerProfile] = relationship(back_populates="declarations")


class TrackedPlayer(Base):
    """A talent in the scouting registry. Public CHPP data auto-fills; scout
    fields (estimate, market plan, notes) are the scout's judgement."""

    __tablename__ = "tracked_players"

    id: Mapped[int] = mapped_column(primary_key=True)
    ht_player_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    squad: Mapped[str] = mapped_column(String(10), default="u21")  # senior | u21
    target_skill: Mapped[str] = mapped_column(String(30))
    estimated_price: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    market_status: Mapped[str] = mapped_column(String(20), default="watching")
    expected_listing: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    # Scout-entered current skills ({skill: 1–20}); never auto-synced because
    # CHPP exposes skills to the owner only.
    skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    added_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Public data from playerdetails (auto-filled, read-only in the UI)
    age_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    age_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tsi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    specialty_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    owner_team_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    owner_team_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    asking_price: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    caps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    caps_u20: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    national_team_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    national_team_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    # Currency of the converted money fields (salary, asking price).
    currency_name: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    last_public_sync: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    added_by: Mapped[Optional[User]] = relationship()
    claims: Mapped[list[Claim]] = relationship(back_populates="player", cascade="all, delete")
    interests: Mapped[list[Interest]] = relationship(back_populates="player", cascade="all, delete")
    plan_steps: Mapped[list[TrainingPlanStep]] = relationship(
        back_populates="player",
        cascade="all, delete",
        order_by="TrainingPlanStep.position, TrainingPlanStep.id",
    )
    comments: Mapped[list[Comment]] = relationship(
        back_populates="player",
        cascade="all, delete",
        order_by="Comment.created_at, Comment.id",
    )


class Comment(Base):
    """Discussion thread under a tracked player: comments and one level of
    replies, from scouts and trainers alike."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("tracked_players.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id"), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    player: Mapped[TrackedPlayer] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()
    replies: Mapped[list[Comment]] = relationship(
        cascade="all, delete",
        order_by="Comment.created_at, Comment.id",
    )


class TrainingPlanStep(Base):
    """One row of the training plan a scout attaches to a player going to
    market: what the buying trainer should train, for roughly how long, and
    at what stamina share. Shown to trainers in the pipeline."""

    __tablename__ = "training_plan_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("tracked_players.id"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=1)
    skill: Mapped[str] = mapped_column(String(30))
    weeks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stamina_share: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    player: Mapped[TrackedPlayer] = relationship(back_populates="plan_steps")


class Claim(Base):
    """A scout marks a player as being handled by them, so two scouts don't
    pitch the same trainer (PRODUCT.md P1 #8)."""

    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("tracked_players.id"), index=True)
    scout_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    trainer_profile_id: Mapped[Optional[int]] = mapped_column(ForeignKey("trainer_profiles.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | released | completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    player: Mapped[TrackedPlayer] = relationship(back_populates="claims")
    scout: Mapped[User] = relationship(back_populates="claims")
    trainer_profile: Mapped[Optional[TrainerProfile]] = relationship()


class Interest(Base):
    """A trainer raises a hand for a pipeline player (the reverse flow the
    user asked for: trainers see what scouts plan to bring to market)."""

    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("tracked_players.id"), index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("trainer_profiles.id"), index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    # The most the trainer is ready to bid for this player (local currency).
    max_bid: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | accepted | declined | withdrawn
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    player: Mapped[TrackedPlayer] = relationship(back_populates="interests")
    profile: Mapped[TrainerProfile] = relationship(back_populates="interests")


class CurrencyInfo(Base):
    """Cached worlddetails currency data per league. CHPP money is SEK;
    local amount = SEK value / currency_rate."""

    __tablename__ = "currency_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    currency_name: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    currency_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SyncLog(Base):
    """Fetch-discipline ledger: refresh no more than once per day per object."""

    __tablename__ = "sync_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    obj_type: Mapped[str] = mapped_column(String(20), index=True)
    obj_id: Mapped[int] = mapped_column(Integer, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
