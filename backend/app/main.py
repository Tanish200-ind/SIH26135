"""FastAPI application entry point for the SIH26135 prototype.

Day 3 wires the auth + minimal read routes into a single app. Day 4 adds the
read-only analytics endpoints. Runs with
``uvicorn backend.app.main:app`` from the project root.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.config import APP_NAME, DEBUG
from backend.app.database.session import engine, get_db, init_db
from backend.app.routes import analytics, auth, employment, trainees, training


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ensure the SQLite schema exists on startup (idempotent)."""
    init_db()
    yield
    engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version="0.7.0",
        debug=DEBUG,
        lifespan=lifespan,
    )

    @app.get("/api/health", tags=["meta"])
    def health(db: Session = Depends(get_db)) -> dict:
        """Public liveness probe that also verifies database connectivity."""
        try:
            db.execute(text("SELECT 1"))
        except Exception:  # any DB failure must surface as an explicit 503
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable",
            )
        return {"status": "ok", "app": APP_NAME, "database": "connected"}

    app.include_router(auth.router, prefix="/api")
    app.include_router(trainees.router, prefix="/api")
    app.include_router(training.router, prefix="/api")
    app.include_router(employment.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")

    return app


app = create_app()