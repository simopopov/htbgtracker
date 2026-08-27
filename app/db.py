from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
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


def init_db():
    from . import models  # noqa: F401  — register tables on the metadata

    _migrate_columns()
    Base.metadata.create_all(engine)
