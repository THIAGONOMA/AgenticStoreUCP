# =============================================================================
# Livraria UCP - Makefile
# =============================================================================
# Comandos para gerenciar os serviços da aplicação
# =============================================================================

.PHONY: help up down status logs install clean test up-ua-api down-ua-api demo demo-wallet demo-store-wallet seed reset-db

# Cores para output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m # No Color

# Diretórios
BACKEND_DIR := backend
FRONTEND_DIR := frontend
USER_AGENT_DIR := user_agent

# Portas
UCP_PORT := 8182
API_PORT := 8000
FRONTEND_PORT := 5173
USER_AGENT_PORT := 8001

# =============================================================================
# AJUDA
# =============================================================================

help: ## Mostra esta ajuda
	@echo ""
	@echo "$(GREEN)Livraria UCP - Comandos Disponíveis$(NC)"
	@echo "======================================"
	@echo ""
	@echo "$(YELLOW)Serviços:$(NC)"
	@echo "  make up              - Sobe todos os serviços"
	@echo "  make down            - Derruba todos os serviços"
	@echo "  make restart         - Reinicia todos os serviços"
	@echo "  make status          - Mostra status dos serviços"
	@echo ""
	@echo "$(YELLOW)Serviços Individuais:$(NC)"
	@echo "  make up-ucp          - Sobe UCP Server (porta $(UCP_PORT))"
	@echo "  make up-api          - Sobe API Gateway (porta $(API_PORT))"
	@echo "  make up-frontend     - Sobe Frontend (porta $(FRONTEND_PORT))"
	@echo "  make up-ua-api       - Sobe User Agent API (porta $(USER_AGENT_PORT))"
	@echo "  make down-ucp        - Derruba UCP Server"
	@echo "  make down-api        - Derruba API Gateway"
	@echo "  make down-frontend   - Derruba Frontend"
	@echo "  make down-ua-api     - Derruba User Agent API"
	@echo ""
	@echo "$(YELLOW)Desenvolvimento:$(NC)"
	@echo "  make install         - Instala todas as dependências"
	@echo "  make seed            - Importa livros e cupons para o banco"
	@echo "  make reset-db        - Limpa e recria os bancos de dados"
	@echo "  make test            - Executa todos os testes"
	@echo "  make logs            - Mostra logs dos serviços"
	@echo "  make clean           - Limpa arquivos temporários"
	@echo ""
	@echo "$(YELLOW)User Agent CLI:$(NC)"
	@echo "  make ua-discover     - Descobre perfil UCP da loja"
	@echo "  make ua-search       - Busca livros (ex: make ua-search Q=python)"
	@echo "  make ua-buy          - Compra livro (ex: make ua-buy ID=book_001)"
	@echo "  make ua-chat         - Chat interativo com a loja"
	@echo ""
	@echo "$(YELLOW)Demonstrações:$(NC)"
	@echo "  make demo            - Executa demo completa do User Agent"
	@echo "  make demo-ap2        - Demo do Agent Payments Protocol (AP2)"
	@echo "  make demo-ucp        - Mostra perfil UCP da loja"
	@echo "  make demo-wallet     - Mostra carteira pessoal (User Agent)"
	@echo "  make demo-store-wallet - Mostra carteira da loja (PSP)"
	@echo ""

# =============================================================================
# SERVIÇOS - TODOS
# =============================================================================

up: up-ucp up-api up-ua-api up-frontend ## Sobe todos os serviços
	@echo ""
	@echo "$(GREEN)✅ Todos os serviços iniciados!$(NC)"
	@echo ""
	@echo "  UCP Server:      http://localhost:$(UCP_PORT)"
	@echo "  API Gateway:     http://localhost:$(API_PORT)"
	@echo "  User Agent API:  http://localhost:$(USER_AGENT_PORT)"
	@echo "  Frontend:        http://localhost:$(FRONTEND_PORT)"
	@echo ""

down: ## Derruba todos os serviços
	@echo "$(YELLOW)Derrubando serviços...$(NC)"
	@pkill -f "uvicorn src.ucp_server" 2>/dev/null || true
	@pkill -f "uvicorn src.main" 2>/dev/null || true
	@pkill -f "uvicorn user_agent.src.main" 2>/dev/null || true
	@pkill -f "vite" 2>/dev/null || true
	@sleep 1
	@echo "$(GREEN)✅ Todos os serviços derrubados$(NC)"

restart: down up ## Reinicia todos os serviços

