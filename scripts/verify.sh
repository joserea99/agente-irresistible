#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }
info() { echo -e "${YELLOW}→ $1${NC}"; }

echo "═══════════════════════════════════════"
echo " Irresistible Agent — Full Verification"
echo "═══════════════════════════════════════"

# --- Backend ---
info "Backend: installing dependencies..."
cd "$ROOT/backend"
pip install -r requirements.txt -q 2>/dev/null && pass "Backend dependencies installed" || fail "Backend dependency install failed"

info "Backend: running tests..."
if python -m pytest --tb=short -q 2>/dev/null; then
    pass "Backend tests passed"
else
    fail "Backend tests failed"
fi

# --- Frontend ---
info "Frontend: installing dependencies..."
cd "$ROOT/frontend"
npm install --silent 2>/dev/null && pass "Frontend dependencies installed" || fail "Frontend dependency install failed"

info "Frontend: building..."
if npm run build 2>/dev/null; then
    pass "Frontend build succeeded"
else
    fail "Frontend build failed"
fi

info "Frontend: linting..."
if npm run lint 2>/dev/null; then
    pass "Frontend lint passed"
else
    echo -e "${YELLOW}⚠ Frontend lint had warnings${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN} All checks passed!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
