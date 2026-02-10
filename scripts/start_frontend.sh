#!/bin/bash
# Script para iniciar o frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_DIR/frontend"

cd "$FRONTEND_DIR"

# Verificar node_modules
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias do frontend..."
    npm install
fi

echo ""
echo "============================================"
echo "  Iniciando Frontend React"
echo "============================================"
echo ""
echo "  URL: http://localhost:5173"
echo ""
echo "  Pressione Ctrl+C para parar"
echo "============================================"

# Iniciar Vite
npm run dev