status: ## Mostra status dos serviços
	@echo ""
	@echo "$(YELLOW)Status dos Serviços$(NC)"
	@echo "===================="
	@echo ""
	@if lsof -i :$(UCP_PORT) > /dev/null 2>&1; then \
		echo "$(GREEN)● UCP Server ($(UCP_PORT))$(NC)      - Rodando"; \
	else \
		echo "$(RED)○ UCP Server ($(UCP_PORT))$(NC)      - Parado"; \
	fi
	@if lsof -i :$(API_PORT) > /dev/null 2>&1; then \
		echo "$(GREEN)● API Gateway ($(API_PORT))$(NC)     - Rodando"; \
	else \
		echo "$(RED)○ API Gateway ($(API_PORT))$(NC)     - Parado"; \
	fi
	@if lsof -i :$(USER_AGENT_PORT) > /dev/null 2>&1; then \
		echo "$(GREEN)● User Agent API ($(USER_AGENT_PORT))$(NC)  - Rodando"; \
	else \
		echo "$(RED)○ User Agent API ($(USER_AGENT_PORT))$(NC)  - Parado"; \
	fi
	@if lsof -i :$(FRONTEND_PORT) > /dev/null 2>&1; then \
		echo "$(GREEN)● Frontend ($(FRONTEND_PORT))$(NC)       - Rodando"; \
	else \
		echo "$(RED)○ Frontend ($(FRONTEND_PORT))$(NC)       - Parado"; \
	fi
	@echo ""

# =============================================================================
# SERVIÇOS - INDIVIDUAIS
# =============================================================================

up-ucp: ## Sobe UCP Server
	@echo "$(YELLOW)Iniciando UCP Server na porta $(UCP_PORT)...$(NC)"
	@if lsof -i :$(UCP_PORT) > /dev/null 2>&1; then \
		echo "$(RED)Porta $(UCP_PORT) já em uso$(NC)"; \
	else \
		cd $(BACKEND_DIR) && ./venv/bin/uvicorn src.ucp_server.server:app --host 0.0.0.0 --port $(UCP_PORT) & \
		sleep 2; \
		echo "$(GREEN)✅ UCP Server iniciado$(NC)"; \
	fi

up-api: ## Sobe API Gateway
	@echo "$(YELLOW)Iniciando API Gateway na porta $(API_PORT)...$(NC)"
	@if lsof -i :$(API_PORT) > /dev/null 2>&1; then \
		echo "$(RED)Porta $(API_PORT) já em uso$(NC)"; \
	else \
		cd $(BACKEND_DIR) && ./venv/bin/uvicorn src.main:app --host 0.0.0.0 --port $(API_PORT) & \
		sleep 2; \
		echo "$(GREEN)✅ API Gateway iniciado$(NC)"; \
	fi

up-frontend: ## Sobe Frontend
	@echo "$(YELLOW)Iniciando Frontend na porta $(FRONTEND_PORT)...$(NC)"
	@if lsof -i :$(FRONTEND_PORT) > /dev/null 2>&1; then \
		echo "$(RED)Porta $(FRONTEND_PORT) já em uso$(NC)"; \
	else \
		cd $(FRONTEND_DIR) && npm run dev & \
		sleep 3; \
		echo "$(GREEN)✅ Frontend iniciado$(NC)"; \
	fi

down-ucp: ## Derruba UCP Server
	@pkill -f "uvicorn src.ucp_server" 2>/dev/null && \
		echo "$(GREEN)✅ UCP Server derrubado$(NC)" || \
		echo "$(YELLOW)UCP Server não estava rodando$(NC)"

down-api: ## Derruba API Gateway
	@pkill -f "uvicorn src.main" 2>/dev/null && \
		echo "$(GREEN)✅ API Gateway derrubado$(NC)" || \
		echo "$(YELLOW)API Gateway não estava rodando$(NC)"

down-frontend: ## Derruba Frontend
	@pkill -f "vite" 2>/dev/null && \
		echo "$(GREEN)✅ Frontend derrubado$(NC)" || \
		echo "$(YELLOW)Frontend não estava rodando$(NC)"

up-ua-api: ## Sobe User Agent API (carteira pessoal)
	@echo "$(YELLOW)Iniciando User Agent API na porta $(USER_AGENT_PORT)...$(NC)"
	@if lsof -i :$(USER_AGENT_PORT) > /dev/null 2>&1; then \
		echo "$(RED)Porta $(USER_AGENT_PORT) já em uso$(NC)"; \
	else \
		cd $(USER_AGENT_DIR) && ./venv/bin/uvicorn src.main:app --host 0.0.0.0 --port $(USER_AGENT_PORT) & \
		sleep 2; \
		echo "$(GREEN)✅ User Agent API iniciado$(NC)"; \
	fi

down-ua-api: ## Derruba User Agent API
	@lsof -ti :$(USER_AGENT_PORT) | xargs kill -9 2>/dev/null && \
		echo "$(GREEN)✅ User Agent API derrubado$(NC)" || \
		echo "$(YELLOW)User Agent API não estava rodando$(NC)"

# =============================================================================
# DESENVOLVIMENTO
# =============================================================================

install: install-backend install-frontend install-user-agent ## Instala todas as dependências
	@echo "$(GREEN)✅ Todas as dependências instaladas$(NC)"

