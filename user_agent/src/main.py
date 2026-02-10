"""User Agent API Server.

Servidor FastAPI para expor a carteira pessoal e outras funcionalidades.
Roda na porta 8001 (separado do backend).
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .api import wallet_router
from .wallet import get_wallet

logger = structlog.get_logger()

# Criar app FastAPI
app = FastAPI(
    title="User Agent API",
    description="API do User Agent - Carteira Pessoal e Ferramentas",
    version="1.0.0",
)

# Configurar CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================================
# Registrar Routers
# =========================================================================

app.include_router(wallet_router)


# =========================================================================
# Endpoints Raiz
# =========================================================================

@app.get("/")
async def root():
    """Informacoes basicas da API do User Agent."""
    wallet = get_wallet()
    return {
        "name": "User Agent API",
        "version": "1.0.0",
        "wallet": {
            "id": wallet.wallet_id,
            "balance_formatted": wallet.balance_formatted,
        },
        "endpoints": {
            "wallet": "/wallet",
            "wallet_token": "/wallet/token",
            "add_funds": "/wallet/add-funds",
            "transactions": "/wallet/transactions",
        }
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


# =========================================================================
# Startup/Shutdown
# =========================================================================

@app.on_event("startup")
async def startup():
    """Inicializar recursos."""
    wallet = get_wallet()
    logger.info(
        "User Agent API starting",
        wallet_id=wallet.wallet_id,
        balance=wallet.balance_formatted
    )


@app.on_event("shutdown")
async def shutdown():
    """Limpar recursos."""
    logger.info("User Agent API shutting down")


# =========================================================================
# Entry Point
# =========================================================================

def run():
    """Executar o servidor."""
    uvicorn.run(
        "user_agent.src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    run()
