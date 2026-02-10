#!/bin/bash
# Script para iniciar o backend completo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

cd "$BACKEND_DIR"

# Verificar ambiente virtual
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

# Instalar dependencias
pip install -q -r requirements.txt

# Importar dados se necessario
if [ ! -f "data/products.db" ]; then
    echo "Importando dados iniciais..."
    python -m src.db.import_books
fi

# Iniciar servidores em background
echo "Iniciando UCP Server na porta 8182..."
uvicorn src.ucp_server.server:app --host 0.0.0.0 --port 8182 &
UCP_PID=$!

sleep 2

echo "Iniciando API Gateway na porta 8000..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo ""
echo "============================================"
echo "  Backend iniciado com sucesso!"
echo "============================================"
echo ""
echo "  UCP Server:   http://localhost:8182"
echo "  API Gateway:  http://localhost:8000"
echo "  Discovery:    http://localhost:8182/.well-known/ucp"
echo ""
echo "  PIDs: UCP=$UCP_PID, API=$API_PID"
echo ""
echo "  Pressione Ctrl+C para parar"
echo "============================================"

# Cleanup ao sair
trap "kill $UCP_PID $API_PID 2>/dev/null" EXIT

# Aguardar
wait
