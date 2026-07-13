.PHONY: install test lint format

install:
	uv pip install -e ".[dev]"

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .
