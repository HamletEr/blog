ROOT=src

.PHONY: help rlint rfmt types check tests dev-db-up migrate migrate-current down up dev-db-migrate dev-seed

help:
	@echo "       Tool           |       Command        |         Description"
	@echo "----------------------|----------------------|---------------------------------------------"
	@echo "       Ruff           |  make rlint          |    'uv run ruff check src --fix'"
	@echo "       Ruff           |  make rfmt           |    'uv run ruff format src'"
	@echo "                      |                      |    "
	@echo "       Mypy           |  make types          |    'uv run mypy src'"
	@echo "                      |                      |    "
	@echo "        *             |  make check          |    'rlint rfmt types' - Run all checks"
	@echo "                      |                      |    "
	@echo "      pytest          |  make tests          |    'uv run pytest -v' + coverage"
	@echo "                      |                      |    "
	@echo "      docker          |  make up             |    'docker compose up -d'"
	@echo "      docker          |  make down           |    'docker compose down'"
	@echo "                      |                      |    "
	@echo "    db (docker)       |  make dev-db-up      |    'docker compose up -d blog_app_db'"
	@echo "      alembic         |  make migrate        |    'uv run alembic upgrade head'"
	@echo "      alembic         |  make migrate-current|    'uv run alembic current'"
	@echo " alembic + db(docker) |  make dev-db-migrate |    'dev-db-up migrate migrate-current'"
	@echo "                      |                      |    "
	@echo "       seed           |  make dev-seed       |    'fill development db with demo data'"

rlint:
	uv run ruff check $(ROOT) --fix

rfmt:
	uv run ruff format $(ROOT)

types:
	uv run mypy $(ROOT)

check: rlint rfmt types


tests:
	uv run pytest -v --cov --cov-branch --cov-report=term-missing


dev-db-up:
	docker compose up -d blog_app_db

migrate:
	uv run alembic upgrade head

migrate-current:
	uv run alembic current

up:
	docker compose up -d

down:
	docker compose down

dev-db-migrate: dev-db-up migrate migrate-current

dev-seed:
	uv run python -m scripts.seed_dev
