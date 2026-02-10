"""Progressive Disclosure para MCP.

Implementa o conceito de "progressive disclosure" do MCP,
onde ferramentas sao reveladas gradualmente conforme o contexto.
"""
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, field
import structlog

from .registry import ToolDefinition, get_tool_registry

logger = structlog.get_logger()


@dataclass
class DisclosureLevel:
    """Nivel de disclosure."""
    name: str
    tools: Set[str]
    description: str
    
    
@dataclass
class DisclosureContext:
    """Contexto de disclosure para uma sessao."""
    session_id: str
    current_level: str = "basic"
    unlocked_tools: Set[str] = field(default_factory=set)
    interaction_count: int = 0
    
    def unlock(self, tool_name: str):
        """Desbloquear uma ferramenta."""
        self.unlocked_tools.add(tool_name)
        
    def can_access(self, tool_name: str) -> bool:
        """Verificar se pode acessar ferramenta."""
        return tool_name in self.unlocked_tools


class ProgressiveDisclosure:
    """
    Gerenciador de Progressive Disclosure.
    
    Controla quais ferramentas sao visíveis em cada nivel.
    """
    
    def __init__(self):
        self.levels: Dict[str, DisclosureLevel] = {}
        self.contexts: Dict[str, DisclosureContext] = {}
        self._setup_default_levels()
    
    def _setup_default_levels(self):
        """Configurar niveis padrao para livraria."""
        # Nivel basico - ferramentas de descoberta
        self.levels["basic"] = DisclosureLevel(
            name="basic",
            tools={"search_books", "list_categories", "get_book_details"},
            description="Ferramentas basicas de navegacao"
        )
        
        # Nivel intermediario - carrinho e descontos
        self.levels["shopping"] = DisclosureLevel(
            name="shopping",
            tools={
                "search_books", "list_categories", "get_book_details",
                "get_books_by_category", "check_discount_code", "calculate_cart"
            },
            description="Ferramentas de compra"
        )
        
        # Nivel avancado - checkout e recomendacoes
        self.levels["advanced"] = DisclosureLevel(
            name="advanced",
            tools={
                "search_books", "list_categories", "get_book_details",
                "get_books_by_category", "check_discount_code", "calculate_cart",
                "get_recommendations", "create_checkout", "complete_checkout"
            },
            description="Ferramentas completas"
        )
    
    def get_context(self, session_id: str) -> DisclosureContext:
        """Obter ou criar contexto de sessao."""
        if session_id not in self.contexts:
            self.contexts[session_id] = DisclosureContext(
                session_id=session_id,
                unlocked_tools=self.levels["basic"].tools.copy()
            )
        return self.contexts[session_id]
    
    def upgrade_level(self, session_id: str, new_level: str) -> List[str]:
        """
        Fazer upgrade do nivel de uma sessao.
        
        Returns:
            Lista de novas ferramentas desbloqueadas
        """
        context = self.get_context(session_id)
        
        if new_level not in self.levels:
            return []
        
        level = self.levels[new_level]
        new_tools = level.tools - context.unlocked_tools
        
        context.unlocked_tools.update(level.tools)
        context.current_level = new_level
        
        logger.info(
            "Disclosure level upgraded",
            session=session_id,
            level=new_level,
            new_tools=list(new_tools)
        )
        
        return list(new_tools)
    
    def get_available_tools(self, session_id: str) -> List[Dict[str, Any]]:
        """Obter ferramentas disponiveis para uma sessao."""
        context = self.get_context(session_id)
        registry = get_tool_registry()
        
        available = []
        for tool in registry.list_all():
            if tool.name in context.unlocked_tools:
                available.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.input_schema
                })
        
        return available
    
    def record_interaction(self, session_id: str, tool_name: str):
        """
        Registrar interacao e potencialmente fazer upgrade automatico.
        """
        context = self.get_context(session_id)
        context.interaction_count += 1
        
        # Auto-upgrade baseado em uso
        if context.interaction_count >= 3 and context.current_level == "basic":
            self.upgrade_level(session_id, "shopping")
        elif context.interaction_count >= 7 and context.current_level == "shopping":
            self.upgrade_level(session_id, "advanced")
    
    def clear_context(self, session_id: str):
        """Limpar contexto de sessao."""
        if session_id in self.contexts:
            del self.contexts[session_id]


# Instancia global
_progressive_disclosure: Optional[ProgressiveDisclosure] = None


def get_progressive_disclosure() -> ProgressiveDisclosure:
    """Obter instancia de ProgressiveDisclosure."""
    global _progressive_disclosure
    if _progressive_disclosure is None:
        _progressive_disclosure = ProgressiveDisclosure()
    return _progressive_disclosure