install-backend: ## Instala dependências do backend
	@echo "$(YELLOW)Instalando dependências do backend...$(NC)"
	@cd $(BACKEND_DIR) && \
		python3 -m venv venv && \
		./venv/bin/pip install -q -r requirements.txt
	@echo "$(GREEN)✅ Backend instalado$(NC)"

install-frontend: ## Instala dependências do frontend
	@echo "$(YELLOW)Instalando dependências do frontend...$(NC)"
	@cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)✅ Frontend instalado$(NC)"

install-user-agent: ## Instala dependências do user agent
	@echo "$(YELLOW)Instalando dependências do user agent...$(NC)"
	@cd $(USER_AGENT_DIR) && \
		python3 -m venv venv && \
		./venv/bin/pip install -q -r requirements.txt
	@echo "$(GREEN)✅ User Agent instalado$(NC)"

test: test-backend test-ws ## Executa todos os testes
	@echo "$(GREEN)✅ Todos os testes executados$(NC)"

test-backend: ## Executa testes do backend
	@echo "$(YELLOW)Executando testes do backend...$(NC)"
	@cd $(BACKEND_DIR) && ./venv/bin/python -m pytest tests/ -v 2>/dev/null || \
		echo "$(YELLOW)Pytest não instalado ou sem testes$(NC)"

test-ws: ## Executa testes WebSocket
	@echo "$(YELLOW)Executando testes WebSocket...$(NC)"
	@cd $(BACKEND_DIR) && ./venv/bin/python tests/test_websocket.py

logs: ## Mostra processos rodando
	@echo "$(YELLOW)Processos da aplicação:$(NC)"
	@ps aux | grep -E "(uvicorn|vite)" | grep -v grep || echo "Nenhum processo rodando"

clean: ## Limpa arquivos temporários
	@echo "$(YELLOW)Limpando arquivos temporários...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Limpeza concluída$(NC)"

seed: ## Importa livros e cupons para o banco de dados
	@echo "$(YELLOW)Importando dados de exemplo...$(NC)"
	@cd $(BACKEND_DIR) && ./venv/bin/python -m src.db.import_books
	@echo "$(GREEN)✅ Dados importados$(NC)"

reset-db: ## Limpa e recria os bancos de dados
	@echo "$(YELLOW)Resetando bancos de dados...$(NC)"
	@find $(BACKEND_DIR) -name "*.db" -type f -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Bancos de dados removidos$(NC)"
	@echo "$(YELLOW)Reiniciando servidores e importando dados...$(NC)"
	@$(MAKE) down
	@$(MAKE) seed
	@$(MAKE) up

# =============================================================================
# USER AGENT
# =============================================================================

# URL padrão da loja UCP
STORE_URL := http://localhost:8182

ua-discover: ## Descobre perfil UCP da loja
	@cd $(USER_AGENT_DIR) && ./venv/bin/python -m src.cli discover $(STORE_URL)

ua-search: ## Busca livros (use Q=termo)
	@cd $(USER_AGENT_DIR) && ./venv/bin/python -m src.cli search "$(Q)" --store $(STORE_URL)

ua-buy: ## Compra livro (use ID=book_id)
	@cd $(USER_AGENT_DIR) && ./venv/bin/python -m src.cli buy "$(ID)" --store $(STORE_URL)

ua-chat: ## Chat interativo com a loja
	@cd $(USER_AGENT_DIR) && ./venv/bin/python -m src.cli chat --store $(STORE_URL)

# =============================================================================
# DEMONSTRAÇÕES
# =============================================================================

demo-ap2: ## Demonstração do Agent Payments Protocol (AP2)
	@cd $(BACKEND_DIR) && ./venv/bin/python scripts/demo_ap2.py

demo-ucp: ## Mostra perfil UCP da loja
	@curl -s http://localhost:$(UCP_PORT)/.well-known/ucp | python3 -m json.tool

demo: ## Executa demo completa do User Agent
	@echo "$(YELLOW)Executando demo do User Agent...$(NC)"
	@cd $(USER_AGENT_DIR) && ./venv/bin/python demo.py

demo-wallet: ## Mostra saldo da carteira pessoal (User Agent)
	@echo "$(YELLOW)Carteira Pessoal do User Agent:$(NC)"
	@curl -s http://localhost:$(USER_AGENT_PORT)/wallet 2>/dev/null | python3 -m json.tool || \
		echo "$(RED)User Agent API não está rodando. Use: make up-ua-api$(NC)"

demo-store-wallet: ## Mostra saldo da carteira da loja
	@echo "$(YELLOW)Carteira da Loja (PSP):$(NC)"
	@curl -s http://localhost:$(API_PORT)/api/payments/wallet 2>/dev/null | python3 -m json.tool || \
		echo "$(RED)API Gateway não está rodando. Use: make up-api$(NC)"

# =============================================================================
# ATALHOS
# =============================================================================

dev: up ## Alias para 'make up'
stop: down ## Alias para 'make down'
s: status ## Alias para 'make status'
