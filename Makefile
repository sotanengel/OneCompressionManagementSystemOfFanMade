.PHONY: install test lint format migrate up down

install:
	cd backend && UV_INDEX_TAKUMI_GUARD_USERNAME=token UV_INDEX_TAKUMI_GUARD_PASSWORD=$(TAKUMI_GUARD_TOKEN) uv sync --extra dev

test:
	cd backend && OCMS_DATABASE_URL=postgresql+psycopg://ocms:ocms_local@localhost:5432/ocms uv run pytest -q

lint:
	cd backend && uv run ruff check src tests && uv run ruff format --check src tests

format:
	cd backend && uv run ruff check --fix src tests && uv run ruff format src tests

mypy:
	cd backend && uv run mypy src

migrate:
	cd backend && OCMS_DATABASE_URL=postgresql+psycopg://ocms:ocms_local@localhost:5432/ocms uv run alembic upgrade head

up:
	docker compose up -d db

down:
	docker compose down
