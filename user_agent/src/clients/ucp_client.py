"""Cliente UCP para User Agent."""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class UCPProfile:
    """Perfil UCP de uma loja."""
    name: str
    version: str
    base_url: str
    capabilities: Dict[str, Any]
    payment_handlers: List[str]
    
    
@dataclass
class CheckoutSession:
    """Sessao de checkout."""
    id: str
    status: str
    total: int
    currency: str
    line_items: List[Dict[str, Any]]
    raw_data: Dict[str, Any]


class UCPClient:
    """
    Cliente UCP para User Agent.
    
    Implementa o protocolo UCP para descoberta e checkout.
    """
    
    def __init__(self, store_url: str):
        """
        Inicializar cliente.
        
        Args:
            store_url: URL base da loja
        """
        self.store_url = store_url.rstrip("/")
        self.profile: Optional[UCPProfile] = None
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def discover(self) -> Optional[UCPProfile]:
        """
        Descobrir capacidades da loja via UCP.
        
        Returns:
            UCPProfile se sucesso
        """
        try:
            response = await self._client.get(
                f"{self.store_url}/.well-known/ucp"
            )
            response.raise_for_status()
            
            data = response.json()
            
            self.profile = UCPProfile(
                name=data.get("name", "Unknown Store"),
                version=data.get("ucp_version", "1.0"),
                base_url=self.store_url,
                capabilities=data.get("capabilities", {}),
                payment_handlers=data.get("payment", {}).get("handlers", [])
            )
            
            logger.info(
                "UCP discovery complete",
                store=self.profile.name,
                version=self.profile.version
            )
            
            return self.profile
            
        except Exception as e:
            logger.error("UCP discovery failed", url=self.store_url, error=str(e))
            return None
    
    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Buscar produtos na loja.
        
        Args:
            query: Termo de busca
            category: Filtro de categoria
            limit: Maximo de resultados
            
        Returns:
            Lista de produtos
        """
        try:
            params = {"search": query, "limit": limit}
            if category:
                params["category"] = category
            
            response = await self._client.get(
                f"{self.store_url}/books",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            # Handle both list (UCP Server) and dict (API Gateway) responses
            if isinstance(data, list):
                return data
            return data.get("books", [])
            
        except Exception as e:
            logger.error("Product search failed", error=str(e))
            return []
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Obter detalhes de um produto."""
        try:
            response = await self._client.get(
                f"{self.store_url}/books/{product_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Get product failed", error=str(e))
            return None
    
    async def create_checkout(
        self,
        line_items: List[Dict[str, Any]],
        buyer_info: Dict[str, Any]
    ) -> Optional[CheckoutSession]:
        """
        Criar sessao de checkout.
        
        Args:
            line_items: Lista de itens (product_id, quantity)
            buyer_info: Informacoes do comprador
            
        Returns:
            CheckoutSession se sucesso
        """
        try:
            response = await self._client.post(
                f"{self.store_url}/checkout-sessions",
                json={
                    "line_items": line_items,
                    "buyer": buyer_info,
                    "currency": "BRL"
                },
                headers=self._get_ucp_headers()
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extrair total
            total = 0
            for t in data.get("totals", []):
                if t.get("type") == "total":
                    total = t.get("amount", 0)
                    break
            
            session = CheckoutSession(
                id=data["id"],
                status=data["status"],
                total=total,
                currency=data.get("currency", "BRL"),
                line_items=data.get("line_items", []),
                raw_data=data
            )
            
            logger.info("Checkout created", session_id=session.id, total=total)
            return session
            
        except Exception as e:
            logger.error("Create checkout failed", error=str(e))
            return None
    
    async def apply_discount(
        self,
        session_id: str,
        discount_code: str
    ) -> Optional[CheckoutSession]:
        """Aplicar desconto a uma sessao."""
        try:
            response = await self._client.patch(
                f"{self.store_url}/checkout-sessions/{session_id}",
                json={"discount_codes": [discount_code]},
                headers=self._get_ucp_headers()
            )
            response.raise_for_status()
            
            data = response.json()
            total = 0
            for t in data.get("totals", []):
                if t.get("type") == "total":
                    total = t.get("amount", 0)
                    break
            
            return CheckoutSession(
                id=data["id"],
                status=data["status"],
                total=total,
                currency=data.get("currency", "BRL"),
                line_items=data.get("line_items", []),
                raw_data=data
            )
            
        except Exception as e:
            logger.error("Apply discount failed", error=str(e))
            return None
    
    async def complete_checkout(
        self,
        session_id: str,
        payment_token: str,
        mandate_jwt: Optional[str] = None,
        wallet_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Completar checkout com pagamento.
        
        Args:
            session_id: ID da sessao
            payment_token: Token de pagamento
            mandate_jwt: Mandato AP2 (opcional)
            wallet_token: Token da carteira virtual (opcional)
            
        Returns:
            Resultado do checkout
        """
        try:
            payment = {"token": payment_token}
            if mandate_jwt:
                payment["mandate"] = mandate_jwt
            if wallet_token:
                payment["wallet_token"] = wallet_token
            
            response = await self._client.post(
                f"{self.store_url}/checkout-sessions/{session_id}/complete",
                json={"payment": payment},
                headers=self._get_ucp_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(
                "Checkout completed", 
                session_id=session_id,
                wallet_token_used=bool(wallet_token)
            )
            return result
            
        except httpx.HTTPStatusError as e:
            error_data = {"error": f"HTTP {e.response.status_code}"}
            try:
                error_data = e.response.json()
            except:
                pass
            logger.error("Complete checkout failed", error=error_data)
            return error_data
            
        except Exception as e:
            logger.error("Complete checkout failed", error=str(e))
            return {"error": str(e)}
    
    def _get_ucp_headers(self) -> Dict[str, str]:
        """Gerar headers UCP."""
        import uuid
        import time
        return {
            "UCP-Agent": "user-agent/1.0",
            "request-id": str(uuid.uuid4()),
            "idempotency-key": str(uuid.uuid4()),
            "ucp-timestamp": str(int(time.time()))
        }
    
    async def close(self):
        """Fechar cliente."""
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
