FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --index-url https://pypi.org/simple/

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN useradd -m -u 1000 appuser && chown appuser:appuser /app

COPY --from=builder /app/.venv /app/.venv

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

CMD ["uvicorn", "ocms.main:app", "--host", "0.0.0.0", "--port", "8000"]
