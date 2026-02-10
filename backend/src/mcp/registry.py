"""Registry de ferramentas MCP."""
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class ToolDefinition:
    """Definicao de uma ferramenta MCP."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Awaitable[Any]]
    category: str = "general"
    requires_auth: bool = False
    rate_limit: Optional[int] = None  # requests per minute


@dataclass
class ToolRegistry:
    """
    Registry central de ferramentas MCP.
    
    Gerencia registro, descoberta e execucao de ferramentas.
    """
    tools: Dict[str, ToolDefinition] = field(default_factory=dict)
    
    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Awaitable[Any]],
        category: str = "general",
        requires_auth: bool = False,
        rate_limit: Optional[int] = None
    ):
        """Registrar uma ferramenta."""
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
            category=category,
            requires_auth=requires_auth,
            rate_limit=rate_limit
        )
        logger.info("Tool registered", name=name, category=category)
    
    def unregister(self, name: str):
        """Remover uma ferramenta."""
        if name in self.tools:
            del self.tools[name]
            logger.info("Tool unregistered", name=name)
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        """Obter definicao de ferramenta."""
        return self.tools.get(name)
    
    def list_all(self) -> List[ToolDefinition]:
        """Listar todas as ferramentas."""
        return list(self.tools.values())
    
    def list_by_category(self, category: str) -> List[ToolDefinition]:
        """Listar ferramentas por categoria."""
        return [t for t in self.tools.values() if t.category == category]
    
    def get_categories(self) -> List[str]:
        """Listar categorias disponiveis."""
        return list(set(t.category for t in self.tools.values()))
    
    async def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Executar uma ferramenta."""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        
        logger.info("Executing tool", name=name)
        return await tool.handler(arguments)
    
    def to_mcp_format(self) -> List[Dict[str, Any]]:
        """Converter para formato MCP."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema
            }
            for t in self.tools.values()
        ]


# Registry global
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Obter registry global."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    category: str = "general",
    requires_auth: bool = False
):
    """
    Decorator para registrar ferramentas.
    
    Usage:
        @tool("my_tool", "Description", {"type": "object", ...})
        async def my_tool(args):
            return result
    """
    def decorator(func: Callable[[Dict[str, Any]], Awaitable[Any]]):
        registry = get_tool_registry()
        registry.register(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=func,
            category=category,
            requires_auth=requires_auth
        )
        return func
    return decorator
