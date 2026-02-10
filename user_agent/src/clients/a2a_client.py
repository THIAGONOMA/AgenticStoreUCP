"""Cliente A2A para User Agent - Comunicacao bidirecional com Store Agents."""
from typing import Dict, Any, Optional, Callable, Awaitable, List
from dataclasses import dataclass, field
import asyncio
import json
import uuid
import time
import structlog
import httpx
import websockets
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed

from ..config import settings

logger = structlog.get_logger()


@dataclass
class A2AResponse:
    """Resposta de uma requisicao A2A."""
    success: bool
    action: str
    data: Dict[str, Any]
    error: Optional[str] = None
    message_id: Optional[str] = None


@dataclass
class A2AMessage:
    """Mensagem A2A."""
    type: str
    action: str
    payload: Dict[str, Any]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: int = field(default_factory=lambda: int(time.time()))


class A2AClient:
    """
    Cliente A2A para comunicacao com Store Agents.
    
    Conecta via WebSocket e mantem comunicacao bidirecional.
    Suporta reconexao automatica e keep-alive.
    """
    
    def __init__(
        self, 
        store_url: str, 
        agent_id: str = None,
        auto_reconnect: bool = True,
        reconnect_interval: float = None,
        ping_interval: float = None
    ):
        """
        Inicializar cliente.
        
        Args:
            store_url: URL do WebSocket A2A (ws://...)
            agent_id: ID do agente (gerado se nao fornecido)
            auto_reconnect: Reconectar automaticamente se desconectar
            reconnect_interval: Intervalo entre tentativas de reconexao
            ping_interval: Intervalo de ping para keep-alive
        """
        self.store_url = self._normalize_url(store_url)
        self.agent_id = agent_id or f"user-agent-{uuid.uuid4().hex[:8]}"
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval or settings.a2a_reconnect_interval
        self.ping_interval = ping_interval or settings.a2a_ping_interval
        
        self.ws: Optional[WebSocketClientProtocol] = None
        self.connected = False
        self.store_info: Dict[str, Any] = {}
        
        # URL base HTTP para Agent Card
        self._base_http_url = self._get_base_http_url(store_url)
        
        # Handlers
        self._message_handlers: Dict[str, Callable] = {}
        self._pending_requests: Dict[str, asyncio.Future] = {}
        
        # Tasks de background
        self._ping_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_connect: Optional[Callable[[], Awaitable[None]]] = None
        self.on_disconnect: Optional[Callable[[], Awaitable[None]]] = None
        self.on_message: Optional[Callable[[Dict], Awaitable[None]]] = None
    
    def _normalize_url(self, url: str) -> str:
        """Normalizar URL para WebSocket."""
        ws_url = url.replace("http://", "ws://").replace("https://", "wss://")
        
        # Se for UCP Server (8182), redirecionar para API Gateway (8000)
        if ":8182" in ws_url:
            ws_url = ws_url.replace(":8182", ":8000")
        
        if not ws_url.endswith("/ws/a2a"):
            ws_url = f"{ws_url.rstrip('/')}/ws/a2a"
        
        return ws_url
    
    def _get_base_http_url(self, url: str) -> str:
        """Obter URL base HTTP a partir de qualquer URL."""
        # Converter ws:// para http://
        http_url = url.replace("ws://", "http://").replace("wss://", "https://")
        
        # Remover paths conhecidos
        for path in ["/ws/a2a", "/ws", "/a2a"]:
            if http_url.endswith(path):
                http_url = http_url[:-len(path)]
        
        return http_url.rstrip("/")
    
    async def get_agent_card(self, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """
        Obter Agent Card via HTTP (sem WebSocket).
        
        Tenta os endpoints padrao:
        - /.well-known/agent.json
        - /.well-known/agent-card.json
        
        Returns:
            Dict com Agent Card ou None se falhar
        """
        endpoints = [
            "/.well-known/agent.json",
            "/.well-known/agent-card.json"
        ]
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            for endpoint in endpoints:
                url = f"{self._base_http_url}{endpoint}"
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        card = response.json()
                        logger.info("Agent card retrieved", url=url, name=card.get("name"))
                        return card
                except Exception as e:
                    logger.debug(f"Agent card not found at {url}: {e}")
                    continue
        
        logger.warning("Agent card not found", base_url=self._base_http_url)
        return None
    
    async def connect(self, timeout: float = 10.0) -> bool:
        """
        Conectar ao servidor A2A.
        
        Returns:
            True se conectou com sucesso
        """
        try:
            self.ws = await asyncio.wait_for(
                websockets.connect(self.store_url),
                timeout=timeout
            )
            
            # Enviar mensagem de conexao
            connect_msg = {
                "type": "a2a.connect",
                "message_id": str(uuid.uuid4()),
                "agent_id": self.agent_id,
                "payload": {
                    "agent_profile": {
                        "agent_id": self.agent_id,
                        "name": "User Agent",
                        "version": "2.0",
                        "capabilities": ["search", "checkout", "recommend", "chat"]
                    }
                }
            }
            
            await self.ws.send(json.dumps(connect_msg))
            
            # Aguardar resposta
            response = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            data = json.loads(response)
            
            if data.get("status") == "connected":
                self.connected = True
                self.store_info = data.get("store_info", {})
                
                logger.info(
                    "A2A connected",
                    agent_id=self.agent_id,
                    store=self.store_url,
                    store_name=self.store_info.get("name")
                )
                
                # Iniciar tasks de background
                self._start_background_tasks()
                
                # Callback
                if self.on_connect:
                    await self.on_connect()
                
                return True
            
            logger.warning("A2A connection rejected", response=data)
            return False
            
        except asyncio.TimeoutError:
            logger.error("A2A connection timeout", url=self.store_url)
            return False
        except Exception as e:
            logger.error("A2A connection failed", error=str(e), url=self.store_url)
            return False
    
    def _start_background_tasks(self):
        """Iniciar tasks de background."""
        # Task de ping
        if self.ping_interval > 0:
            self._ping_task = asyncio.create_task(self._ping_loop())
    
    async def _ping_loop(self):
        """Loop de ping para manter conexao."""
        while self.connected:
            try:
                await asyncio.sleep(self.ping_interval)
                if self.connected and self.ws:
                    await self.ping()
            except Exception as e:
                logger.warning("Ping failed", error=str(e))
                if self.auto_reconnect:
                    await self._try_reconnect()
    
    async def _try_reconnect(self):
        """Tentar reconectar."""
        if not self.auto_reconnect:
            return
        
        logger.info("Attempting reconnection", url=self.store_url)
        self.connected = False
        
        for attempt in range(3):
            await asyncio.sleep(self.reconnect_interval * (attempt + 1))
            
            if await self.connect():
                logger.info("Reconnected successfully", attempt=attempt + 1)
                return
        
        logger.error("Reconnection failed after 3 attempts")
    
    async def disconnect(self):
        """Desconectar do servidor."""
        self.connected = False
        
        # Cancelar tasks
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
        
        if self.ws:
            try:
                disconnect_msg = {
                    "type": "a2a.disconnect",
                    "message_id": str(uuid.uuid4()),
                    "agent_id": self.agent_id
                }
                await self.ws.send(json.dumps(disconnect_msg))
                await self.ws.close()
            except:
                pass
            finally:
                self.ws = None
        
        # Callback
        if self.on_disconnect:
            await self.on_disconnect()
        
        logger.info("A2A disconnected", agent_id=self.agent_id)
    
    async def request(
        self,
        action: str,
        payload: Dict[str, Any],
        timeout: float = 30.0
    ) -> A2AResponse:
        """
        Enviar requisicao A2A e aguardar resposta.
        
        Args:
            action: Acao a executar
            payload: Dados da requisicao
            timeout: Timeout em segundos
            
        Returns:
            A2AResponse com resultado
        """
        if not self.connected or not self.ws:
            return A2AResponse(
                success=False,
                action=action,
                data={},
                error="Not connected"
            )
        
        message_id = str(uuid.uuid4())
        
        request_msg = {
            "type": "a2a.request",
            "message_id": message_id,
            "timestamp": int(time.time()),
            "agent_id": self.agent_id,
            "action": action,
            "payload": payload
        }
        
        try:
            await self.ws.send(json.dumps(request_msg))
            
            # Aguardar resposta
            response = await asyncio.wait_for(
                self.ws.recv(),
                timeout=timeout
            )
            
            data = json.loads(response)
            
            # Callback de mensagem
            if self.on_message:
                await self.on_message(data)
            
            if data.get("status") == "error":
                return A2AResponse(
                    success=False,
                    action=action,
                    data={},
                    error=data.get("error", "Unknown error"),
                    message_id=message_id
                )
            
            return A2AResponse(
                success=True,
                action=action,
                data=data.get("payload", data),
                message_id=message_id
            )
            
        except asyncio.TimeoutError:
            logger.warning("A2A request timeout", action=action)
            return A2AResponse(
                success=False,
                action=action,
                data={},
                error="Request timeout",
                message_id=message_id
            )
        except ConnectionClosed:
            logger.warning("Connection closed during request")
            if self.auto_reconnect:
                await self._try_reconnect()
            return A2AResponse(
                success=False,
                action=action,
                data={},
                error="Connection closed",
                message_id=message_id
            )
        except Exception as e:
            logger.error("A2A request failed", action=action, error=str(e))
            return A2AResponse(
                success=False,
                action=action,
                data={},
                error=str(e),
                message_id=message_id
            )
    
    # =========================================================================
    # Helper Methods - Acoes Especificas
    # =========================================================================
    
    async def search(self, query: str, limit: int = 20) -> A2AResponse:
        """Buscar produtos."""
        return await self.request("search", {"query": query, "limit": limit})
    
    async def get_products(self, category: str = None, limit: int = 20) -> A2AResponse:
        """Listar produtos."""
        payload = {"limit": limit}
        if category:
            payload["category"] = category
        return await self.request("get_products", payload)
    
    async def get_product(self, product_id: str) -> A2AResponse:
        """Obter detalhes de um produto."""
        return await self.request("get_product", {"product_id": product_id})
    
    async def get_categories(self) -> A2AResponse:
        """Listar categorias."""
        return await self.request("list_categories", {})
    
    async def add_to_cart(self, product_id: str, quantity: int = 1) -> A2AResponse:
        """Adicionar produto ao carrinho."""
        return await self.request("add_to_cart", {
            "product_id": product_id,
            "quantity": quantity
        })
    
    async def remove_from_cart(self, product_id: str) -> A2AResponse:
        """Remover produto do carrinho."""
        return await self.request("remove_from_cart", {"product_id": product_id})
    
    async def get_cart(self) -> A2AResponse:
        """Obter carrinho atual."""
        return await self.request("get_cart", {})
    
    async def apply_discount(self, code: str) -> A2AResponse:
        """Aplicar codigo de desconto."""
        return await self.request("apply_discount", {"code": code})
    
    async def create_order(
        self,
        items: List[Dict[str, Any]],
        buyer: Dict[str, Any],
        discount_code: str = None
    ) -> A2AResponse:
        """Criar pedido."""
        payload = {
            "items": items,
            "buyer": buyer
        }
        if discount_code:
            payload["discount_code"] = discount_code
        return await self.request("create_order", payload)
    
    async def checkout(
        self,
        buyer: Dict[str, Any],
        payment_method: str = "mock",
        mandate_jwt: str = None
    ) -> A2AResponse:
        """Finalizar checkout."""
        payload = {
            "buyer": buyer,
            "payment_method": payment_method
        }
        if mandate_jwt:
            payload["mandate_jwt"] = mandate_jwt
        return await self.request("checkout", payload)
    
    async def get_recommendations(
        self,
        book_id: str = None,
        category: str = None,
        limit: int = 5
    ) -> A2AResponse:
        """Obter recomendacoes."""
        payload = {"limit": limit}
        if book_id:
            payload["book_id"] = book_id
        if category:
            payload["category"] = category
        return await self.request("recommend", payload)
    
    async def chat(self, message: str) -> A2AResponse:
        """Enviar mensagem de chat."""
        return await self.request("chat", {"message": message})
    
    async def ping(self) -> A2AResponse:
        """Ping para verificar conexao."""
        return await self.request("ping", {})
    
    # =========================================================================
    # Context Manager
    # =========================================================================
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


class A2AClientPool:
    """
    Pool de clientes A2A para multiplas lojas.
    """
    
    def __init__(self):
        self._clients: Dict[str, A2AClient] = {}
    
    async def get_client(self, store_url: str) -> A2AClient:
        """Obter ou criar cliente para uma loja."""
        if store_url not in self._clients:
            client = A2AClient(store_url)
            if await client.connect():
                self._clients[store_url] = client
            else:
                raise ConnectionError(f"Failed to connect to {store_url}")
        
        return self._clients[store_url]
    
    async def disconnect_all(self):
        """Desconectar todos os clientes."""
        for client in self._clients.values():
            await client.disconnect()
        self._clients.clear()
    
    def list_connected(self) -> List[str]:
        """Listar lojas conectadas."""
        return [url for url, client in self._clients.items() if client.connected]


# Instancia global do pool
_a2a_pool: Optional[A2AClientPool] = None


def get_a2a_pool() -> A2AClientPool:
    """Obter pool global de clientes A2A."""
    global _a2a_pool
    if _a2a_pool is None:
        _a2a_pool = A2AClientPool()
    return _a2a_pool
