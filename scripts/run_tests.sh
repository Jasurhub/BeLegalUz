#!/bin/bash
# run_tests.sh - Run tests, linting, and coverage for BeLagel

set -e

echo "🚀 Starting BeLagel Test Suite..."

# 1. Code Formatting & Linting
echo " Checking code format (Black & Flake8)..."
black src/ tests/ --check
flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503

# 2. Run Tests with Coverage
echo " Running tests with coverage..."
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# 3. Generate Coverage Report
echo "📊 Coverage report generated in htmlcov/"
echo "✅ All tests passed successfully!"