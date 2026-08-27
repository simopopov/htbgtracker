from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = settings.database_url
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    # Postgres (Supabase): normalize the URL onto the psycopg3 driver.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    # Serverless-friendly: no client-side pool (each invocation is short-
    # lived; Supabase's Supavisor pooler does the pooling), and no prepared
    # statements (transaction-mode pooling breaks them).
    return create_engine(
        url,
        poolclass=NullPool,
        connect_args={"prepare_threshold": None},
    )


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added after the first release; applied to existing SQLite databases
# on startup (create_all only creates missing tables, not missing columns).
_COLUMN_MIGRATIONS = [
    ("trainer_profiles", "league_id", "INTEGER"),
    ("trainer_profiles", "currency_name", "VARCHAR(30)"),
    ("trainer_profiles", "currency_rate", "FLOAT"),
    ("tracked_players", "currency_name", "VARCHAR(30)"),
    ("tracked_players", "skills", "TEXT"),
    ("declarations", "training_weeks", "INTEGER"),
    ("interests", "max_bid", "BIGINT"),
    ("tracked_players", "national_team_id", "INTEGER"),
    ("tracked_players", "national_team_name", "VARCHAR(120)"),
    ("declarations", "max_price", "BIGINT"),
    ("declarations", "min_age", "INTEGER"),
    ("declarations", "max_age", "INTEGER"),
    ("declarations", "specialty_id", "INTEGER"),
    ("declarations", "skill_reqs", "TEXT"),
]

# Columns retired by the declaration redesign (requirements instead of
# player-to-move / conditional-on-sale). Dropped when present.
_COLUMN_DROPS = [
    ("declarations", "quality_threshold"),
    ("declarations", "player_to_move"),
    ("declarations", "expected_sale_price"),
    ("declarations", "conditional_on_sale"),
]


def _migrate_columns():
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        for table, column, ddl_type in _COLUMN_MIGRATIONS:
            rows = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            existing = {row[1] for row in rows}
            if existing and column not in existing:
                conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")
        for table, column in _COLUMN_DROPS:
            rows = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            existing = {row[1] for row in rows}
            if column in existing:
                conn.exec_driver_sql(f"ALTER TABLE {table} DROP COLUMN {column}")


def init_db():
    from . import models  # noqa: F401  — register tables on the metadata

    _migrate_columns()
    Base.metadata.create_all(engine)
