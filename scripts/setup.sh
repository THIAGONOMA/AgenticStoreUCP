#!/bin/bash
set -e

echo "=== Setup Livraria UCP ==="
echo ""

# Backend
echo "[1/4] Configurando backend..."
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copiar .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  -> Criado .env (edite com suas chaves de API)"
fi

# Criar diretorio de dados
mkdir -p data

cd ..

# User Agent
echo "[2/4] Configurando user_agent..."
cd user_agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copiar .env
if [ ! -f .env ]; then
    echo "OPENAI_API_KEY=sk-xxx" > .env
    echo "  -> Criado .env (edite com suas chaves de API)"
fi

cd ..

# Frontend
echo "[3/4] Configurando frontend..."
cd frontend
npm install

cd ..

# Importar dados
echo "[4/4] Importando catalogo de livros..."
cd backend
source .venv/bin/activate
python -m src.db.import_books

echo ""
echo "=== Setup completo! ==="
echo ""
echo "Para iniciar:"
echo "  ./scripts/run_demo.sh"
echo ""
