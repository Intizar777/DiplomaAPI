#!/bin/bash

# init.sh — Standard initialization and verification for Dashboard Analytics API
# Run this at the start of each session to ensure environment is ready

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         Dashboard Analytics API — Session Initialization          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Step 1: Check Python version
echo "1. Checking Python version..."
if ! command -v python3 &> /dev/null; then
    error "Python 3 not found. Please install Python 3.10+"
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
success "Python $PYTHON_VERSION found"

# Step 2: Check virtual environment
echo ""
echo "2. Checking virtual environment..."
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ ! -d "venv" ]]; then
        warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    source venv/bin/activate
fi
success "Virtual environment activated"

# Step 3: Check .env file exists
echo ""
echo "3. Checking .env configuration..."
if [[ ! -f ".env" ]]; then
    error ".env file not found. Copy from .env.example and configure"
fi
success ".env file found"

# Step 4: Install/update dependencies
echo ""
echo "4. Installing Python dependencies..."
pip install -q -r requirements.txt || error "Failed to install dependencies"
success "Dependencies installed"

# Step 5: Check database connection
echo ""
echo "5. Checking database connection..."
python3 -c "
import sys
from app.config import settings
from sqlalchemy import create_engine
try:
    engine = create_engine(settings.DATABASE_URL.replace('asyncpg', 'psycopg2'))
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('Database connection OK')
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
" || error "Database connection failed. Check DATABASE_URL in .env"
success "Database connection verified"

# Step 6: Run database migrations
echo ""
echo "6. Running database migrations..."
if ! alembic upgrade head 2>&1 | grep -q "ERROR"; then
    success "Database migrations completed"
else
    error "Database migration failed"
fi

# Step 7: Run type checks
echo ""
echo "7. Running type checks (mypy)..."
if mypy app/ --ignore-missing-imports 2>&1 | tee /tmp/mypy_output.txt | grep -q "error:"; then
    warning "Type check issues found (see above)"
    echo ""
    echo "Note: Type issues should be fixed before marking features as done"
else
    success "Type checks passed"
fi

# Step 8: Run linting
echo ""
echo "8. Running code quality checks (ruff)..."
if command -v ruff &> /dev/null; then
    if ruff check app/ 2>&1 | grep -q "error"; then
        warning "Linting issues found (see above)"
    else
        success "Linting passed"
    fi
else
    warning "ruff not installed, skipping linting"
fi

# Step 9: Run tests
echo ""
echo "9. Running test suite..."
if pytest tests/ -v --tb=short 2>&1 | tee /tmp/pytest_output.txt | grep -q "passed"; then
    PASSED=$(grep -oP '\d+(?= passed)' /tmp/pytest_output.txt | tail -1)
    success "Tests passed ($PASSED tests)"
else
    warning "Some tests failed or no tests found"
    echo ""
    echo "Note: Run 'pytest tests/ -v' for details"
fi

# Step 10: Summary
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                   Initialization Complete!                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Read progress.md for session context"
echo "  2. Read feature_list.json to see what's in progress"
echo "  3. Start coding on your assigned feature"
echo ""
echo "Development commands:"
echo "  • Start dev server: uvicorn app.main:app --reload"
echo "  • Run tests: pytest tests/ -v"
echo "  • Type check: mypy app/"
echo "  • View API docs: http://localhost:8000/docs (after starting server)"
echo ""
echo "Before ending your session:"
echo "  • Run: pytest tests/ && mypy app/"
echo "  • Update: progress.md and feature_list.json"
echo "  • Commit with clear message"
echo ""
