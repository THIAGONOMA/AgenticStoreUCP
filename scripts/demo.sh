#!/bin/bash
# Script de demonstracao completa do projeto

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║        🏪  LIVRARIA VIRTUAL UCP - DEMONSTRACAO  🏪          ║"
echo "║                                                              ║"
echo "║     Universal Commerce Protocol + Agent-to-Agent + AP2      ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Funcao para verificar porta
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Setup Backend
echo -e "${YELLOW}[1/4] Configurando Backend...${NC}"
cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

# Importar dados
if [ ! -f "data/products.db" ]; then
    echo "  Importando catalogo de livros..."
    python -m src.db.import_books
fi

echo -e "${GREEN}  ✓ Backend configurado${NC}"

# Setup Frontend
echo -e "${YELLOW}[2/4] Configurando Frontend...${NC}"
cd "$PROJECT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    npm install --silent
fi

echo -e "${GREEN}  ✓ Frontend configurado${NC}"

# Iniciar servidores
echo -e "${YELLOW}[3/4] Iniciando servidores...${NC}"

cd "$PROJECT_DIR/backend"
source venv/bin/activate

# UCP Server
if ! check_port 8182; then
    uvicorn src.ucp_server.server:app --host 0.0.0.0 --port 8182 &
    UCP_PID=$!
    sleep 2
    echo -e "${GREEN}  ✓ UCP Server iniciado (porta 8182)${NC}"
else
    echo -e "${YELLOW}  ! UCP Server ja esta rodando${NC}"
fi

# API Gateway
if ! check_port 8000; then
    uvicorn src.main:app --host 0.0.0.0 --port 8000 &
    API_PID=$!
    sleep 2
    echo -e "${GREEN}  ✓ API Gateway iniciado (porta 8000)${NC}"
else
    echo -e "${YELLOW}  ! API Gateway ja esta rodando${NC}"
fi

# Frontend
cd "$PROJECT_DIR/frontend"
if ! check_port 5173; then
    npm run dev &
    FRONTEND_PID=$!
    sleep 3
    echo -e "${GREEN}  ✓ Frontend iniciado (porta 5173)${NC}"
else
    echo -e "${YELLOW}  ! Frontend ja esta rodando${NC}"
fi

# Informacoes finais
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}                    ${GREEN}DEMO PRONTA!${NC}                             ${BLUE}║${NC}"
echo -e "${BLUE}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}Frontend:${NC}     http://localhost:5173                       ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}UCP Server:${NC}   http://localhost:8182                       ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}API Gateway:${NC}  http://localhost:8000                       ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}Discovery:${NC}    http://localhost:8182/.well-known/ucp       ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}Cenarios de Teste:${NC}                                        ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  1. Abra http://localhost:5173 no navegador                 ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  2. Navegue pelo catalogo e adicione livros ao carrinho     ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  3. Clique no icone de chat para conversar com o agente     ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  4. Finalize uma compra pelo carrinho                       ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  Para User Agent CLI:                                        ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}    ./scripts/start_user_agent.sh                             ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC}  Pressione ${RED}Ctrl+C${NC} para parar todos os servicos              ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}Parando servicos...${NC}"
    [ ! -z "$UCP_PID" ] && kill $UCP_PID 2>/dev/null
    [ ! -z "$API_PID" ] && kill $API_PID 2>/dev/null
    [ ! -z "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Servicos parados.${NC}"
    exit 0
}

trap cleanup INT TERM

# Aguardar
wait
