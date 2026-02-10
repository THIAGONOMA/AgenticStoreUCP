"""API Gateway - Entry point principal."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import structlog
import uuid
import httpx

from .config import settings
from .db.database import init_databases, products_db, transactions_db
from .db.products import products_repo
from .agents import store_agent_runner
from .agents.a2a import a2a_handler, A2AMessage
from .mcp.http_server import router as mcp_router

# URL do UCP Server
UCP_SERVER_URL = "http://localhost:8182"

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
    title="Livraria UCP - API Gateway",
    description="API Gateway para frontend e agentes",
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir router MCP para ferramentas
app.include_router(mcp_router, prefix="/api")


# WebSocket connections
class ConnectionManager:
    """Gerenciador de conexoes WebSocket."""
    
    def __init__(self):
        self.chat_connections: Dict[str, WebSocket] = {}
        self.a2a_connections: Dict[str, WebSocket] = {}
    
    async def connect_chat(self, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self.chat_connections[session_id] = websocket
        logger.info("Chat WebSocket connected", session=session_id)
        return session_id
    
    async def connect_a2a(self, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self.a2a_connections[session_id] = websocket
        logger.info("A2A WebSocket connected", session=session_id)
        return session_id
    
    def disconnect_chat(self, session_id: str):
        if session_id in self.chat_connections:
            del self.chat_connections[session_id]
            store_agent_runner.clear_session(session_id)
            logger.info("Chat WebSocket disconnected", session=session_id)
    
    def disconnect_a2a(self, session_id: str):
        if session_id in self.a2a_connections:
            del self.a2a_connections[session_id]
            logger.info("A2A WebSocket disconnected", session=session_id)
    
    async def broadcast_chat(self, message: dict):
        for ws in self.chat_connections.values():
            await ws.send_json(message)


manager = ConnectionManager()


@app.on_event("startup")
async def startup():
    """Inicializar."""
    logger.info("Initializing API Gateway...")
    await init_databases()
    await products_db.connect()
    await transactions_db.connect()
    logger.info("API Gateway started", port=settings.api_port)


@app.on_event("shutdown")
async def shutdown():
    """Fechar conexoes."""
    await products_db.disconnect()
    await transactions_db.disconnect()
    logger.info("API Gateway stopped")


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/.well-known/agent.json")
async def a2a_agent_discovery(request: Request):
    """
    Discovery endpoint A2A (Agent-to-Agent Protocol).
    
    Retorna o AgentCard seguindo o formato do SDK oficial A2A.
    """
    from .agents.a2a.adapters import get_store_agent_card
    
    base_url = str(request.base_url).rstrip("/")
    agent_card = get_store_agent_card()
    agent_card["url"] = f"{base_url}/a2a"
    
    logger.info("A2A Agent Discovery", base_url=base_url)
    
    return agent_card


@app.get("/api/books")
async def list_books(limit: int = 50, offset: int = 0):
    """Listar livros."""
    books = await products_repo.get_all(limit=limit, offset=offset)
    return {"books": [b.model_dump() for b in books]}


@app.get("/api/books/search")
async def search_books(q: str, category: str = None, limit: int = 20):
    """Buscar livros."""
    books = await products_repo.search(query=q, category=category, limit=limit)
    return {"books": [b.model_dump() for b in books], "query": q}


@app.get("/api/books/{book_id}")
async def get_book(book_id: str):
    """Obter livro."""
    book = await products_repo.get_by_id(book_id)
    if not book:
        return {"error": "Book not found"}, 404
    return book.model_dump()


# =============================================================================
# UCP PROXY - Encaminha requisições para o UCP Server
# =============================================================================

@app.post("/api/ucp/checkout-sessions")
async def create_checkout_session(request: Request):
    """Criar sessão de checkout via UCP Server."""
    body = await request.json()
    
    # Converter formato do frontend para formato UCP
    line_items = []
    for item in body.get("line_items", []):
        # Buscar detalhes do produto
        book = await products_repo.get_by_id(item.get("product_id"))
        if book:
            line_items.append({
                "item": {
                    "id": book.id,
                    "title": book.title
                },
                "quantity": item.get("quantity", 1)
            })
    
    buyer = body.get("buyer", {})
    ucp_payload = {
        "line_items": line_items,
        "buyer": {
            "full_name": buyer.get("name", "Cliente Web"),
            "email": buyer.get("email", "cliente@web.com")
        },
        "currency": "BRL"
    }
    
    logger.info("Creating UCP checkout session", items=len(line_items))
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{UCP_SERVER_URL}/checkout-sessions",
            json=ucp_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.error("UCP checkout failed", status=response.status_code, body=response.text)
            return Response(content=response.text, status_code=response.status_code)
        
        return response.json()


@app.get("/api/ucp/checkout-sessions/{session_id}")
async def get_checkout_session(session_id: str):
    """Obter sessão de checkout."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{UCP_SERVER_URL}/checkout-sessions/{session_id}")
        return Response(content=response.content, status_code=response.status_code)


