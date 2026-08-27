from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .db import init_db
from .routers import admin, auth, dashboard, scout, trainer
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
