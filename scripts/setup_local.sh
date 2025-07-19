#!/bin/bash

# Local development setup script
set -e

echo "🔧 Setting up local development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Set variables
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

# Check Python
echo "🐍 Checking Python installation..."
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Python 3 is required but not installed.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Check pip
if ! command -v pip3 >/dev/null 2>&1; then
    echo -e "${RED}pip3 is required but not installed.${NC}"
    exit 1
fi

# Create virtual environment
echo "🏗️  Creating virtual environment..."
cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

echo "📦 Installing project dependencies..."
pip install -r requirements.txt

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create .env files
echo "📝 Creating environment files..."

# Backend .env
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo -e "${GREEN}✅ Backend .env created${NC}"
    echo -e "${YELLOW}⚠️  Please update backend/.env with your AWS configuration${NC}"
else
    echo -e "${YELLOW}⚠️  Backend .env already exists${NC}"
fi

# Frontend .env
if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
    echo -e "${GREEN}✅ Frontend .env created${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend .env already exists${NC}"
fi

echo ""
echo "🎉 Local development setup completed!"
echo ""
echo "🚀 To start development:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Start backend: cd backend && uvicorn main:app --reload"
echo "  3. Start frontend: cd frontend && streamlit run app.py"
echo ""
echo "📋 Alternative with Docker:"
echo "  docker-compose up -d"
echo ""
echo "🔧 Don't forget to:"
echo "  - Update .env files with your AWS credentials"
echo "  - Configure AWS CLI: aws configure"
echo "  - Deploy infrastructure: ./scripts/deploy.sh"

echo -e "${GREEN}✅ Setup script completed!${NC}"
