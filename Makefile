ROOT=src

.PHONY: help rlint rfmt types check

help:
	@echo "   Tool   |   Command   |   Description"
	@echo "   Ruff      make rlint     'uv run ruff check . --fix'"
	@echo "   Ruff      make rfmt      'uv run ruff format .'"
	@echo ""
	@echo "   Mypy      make types     'uv run mypy .'"
	@echo ""
	@echo "    *        make check     'rlint rfmt types' - Run all checks"

rlint:
	uv run ruff check $(ROOT) --fix

rfmt:
	uv run ruff format $(ROOT)

types:
	uv run mypy $(ROOT)

check: rlint rfmt types
