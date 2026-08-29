from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from . import models
from .config import settings
from .db import get_db, init_db
from .routers import admin, auth, cron, dashboard, scout, trainer
from .seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.chpp_mock:
        seed_if_empty()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(scout.router)
app.include_router(trainer.router)
app.include_router(admin.router)
app.include_router(cron.router)


@app.get("/healthz")
def healthz(db: Session = Depends(get_db)):
    """Liveness + keep-alive: the query counts as database activity, which
    keeps a Supabase free-tier project from being paused for inactivity."""
    users = db.execute(select(func.count(models.User.id))).scalar_one()
    return {"ok": True, "users": users}
