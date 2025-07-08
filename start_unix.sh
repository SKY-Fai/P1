#!/bin/bash

# F-AI Accountant Enterprise Startup Script
# Unix/Linux/macOS Version

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

clear

echo -e "${GREEN}"
echo "========================================"
echo " F-AI ACCOUNTANT ENTERPRISE v2.0.0"
echo "========================================"
echo " Complete Enterprise Accounting SaaS"
echo "========================================"
echo -e "${NC}"

# Check Python installation
echo -e "${BLUE}[INFO]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 is not installed"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}[INFO]${NC} Python ${PYTHON_VERSION} detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}[INFO]${NC} Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}[INFO]${NC} Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/lib/python*/site-packages/flask" ]; then
    echo -e "${BLUE}[INFO]${NC} Installing dependencies..."
    pip install -r requirements.txt
fi

# Setup database if needed
if [ ! -f "database/fai_accountant.db" ]; then
    echo -e "${BLUE}[INFO]${NC} Setting up database..."
    python database/database_manager.py setup
fi

echo -e "${GREEN}[INFO]${NC} Starting F-AI Accountant Server..."
echo ""
echo -e "${YELLOW}[ACCESS]${NC} Application URL: http://localhost:5000"
echo -e "${YELLOW}[LOGIN]${NC}  Username: admin"
echo -e "${YELLOW}[LOGIN]${NC}  Password: test"
echo ""
echo -e "${BLUE}[STATUS]${NC} Server is starting... Please wait"
echo -e "${BLUE}[INFO]${NC}   Press Ctrl+C to stop the server"
echo ""

# Start the application
python3 -m gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 300 --worker-class sync --max-requests 1000 --preload main:app

echo ""
echo -e "${GREEN}[INFO]${NC} Server stopped"
echo "Thank you for using F-AI Accountant!"