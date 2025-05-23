#!/bin/bash
# Format all Python code using black and isort

echo "Running Black formatter..."
uv run black src tests ui

echo "Running isort import sorter..."
uv run isort src tests ui

echo "Checking with mypy..."
uv run mypy src

echo "All formatting complete! 🎉"
