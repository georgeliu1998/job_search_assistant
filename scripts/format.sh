#!/bin/bash
# Format and lint all Python code using ruff

echo "Running Ruff linter (with import sorting and autofix)..."
uv run ruff check --fix src tests ui

echo "Running Ruff formatter..."
uv run ruff format src tests ui

echo "Checking with mypy..."
uv run mypy src

echo "All formatting complete! 🎉"
