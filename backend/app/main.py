"""FastAPI application entry point for the SIH26135 prototype.

Day 3 wires the auth + minimal read routes into a single app. Runs with
``uvicorn backend.app.main:app`` from the project root.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.config import APP_NAME, DEBUG
from backend.app.database.session import engine, init_db
from backend.app.routes import auth, employment, trainees, training


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ensure the SQLite schema exists on startup (idempotent)."""
    init_db()
    yield
    engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version="0.3.0",
        debug=DEBUG,
        lifespan=lifespan,
    )

    @app.get("/api/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "app": APP_NAME}

    app.include_router(auth.router, prefix="/api")
    app.include_router(trainees.router, prefix="/api")
    app.include_router(training.router, prefix="/api")
    app.include_router(employment.router, prefix="/api")

    return app


app = create_app()