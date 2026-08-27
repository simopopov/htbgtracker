import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Loads .env from the project root. Existing environment variables win, so
# tests and deployments can still override.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass
class Settings:
    secret_key: str = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///./scoutbridge.db")
    # Mock mode is the default: no request ever leaves the machine.
    # Flip to 0 only after the CHPP application is approved and keys are set.
    chpp_mock: bool = os.environ.get("CHPP_MOCK", "1") == "1"
    chpp_consumer_key: str = os.environ.get("CHPP_CONSUMER_KEY", "")
    chpp_consumer_secret: str = os.environ.get("CHPP_CONSUMER_SECRET", "")
    base_url: str = os.environ.get("BASE_URL", "http://localhost:8000")
    app_name: str = "HT Scout Bridge"
    app_version: str = "0.1.0"


settings = Settings()
