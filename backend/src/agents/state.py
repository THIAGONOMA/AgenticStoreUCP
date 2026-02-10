"""Estado compartilhado dos Store Agents."""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from enum import Enum
import operator


class AgentRole(str, Enum):
    """Roles dos agentes."""
    ORCHESTRATOR = "orchestrator"
    DISCOVERY = "discovery"
    SHOPPING = "shopping"
    RECOMMEND = "recommend"
    SUPPORT = "support"


class MessageType(str, Enum):
    """Tipos de mensagem."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    A2A = "a2a"


class Message(TypedDict):
    """Mensagem no chat."""
    role: str
    content: str
    type: str
    metadata: Optional[Dict[str, Any]]


class CartItem(TypedDict):
    """Item no carrinho."""
    book_id: str
    title: str
    quantity: int
    price: int


class StoreAgentState(TypedDict):
    """
    Estado compartilhado entre os agentes da loja.
    
    Usado pelo LangGraph para manter contexto entre nodes.
    """
    # Identificacao
    session_id: str
    user_id: Optional[str]
    
    # Conversa
    messages: Annotated[List[Message], operator.add]
    current_intent: Optional[str]
    
    # Carrinho
    cart_items: List[CartItem]
    cart_total: int
    applied_discount: Optional[str]
    
    # Checkout
    checkout_session_id: Optional[str]
    checkout_status: Optional[str]
    
    # Contexto de busca
    search_query: Optional[str]
    search_results: List[Dict[str, Any]]
    selected_book_id: Optional[str]
    
    # Recomendacoes
    recommendations: List[Dict[str, Any]]
    
    # Controle de fluxo
    next_agent: Optional[str]
    error: Optional[str]
    
    # A2A
    external_agent_id: Optional[str]
    a2a_request: Optional[Dict[str, Any]]


def create_initial_state(session_id: str) -> StoreAgentState:
    """Criar estado inicial."""
    return StoreAgentState(
        session_id=session_id,
        user_id=None,
        messages=[],
        current_intent=None,
        cart_items=[],
        cart_total=0,
        applied_discount=None,
        checkout_session_id=None,
        checkout_status=None,
        search_query=None,
        search_results=[],
        selected_book_id=None,
        recommendations=[],
        next_agent=None,
        error=None,
        external_agent_id=None,
        a2a_request=None,
    )
