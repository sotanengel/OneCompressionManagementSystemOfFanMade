from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ocms.api.routers.cost import router as cost_router
from ocms.api.routers.jobs import router as jobs_router
from ocms.api.routers.log_stream import router as log_stream_router

app = FastAPI(title="OneCompression Management System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(log_stream_router)
app.include_router(cost_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
