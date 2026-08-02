ROOT=src

.PHONY: help rlint rfmt types check tests db-up migrate migrate-current down up dev-db-migrate seed-dev

help:
	@echo "       Tool           |       Command        |         Description"
	@echo "----------------------|----------------------|---------------------------------------------"
	@echo "       Ruff           |  make rlint          |    'uv run ruff check . --fix'"
	@echo "       Ruff           |  make rfmt           |    'uv run ruff format .'"
	@echo "                      |                      |    "
	@echo "       Mypy           |  make types          |    'uv run mypy .'"
	@echo "                      |                      |    "
	@echo "        *             |  make check          |    'rlint rfmt types' - Run all checks"
	@echo "                      |                      |    "
	@echo "      pytest          |  make tests          |    'uv run pytest -v' + coverage percent"
	@echo "                      |                      |    "
	@echo "      docker          |  make up             |    'docker compose up -d'"
	@echo "      docker          |  make down           |    'docker compose down'"
	@echo "                      |                      |    "
	@echo " uvicorn + db + redis |  make up-dev         |    'run local uvicorn + db & redis in docker compose'"
	@echo "       (docker)       |                      |    "
	@echo "                      |                      |    "
	@echo " alembic + db(docker) |  make db-migrate-dev |    'make alembic migrations in dev db'"
	@echo "                      |                      |    "
	@echo "       seed           |  make seed-dev       |    'fill development db with demo data'"

rlint:
	uv run ruff check $(ROOT) --fix

rfmt:
	uv run ruff format $(ROOT)

types:
	uv run mypy $(ROOT)

check: rlint rfmt types


tests:
	uv run pytest -v --cov --cov-branch --cov-report=term-missing


db-up:
	docker compose up -d blog_app_db

migrate:
	alembic upgrade head

migrate-current:
	alembic current

up:
	docker compose up -d

down:
	docker compose down

dev-db-migrate: db-up migrate migrate-current down

seed-dev:
	uv run python -m scripts.seed_dev
