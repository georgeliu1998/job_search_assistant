#!/bin/bash
# Clean up Python cache files and directories

echo "Cleaning up __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "Cleaning up .pyc files..."
find . -name "*.pyc" -delete 2>/dev/null || true

echo "Cleaning up .pyo files..."
find . -name "*.pyo" -delete 2>/dev/null || true

echo "Cleaning up mypy cache..."
rm -rf .mypy_cache 2>/dev/null || true

echo "Cleaning up pytest cache..."
rm -rf .pytest_cache 2>/dev/null || true

echo "All cleanup complete! 🧹"
