from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ocms.api.deps import get_db
from ocms.core.models import JobLog, JobStatus
from ocms.storage.repository import JobRepository

router = APIRouter(prefix="/jobs", tags=["log-stream"])

_TERMINAL_STATUSES = {JobStatus.COMPLETED, JobStatus.FAILED}


def _format_sse_event(log: JobLog) -> str:
    payload = json.dumps(
        {
            "log_id": str(log.log_id),
            "timestamp": log.timestamp.isoformat(),
            "level": log.level,
            "source": log.source,
            "message": log.message,
        }
    )
    return f"id: {log.timestamp.isoformat()}\ndata: {payload}\n\n"


@router.get("/{job_id}/log-stream")
async def stream_job_logs(
    job_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    repo = JobRepository(db)
    if repo.get(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")

    last_event_id_str = request.headers.get("Last-Event-ID")
    since: datetime | None = None
    if last_event_id_str:
        try:
            since = datetime.fromisoformat(last_event_id_str)
        except ValueError:
            since = None

    async def event_generator() -> AsyncGenerator[str, None]:
        nonlocal since
        while True:
            if await request.is_disconnected():
                return

            logs = await asyncio.to_thread(repo.get_logs_since, job_id, since)
            for log in logs:
                since = log.timestamp
                yield _format_sse_event(log)

            job = await asyncio.to_thread(repo.get, job_id)
            if job is not None and job.status in _TERMINAL_STATUSES:
                yield "event: done\ndata: {}\n\n"
                return

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
