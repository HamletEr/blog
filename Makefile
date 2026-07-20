ROOT=src

.PHONY: help rlint rfmt types check tests db-up migrate migrate-current down db-migrate-dev up run-dev

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
	@echo " uvicorn + db(docker) |  make run-dev        |    'run local uvicorn + db in docker compose'"
	@echo "                      |                      |    "
	@echo " alembic + db(docker) |  make db-migrate-dev |    'make alembic migrations in dev db'"

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

db-migrate-dev: db-up migrate migrate-current down

run-dev:
	make db-up && uv run uvicorn --app-dir src blog_app.main:app --reload
