#!/bin/bash
# Test runner script for allsorted
# Created by orpheus497

set -e  # Exit on error

echo "========================================="
echo "  allsorted Test Suite"
echo "========================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating venv: source venv/bin/activate"
    echo ""
fi

# Parse arguments
COVERAGE=false
VERBOSE=false
FAST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --fast|-f)
            FAST=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./scripts/run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --coverage, -c    Generate coverage report"
            echo "  --verbose, -v     Verbose test output"
            echo "  --fast, -f        Skip slow tests"
            echo "  --help, -h        Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_ARGS=""

if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -v"
fi

if [ "$FAST" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=allsorted --cov-report=term-missing --cov-report=html"
fi

# Run tests
echo "Running tests..."
echo "Command: pytest $PYTEST_ARGS"
echo ""

pytest $PYTEST_ARGS

# Show coverage report location if generated
if [ "$COVERAGE" = true ]; then
    echo ""
    echo "========================================="
    echo "✅ Coverage report generated!"
    echo "   HTML report: htmlcov/index.html"
    echo ""
    echo "   To view: open htmlcov/index.html"
    echo "========================================="
fi

echo ""
echo "========================================="
echo "✅ All tests passed!"
echo "========================================="
