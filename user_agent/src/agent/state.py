"""Estado do User Agent."""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from enum import Enum
from dataclasses import dataclass
import operator


class UserIntent(str, Enum):
    """Intencoes do usuario - Agente Pessoal Generico."""
    
    # Geral
    QUESTION = "question"      # Pergunta geral
    CHAT = "chat"              # Conversa casual
    HELP = "help"              # Ajuda
    
    # Agentes (A2A)
    DISCOVER_AGENT = "discover_agent"  # Descobrir agente por URL
    LIST_AGENTS = "list_agents"        # Listar agentes conectados
    TALK_TO_AGENT = "talk_to_agent"    # Falar com agente especifico
    
    # Comercio (UCP)
    DISCOVER = "discover"              # Descobrir loja UCP
    SEARCH = "search"                  # Buscar produtos
    COMPARE = "compare"                # Comparar produtos
    BUY = "buy"                        # Comprar (alias para checkout)
    ADD_TO_CART = "add_to_cart"        # Adicionar ao carrinho
    REMOVE_FROM_CART = "remove_from_cart"  # Remover do carrinho
    VIEW_CART = "view_cart"            # Ver carrinho
    CHECKOUT = "checkout"              # Finalizar compra
    APPLY_DISCOUNT = "apply_discount"  # Aplicar cupom
    RECOMMEND = "recommend"            # Pedir recomendacoes
    
    # Ferramentas (MCP)
    USE_TOOL = "use_tool"              # Usar ferramenta MCP
    LIST_TOOLS = "list_tools"          # Listar ferramentas disponiveis


class AgentInfo(TypedDict):
    """Informacoes de um agente A2A."""
    url: str
    name: str
    description: str
    version: str
    skills: List[str]
    connected: bool


class StoreInfo(TypedDict):
    """Informacoes de uma loja UCP."""
    url: str
    name: str
    version: str
    connected: bool
    capabilities: List[str]
    a2a_connected: bool  # Se esta conectado via A2A


class MCPToolInfo(TypedDict):
    """Informacoes de uma ferramenta MCP."""
    name: str
    description: str
    server_url: str
    input_schema: Optional[Dict[str, Any]]


class CartItem(TypedDict):
    """Item no carrinho."""
    store_url: str
    product_id: str
    title: str
    price: int
    quantity: int


class Message(TypedDict):
    """Mensagem no historico."""
    role: str  # user, assistant, system
    content: str
    metadata: Optional[Dict[str, Any]]  # Dados extras (intent, params, etc)


class A2ASession(TypedDict):
    """Sessao A2A ativa."""
    store_url: str
    agent_id: str
    connected: bool
    last_message_id: Optional[str]
    pending_responses: List[str]


class AP2MandateInfo(TypedDict):
    """Informacoes de mandato AP2."""
    intent_mandate_id: Optional[str]
    cart_mandate_id: Optional[str]
    cart_mandate_jwt: Optional[str]
    payment_mandate_id: Optional[str]
    payment_mandate_jwt: Optional[str]
    total_authorized: int
    currency: str


class UserAgentState(TypedDict):
    """
    Estado do User Agent - Agente Pessoal Generico.
    
    Mantém contexto de:
    - Conversa e intencoes
    - Agentes conectados (A2A)
    - Lojas descobertas (UCP)
    - Ferramentas disponiveis (MCP)
    - Carrinho e checkout
    """
    # Identificacao
    session_id: str
    user_name: Optional[str]
    user_email: Optional[str]
    
    # Conversa
    messages: Annotated[List[Message], operator.add]
    current_intent: Optional[str]
    intent_params: Optional[Dict[str, Any]]
    intent_confidence: float
    
    # LLM
    llm_enabled: bool
    
    # Agentes A2A conectados
    connected_agents: Dict[str, AgentInfo]  # url -> AgentInfo
    active_agent_url: Optional[str]  # Agente ativo para conversa
    
    # Lojas UCP descobertas
    discovered_stores: Dict[str, StoreInfo]
    active_store_url: Optional[str]
    
    # Sessoes A2A (para comunicacao com agentes/lojas)
    a2a_sessions: Dict[str, A2ASession]  # url -> session
    active_a2a_session: Optional[str]  # url da sessao ativa
    
    # Ferramentas MCP disponiveis
    mcp_tools: Dict[str, MCPToolInfo]  # name -> MCPToolInfo
    mcp_servers: List[str]  # URLs dos servidores MCP conectados
    
    # Busca
    search_query: Optional[str]
    search_results: List[Dict[str, Any]]
    
    # Comparacao
    comparison_items: List[Dict[str, Any]]
    
    # Carrinho (multi-loja)
    cart_items: List[CartItem]
    cart_total: int
    applied_discount: Optional[str]
    discount_amount: int
    
    # Checkout
    checkout_in_progress: bool
    checkout_store: Optional[str]
    checkout_session_id: Optional[str]
    checkout_total: int
    
    # AP2 Mandates (pagamento autonomo)
    ap2_mandate: Optional[AP2MandateInfo]
    
    # Recomendacoes
    recommendations: List[Dict[str, Any]]
    
    # Controle
    next_action: Optional[str]
    error: Optional[str]
    waiting_for_confirmation: bool
    confirmation_context: Optional[Dict[str, Any]]


def create_initial_state(
    session_id: str, 
    user_name: str = None,
    user_email: str = None
) -> UserAgentState:
    """Criar estado inicial do Agente Pessoal."""
    return UserAgentState(
        # Identificacao
        session_id=session_id,
        user_name=user_name or "Usuario",
        user_email=user_email or f"{session_id[:8]}@user-agent.local",
        
        # Conversa
        messages=[],
        current_intent=None,
        intent_params=None,
        intent_confidence=0.0,
        
        # LLM
        llm_enabled=False,
        
        # Agentes A2A
        connected_agents={},
        active_agent_url=None,
        
        # Lojas UCP
        discovered_stores={},
        active_store_url=None,
        
        # Sessoes A2A
        a2a_sessions={},
        active_a2a_session=None,
        
        # Ferramentas MCP
        mcp_tools={},
        mcp_servers=[],
        
        # Busca
        search_query=None,
        search_results=[],
        
        # Comparacao
        comparison_items=[],
        
        # Carrinho
        cart_items=[],
        cart_total=0,
        applied_discount=None,
        discount_amount=0,
        
        # Checkout
        checkout_in_progress=False,
        checkout_store=None,
        checkout_session_id=None,
        checkout_total=0,
        
        # AP2
        ap2_mandate=None,
        
        # Recomendacoes
        recommendations=[],
        
        # Controle
        next_action=None,
        error=None,
        waiting_for_confirmation=False,
        confirmation_context=None
    )
