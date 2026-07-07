ROOT=src

.PHONY: help rlint rfmt types check tests

help:
	@echo "   Tool   |   Command   |   Description"
	@echo "   Ruff      make rlint     'uv run ruff check . --fix'"
	@echo "   Ruff      make rfmt      'uv run ruff format .'"
	@echo ""
	@echo "   Mypy      make types     'uv run mypy .'"
	@echo ""
	@echo "    *        make check     'rlint rfmt types' - Run all checks"
	@echo "  pytest     make tests      'uv run pytest -v' + coverage percent"

rlint:
	uv run ruff check $(ROOT) --fix

rfmt:
	uv run ruff format $(ROOT)

types:
	uv run mypy $(ROOT)

check: rlint rfmt types

tests:
	uv run pytest -v --cov --cov-branch --cov-report=term-missing
