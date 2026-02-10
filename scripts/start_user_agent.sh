#!/bin/bash
# Script para iniciar o User Agent CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
USER_AGENT_DIR="$PROJECT_DIR/user_agent"

cd "$USER_AGENT_DIR"

# Verificar ambiente virtual
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

# Instalar dependencias
pip install -q -r requirements.txt

echo ""
echo "============================================"
echo "  User Agent CLI"
echo "============================================"
echo ""
echo "  Comandos disponiveis:"
echo "    python -m src.cli chat        - Chat interativo"
echo "    python -m src.cli discover    - Descobrir loja"
echo "    python -m src.cli search      - Buscar produtos"
echo "    python -m src.cli buy         - Comprar produto"
echo ""
echo "============================================"

# Iniciar CLI
python -m src.cli chat --store http://localhost:8182
