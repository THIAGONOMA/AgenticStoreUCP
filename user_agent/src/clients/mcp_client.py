"""Cliente MCP para User Agent."""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class MCPTool:
    """Representacao de uma ferramenta MCP."""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass 
class MCPCallResult:
    """Resultado de uma chamada MCP."""
    success: bool
    data: Any = None
    error: Optional[str] = None


class MCPClient:
    """
    Cliente MCP para User Agent.
    
    Conecta a servidores MCP via HTTP/SSE e executa ferramentas.
    """
    
    def __init__(self, server_url: str):
        """
        Inicializar cliente.
        
        Args:
            server_url: URL base do servidor MCP
        """
        self.server_url = server_url.rstrip("/")
        self.tools: Dict[str, MCPTool] = {}
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def discover_tools(self) -> List[MCPTool]:
        """
        Descobrir ferramentas disponiveis no servidor.
        
        Returns:
            Lista de ferramentas MCP
        """
        try:
            # Tentar endpoint MCP padrao (/mcp/tools)
            response = await self._client.get(f"{self.server_url}/mcp/tools")
            if response.status_code == 404:
                # Fallback para endpoint antigo (/tools)
                response = await self._client.get(f"{self.server_url}/tools")
            
            response.raise_for_status()
            
            data = response.json()
            tools = []
            
            for tool_data in data.get("tools", []):
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {})
                )
                self.tools[tool.name] = tool
                tools.append(tool)
            
            logger.info("MCP tools discovered", count=len(tools), server=self.server_url)
            return tools
            
        except Exception as e:
            logger.error("Failed to discover MCP tools", error=str(e), server=self.server_url)
            return []
    
    async def list_tools(self) -> List[MCPTool]:
        """Alias para discover_tools (compatibilidade)."""
        return await self.discover_tools()
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> MCPCallResult:
        """
        Chamar uma ferramenta MCP.
        
        Args:
            name: Nome da ferramenta
            arguments: Argumentos para a ferramenta
            
        Returns:
            MCPCallResult com resultado ou erro
        """
        try:
            # Usar endpoint MCP padrao
            response = await self._client.post(
                f"{self.server_url}/mcp/tools/{name}/call",
                json={"arguments": arguments}
            )
            response.raise_for_status()
            
            data = response.json()
            
            logger.info("MCP tool called", tool=name)
            return MCPCallResult(success=True, data=data.get("data", data))
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error("MCP tool call failed", tool=name, error=error_msg)
            return MCPCallResult(success=False, error=error_msg)
            
        except Exception as e:
            logger.error("MCP tool call failed", tool=name, error=str(e))
            return MCPCallResult(success=False, error=str(e))
    
    async def search_books(self, query: str, max_results: int = 10) -> MCPCallResult:
        """Helper: Buscar livros."""
        return await self.call_tool("search_books", {
            "query": query,
            "max_results": max_results
        })
    
    async def get_book_details(self, book_id: str) -> MCPCallResult:
        """Helper: Obter detalhes de livro."""
        return await self.call_tool("get_book_details", {"book_id": book_id})
    
    async def list_categories(self) -> MCPCallResult:
        """Helper: Listar categorias."""
        return await self.call_tool("list_categories", {})
    
    async def calculate_cart(
        self,
        items: List[Dict[str, Any]],
        discount_code: Optional[str] = None
    ) -> MCPCallResult:
        """Helper: Calcular carrinho."""
        args = {"items": items}
        if discount_code:
            args["discount_code"] = discount_code
        return await self.call_tool("calculate_cart", args)
    
    async def get_recommendations(
        self,
        book_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> MCPCallResult:
        """Helper: Obter recomendacoes."""
        args = {}
        if book_id:
            args["based_on_book_id"] = book_id
        if category:
            args["category"] = category
        return await self.call_tool("get_recommendations", args)
    
    # =========================================================================
    # Ferramentas de Pagamentos
    # =========================================================================
    
    async def get_wallet_balance(self, wallet_id: str = "default_wallet") -> MCPCallResult:
        """Helper: Consultar saldo da carteira da loja."""
        return await self.call_tool("get_wallet_balance", {"wallet_id": wallet_id})
    
    async def list_transactions(
        self,
        limit: int = 10,
        status: Optional[str] = None,
        wallet_source: Optional[str] = None
    ) -> MCPCallResult:
        """Helper: Listar transacoes de pagamento."""
        args = {"limit": limit}
        if status:
            args["status"] = status
        if wallet_source:
            args["wallet_source"] = wallet_source
        return await self.call_tool("list_transactions", args)
    
    async def get_transaction(self, transaction_id: str) -> MCPCallResult:
        """Helper: Obter detalhes de uma transacao."""
        return await self.call_tool("get_transaction", {"transaction_id": transaction_id})
    
    async def close(self):
        """Fechar cliente."""
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
