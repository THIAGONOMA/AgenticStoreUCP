"""Servidor UCP da Livraria."""
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import structlog

from .discovery import get_discovery_profile, get_a2a_agent_card
from .routes.checkout import router as checkout_router
from .routes.books import router as books_router
from .routes.payments import router as payments_router
from ..db.database import init_databases, products_db, transactions_db
from ..mcp.http_server import router as mcp_router
from ..payments import get_psp_simulator
from ..config import settings

# Configurar logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Criar app
app = FastAPI(
    title="Livraria UCP",
    description="Servidor UCP da Livraria Virtual",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Inicializar banco de dados e PSP."""
    logger.info("Initializing databases...")
    await init_databases()
    await products_db.connect()
    await transactions_db.connect()
    
    # Inicializar PSP Simulator
    psp = get_psp_simulator()
    await psp.initialize()
    logger.info("PSP Simulator initialized")
    
    logger.info("UCP Server started", port=settings.ucp_port)


@app.on_event("shutdown")
async def shutdown():
    """Fechar conexoes."""
    await products_db.disconnect()
    await transactions_db.disconnect()
    logger.info("UCP Server stopped")


@app.get("/.well-known/ucp")
async def discovery(request: Request):
    """
    Discovery endpoint UCP.
    
    Retorna o perfil da loja com capacidades e payment handlers.
    """
    base_url = str(request.base_url).rstrip("/")
    profile = get_discovery_profile(base_url)
    
    logger.info("Discovery request", base_url=base_url)
    
    return profile.model_dump(by_alias=True, exclude_none=True)


@app.get("/.well-known/agent.json")
async def a2a_discovery(request: Request):
    """
    Discovery endpoint A2A (Agent-to-Agent Protocol).
    
    Retorna o AgentCard seguindo o formato do SDK oficial A2A.
    Permite que outros agentes descubram as capacidades deste agente.
    """
    base_url = str(request.base_url).rstrip("/")
    agent_card = get_a2a_agent_card(base_url)
    
    logger.info("A2A Discovery request", base_url=base_url)
    
    return agent_card


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "ucp-server"}


# Incluir routers
app.include_router(checkout_router, tags=["Checkout"])
app.include_router(books_router, prefix="/books", tags=["Books"])
app.include_router(payments_router)  # PSP Payments
app.include_router(mcp_router)  # MCP Tools


# Middleware para logar requests UCP
@app.middleware("http")
async def log_ucp_requests(request: Request, call_next):
    """Logar requests UCP."""
    ucp_agent = request.headers.get("UCP-Agent")
    if ucp_agent:
        logger.info(
            "UCP Request",
            method=request.method,
            path=request.url.path,
            agent=ucp_agent,
        )
    
    response = await call_next(request)
    return response
