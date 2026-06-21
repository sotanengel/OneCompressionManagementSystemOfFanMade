from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ocms.api.routers.cancel import router as cancel_router
from ocms.api.routers.cost import router as cost_router
from ocms.api.routers.jobs import router as jobs_router
from ocms.api.routers.log_stream import router as log_stream_router
from ocms.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="OneCompression Management System", version="0.1.0")

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    app.include_router(jobs_router)
    app.include_router(log_stream_router)
    app.include_router(cost_router)
    app.include_router(cancel_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
