#!/bin/bash

echo "🔍 Verificando configuración de Irresistible Agent..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -n "Verificando Python... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 no encontrado"
    exit 1
fi

# Check Node.js
echo -n "Verificando Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} $NODE_VERSION"
else
    echo -e "${RED}✗${NC} Node.js no encontrado"
    exit 1
fi

# Check .env file
echo -n "Verificando archivo .env... "
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} Encontrado"
    
    # Check for required variables
    if grep -q "GOOGLE_API_KEY=" .env; then
        if grep -q "GOOGLE_API_KEY=tu_clave" .env; then
            echo -e "${YELLOW}⚠${NC}  GOOGLE_API_KEY no configurada (usa el valor de ejemplo)"
        else
            echo -e "${GREEN}✓${NC} GOOGLE_API_KEY configurada"
        fi
    else
        echo -e "${RED}✗${NC} GOOGLE_API_KEY no encontrada en .env"
    fi
    
    if grep -q "SECRET_KEY=" .env; then
        echo -e "${GREEN}✓${NC} SECRET_KEY configurada"
    else
        echo -e "${YELLOW}⚠${NC}  SECRET_KEY no encontrada en .env"
    fi
else
    echo -e "${YELLOW}⚠${NC}  No encontrado (copia .env.example a .env)"
fi

# Check backend dependencies
echo -n "Verificando dependencias del backend... "
if [ -f "backend/requirements.txt" ]; then
    echo -e "${GREEN}✓${NC} requirements.txt encontrado"
else
    echo -e "${RED}✗${NC} requirements.txt no encontrado"
fi

# Check frontend dependencies
echo -n "Verificando dependencias del frontend... "
if [ -f "frontend/package.json" ]; then
    echo -e "${GREEN}✓${NC} package.json encontrado"
    
    if [ -d "frontend/node_modules" ]; then
        echo -e "${GREEN}✓${NC} node_modules instalado"
    else
        echo -e "${YELLOW}⚠${NC}  node_modules no encontrado (ejecuta: cd frontend && npm install)"
    fi
else
    echo -e "${RED}✗${NC} package.json no encontrado"
fi

# Check virtual environment
echo -n "Verificando entorno virtual de Python... "
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} venv encontrado"
else
    echo -e "${YELLOW}⚠${NC}  venv no encontrado (ejecuta: python3 -m venv venv)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Resumen:"
echo ""
echo "Para ejecutar localmente:"
echo ""
echo "1. Backend:"
echo "   cd backend"
echo "   source ../venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   uvicorn main:app --reload --port 8000"
echo ""
echo "2. Frontend (en otra terminal):"
echo "   cd frontend"
echo "   npm install"
echo "   npm run dev"
echo ""
echo "3. Visita: http://localhost:3000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
