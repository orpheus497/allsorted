#!/bin/bash
# Distribution Verification Script for allsorted
# Verifies the project is ready for distribution

set -e

echo "================================================"
echo "  allsorted Distribution Verification"
echo "================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. Checking Python files..."
if python3 -m py_compile src/allsorted/*.py 2>/dev/null; then
    check_pass "All Python files compile"
else
    check_fail "Python compilation failed"
fi

echo ""
echo "2. Checking required files..."
for file in README.md LICENSE CHANGELOG.md pyproject.toml requirements.txt; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_fail "$file missing"
    fi
done

echo ""
echo "3. Checking package structure..."
if [ -d "src/allsorted" ]; then
    check_pass "Package directory exists"
else
    check_fail "Package directory missing"
fi

if [ -f "src/allsorted/__init__.py" ]; then
    check_pass "__init__.py exists"
else
    check_fail "__init__.py missing"
fi

echo ""
echo "4. Checking module imports..."
if python3 -c "import sys; sys.path.insert(0, 'src'); from allsorted import __version__; print(f'Version: {__version__}')" 2>/dev/null; then
    check_pass "Package imports successfully"
else
    check_fail "Package import failed"
fi

echo ""
echo "5. Checking test structure..."
if [ -d "tests" ]; then
    check_pass "Tests directory exists"
else
    check_warn "Tests directory missing"
fi

echo ""
echo "6. Checking documentation..."
if grep -q "orpheus497" README.md; then
    check_pass "Creator attribution present"
else
    check_fail "Creator attribution missing"
fi

if grep -q "MIT" LICENSE; then
    check_pass "MIT License present"
else
    check_fail "License verification failed"
fi

echo ""
echo "7. Checking installation scripts..."
if [ -f "scripts/install.sh" ] && [ -x "scripts/install.sh" ]; then
    check_pass "install.sh present and executable"
else
    check_warn "install.sh not executable"
fi

echo ""
echo "8. Checking .gitignore..."
if [ -f ".gitignore" ]; then
    if grep -q ".dev-docs" .gitignore; then
        check_pass ".gitignore excludes .dev-docs"
    else
        check_warn ".gitignore doesn't exclude .dev-docs"
    fi
else
    check_warn ".gitignore missing"
fi

echo ""
echo "9. Checking CHANGELOG..."
if grep -q "Unreleased" CHANGELOG.md; then
    check_pass "CHANGELOG has Unreleased section"
else
    check_fail "CHANGELOG missing Unreleased section"
fi

echo ""
echo "10. Verifying FOSS compliance..."
if grep -q "rich" requirements.txt && grep -q "click" requirements.txt && grep -q "pyyaml" requirements.txt; then
    check_pass "All runtime dependencies declared"
else
    check_fail "Missing runtime dependencies"
fi

echo ""
echo "================================================"
echo "  Distribution Verification Complete"
echo "================================================"
echo ""
echo "✓ Project is ready for distribution!"
echo ""
echo "Next steps:"
echo "  1. Build package:  python3 -m build"
echo "  2. Install local:  pip install -e ."
echo "  3. Test install:   allsorted --help"
echo ""
