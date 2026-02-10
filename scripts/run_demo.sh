#!/bin/bash

echo "=== Iniciando Livraria UCP Demo ==="
echo ""

# Verificar se setup foi feito
if [ ! -d "backend/.venv" ]; then
    echo "Erro: Execute ./scripts/setup.sh primeiro"
    exit 1
fi

# Iniciar UCP Server
echo "[1/3] Iniciando UCP Server na porta 8182..."
cd backend
source .venv/bin/activate
uvicorn src.ucp_server.server:app --host 0.0.0.0 --port 8182 &
UCP_PID=$!
cd ..

sleep 2

# Iniciar API Gateway
echo "[2/3] Iniciando API Gateway na porta 8000..."
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
cd ..

sleep 2

# Iniciar Frontend
echo "[3/3] Iniciando Frontend na porta 5173..."
cd frontend
npm run dev &
FE_PID=$!
cd ..

echo ""
echo "=== Servidores iniciados ==="
echo ""
echo "  UCP Server:  http://localhost:8182"
echo "  API Gateway: http://localhost:8000"
echo "  Frontend:    http://localhost:5173"
echo ""
echo "  UCP Discovery: http://localhost:8182/.well-known/ucp"
echo ""
echo "Pressione Ctrl+C para parar todos os servidores"

# Trap para limpar processos
cleanup() {
    echo ""
    echo "Parando servidores..."
    kill $UCP_PID $API_PID $FE_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# Aguardar
wait
