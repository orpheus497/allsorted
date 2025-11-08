#!/bin/bash
# Quality check runner for allsorted
# Runs all code quality checks: formatting, linting, type checking, and tests
# Created by orpheus497

set -e  # Exit on error

echo "========================================="
echo "  allsorted Quality Checks"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Warning: No virtual environment detected${NC}"
    echo "   Consider activating venv: source venv/bin/activate"
    echo ""
fi

# Parse arguments
FIX=false
FAST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --fast)
            FAST=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./scripts/run_checks.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --fix         Auto-fix issues where possible"
            echo "  --fast        Skip tests (faster feedback)"
            echo "  --help, -h    Show this help message"
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

# Track failures
FAILED=false

# 1. Black formatting
echo "1️⃣  Running Black (code formatter)..."
if [ "$FIX" = true ]; then
    if black src/ tests/; then
        echo -e "${GREEN}✅ Black: Formatting applied${NC}"
    else
        echo -e "${RED}❌ Black: Formatting failed${NC}"
        FAILED=true
    fi
else
    if black --check src/ tests/; then
        echo -e "${GREEN}✅ Black: Code is formatted correctly${NC}"
    else
        echo -e "${RED}❌ Black: Code needs formatting${NC}"
        echo "   Run with --fix to auto-format"
        FAILED=true
    fi
fi
echo ""

# 2. Ruff linting
echo "2️⃣  Running Ruff (linter)..."
if [ "$FIX" = true ]; then
    if ruff check --fix src/ tests/; then
        echo -e "${GREEN}✅ Ruff: Issues fixed${NC}"
    else
        echo -e "${RED}❌ Ruff: Some issues couldn't be auto-fixed${NC}"
        FAILED=true
    fi
else
    if ruff check src/ tests/; then
        echo -e "${GREEN}✅ Ruff: No linting issues${NC}"
    else
        echo -e "${RED}❌ Ruff: Linting issues found${NC}"
        echo "   Run with --fix to auto-fix"
        FAILED=true
    fi
fi
echo ""

# 3. Mypy type checking
echo "3️⃣  Running Mypy (type checker)..."
if mypy src/; then
    echo -e "${GREEN}✅ Mypy: Type checking passed${NC}"
else
    echo -e "${RED}❌ Mypy: Type checking failed${NC}"
    FAILED=true
fi
echo ""

# 4. Tests (skip if --fast)
if [ "$FAST" = false ]; then
    echo "4️⃣  Running Pytest (tests)..."
    if pytest; then
        echo -e "${GREEN}✅ Pytest: All tests passed${NC}"
    else
        echo -e "${RED}❌ Pytest: Some tests failed${NC}"
        FAILED=true
    fi
    echo ""
else
    echo "4️⃣  Skipping tests (--fast mode)"
    echo ""
fi

# Summary
echo "========================================="
if [ "$FAILED" = true ]; then
    echo -e "${RED}❌ Quality checks FAILED${NC}"
    echo ""
    echo "Some checks failed. Please fix the issues above."
    if [ "$FIX" = false ]; then
        echo ""
        echo "Tip: Run with --fix to auto-fix formatting and linting issues:"
        echo "  ./scripts/run_checks.sh --fix"
    fi
    echo "========================================="
    exit 1
else
    echo -e "${GREEN}✅ All quality checks PASSED!${NC}"
    echo ""
    echo "Your code is ready to commit! 🎉"
    echo "========================================="
    exit 0
fi