@app.post("/api/ucp/checkout-sessions/{session_id}/complete")
async def complete_checkout(session_id: str, request: Request):
    """Completar checkout com pagamento."""
    body = await request.json()
    
    # Usar mock payment token
    payment_token = body.get("payment", {}).get("token", "success_token")
    
    logger.info("Completing UCP checkout", session=session_id)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{UCP_SERVER_URL}/checkout-sessions/{session_id}/complete",
            json={
                "payment": {
                    "token": payment_token
                }
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.error("UCP payment failed", status=response.status_code, body=response.text)
            return Response(content=response.text, status_code=response.status_code)
        
        return response.json()


# =============================================================================
# PAYMENTS PROXY - Encaminha requisições de pagamento para o UCP Server
# =============================================================================

@app.get("/api/payments/wallet")
async def get_wallet():
    """Obter informações da carteira virtual."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{UCP_SERVER_URL}/payments/wallet")
        return Response(
            content=response.content, 
            status_code=response.status_code,
            media_type="application/json"
        )


@app.post("/api/payments/wallet/token")
async def create_wallet_token(request: Request, wallet_id: str = "default_wallet"):
    """Criar token de pagamento."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{UCP_SERVER_URL}/payments/wallet/token",
            params={"wallet_id": wallet_id}
        )
        return Response(
            content=response.content, 
            status_code=response.status_code,
            media_type="application/json"
        )


@app.post("/api/payments/wallet/add-funds")
async def add_funds(request: Request):
    """Adicionar fundos na carteira (simulado)."""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{UCP_SERVER_URL}/payments/wallet/add-funds",
            json=body
        )
        return Response(
            content=response.content, 
            status_code=response.status_code,
            media_type="application/json"
        )


@app.get("/api/payments/transactions")
async def list_transactions(status: str = None):
    """Listar transações PSP."""
    url = f"{UCP_SERVER_URL}/payments/transactions"
    if status:
        url += f"?status={status}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return Response(
            content=response.content, 
            status_code=response.status_code,
            media_type="application/json"
        )


@app.get("/api/payments/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Obter detalhes de uma transação."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{UCP_SERVER_URL}/payments/transactions/{transaction_id}"
        )
        return Response(
            content=response.content, 
            status_code=response.status_code,
            media_type="application/json"
        )


@app.post("/api/payments/transactions/{transaction_id}/refund")
async def refund_transaction(transaction_id: str, request: Request):
    """Processar reembolso de uma transação."""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{UCP_SERVER_URL}/payments/transactions/{transaction_id}/refund",
            json=body
        )
        return Response(
            content=response.content, 
            status_code=response.status_code,
            media_type="application/json"
        )


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket para chat com Store Agents."""
    session_id = await manager.connect_chat(websocket)
    
    # Enviar boas-vindas
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "message": "Conectado ao chat da livraria!"
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            user_id = data.get("user_id")
            
            logger.info("Chat message received", session=session_id, message=message[:50])
            
            # Processar com Store Agents
            result = await store_agent_runner.process_message(
                session_id=session_id,
                message=message,
                user_id=user_id
            )
            
            response = {
                "type": "response",
                "session_id": session_id,
                "message": result["response"],
                "metadata": result.get("metadata", {}),
                "cart": {
                    "items": result.get("cart_items", []),
                    "total": result.get("cart_total", 0)
                },
                "search_results": result.get("search_results", []),
                "recommendations": result.get("recommendations", [])
            }
            
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        manager.disconnect_chat(session_id)


@app.websocket("/ws/a2a")
async def websocket_a2a(websocket: WebSocket):
    """WebSocket para comunicacao A2A com User Agents externos."""
    session_id = await manager.connect_a2a(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Converter para mensagem A2A
            message = A2AMessage.from_dict(data)
            
            logger.info(
                "A2A message received",
                session=session_id,
                type=message.type.value,
                action=message.action
            )
            
            # Processar com A2A Handler
            response = await a2a_handler.handle_message(message, session_id)
            
            await websocket.send_json(response.to_dict())
            
    except WebSocketDisconnect:
        manager.disconnect_a2a(session_id)


@app.post("/api/chat")
async def chat_message(data: dict):
    """Endpoint REST para chat (alternativa ao WebSocket)."""
    message = data.get("message", "")
    session_id = data.get("session_id", str(uuid.uuid4()))
    user_id = data.get("user_id")
    
    logger.info("Chat message (REST)", session=session_id, message=message[:50])
    
    # Processar com Store Agents
    result = await store_agent_runner.process_message(
        session_id=session_id,
        message=message,
        user_id=user_id
    )
    
    return {
        "session_id": session_id,
        "response": result["response"],
        "metadata": result.get("metadata", {}),
        "cart": {
            "items": result.get("cart_items", []),
            "total": result.get("cart_total", 0)
        },
        "search_results": result.get("search_results", []),
        "recommendations": result.get("recommendations", [])
    }


@app.post("/api/a2a")
async def a2a_request(data: dict):
    """Endpoint REST para A2A (alternativa ao WebSocket)."""
    session_id = data.get("session_id", str(uuid.uuid4()))
    
    message = A2AMessage.from_dict(data)
    
    logger.info("A2A request (REST)", action=message.action)
    
    response = await a2a_handler.handle_message(message, session_id)
    
    return response.to_dict()


@app.get("/api/a2a/agents")
async def list_connected_agents():
    """Listar agentes A2A conectados."""
    from .agents.a2a import a2a_protocol
    return {"agents": a2a_protocol.list_agents()}
