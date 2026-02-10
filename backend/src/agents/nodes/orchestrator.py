"""Orchestrator Node - Roteador principal dos agentes."""
from typing import Dict, Any, Literal
import structlog

from ..state import StoreAgentState, Message, AgentRole
from ..llm import detect_intent_with_llm, is_llm_enabled

logger = structlog.get_logger()

# Palavras-chave para detectar intencao (fallback quando LLM nao disponivel)
# Ordem importa! Mais especificos primeiro
INTENT_KEYWORDS = {
    "buy": ["quero comprar", "comprar esse", "comprar este", "vou levar", "quero esse", "quero este", "me da esse", "me dá esse"],
    "checkout": ["finalizar", "finaliza", "fechar", "concluir", "pagar", "confirmar", "fechar pedido", "concluir compra", "pagar agora", "confirmar pedido", "quero pagar", "quero finalizar"],
    "discount": ["cupom", "desconto", "promocao", "codigo", "tenho cupom"],
    "cart": ["carrinho", "adicionar", "remover", "ver carrinho", "meu carrinho"],
    "recommend": ["recomend", "suger", "indic", "similar", "parecido", "gosto de", "sugira", "indique"],
    "search": ["buscar", "procurar", "encontrar", "pesquisar", "tem livro", "livro sobre", "livros de"],
    "help": ["ajuda", "como funciona", "ola", "oi", "bom dia", "boa tarde", "boa noite"],
}


def detect_intent_rules(message: str) -> str:
    """Detectar intencao da mensagem usando regras (fallback)."""
    message_lower = message.lower()
    
    # Primeiro, verificar frases completas (mais especificas)
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            # Para keywords com espaco, verificar frase completa
            if " " in keyword and keyword in message_lower:
                return intent
    
    # Depois, verificar palavras individuais
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if " " not in keyword and keyword in message_lower:
                return intent
    
    return "search"  # Default


async def detect_intent(message: str) -> str:
    """
    Detectar intencao da mensagem.
    
    Usa LLM se disponivel, senao usa regras baseadas em keywords.
    """
    # Tentar com LLM primeiro
    if is_llm_enabled():
        llm_intent = await detect_intent_with_llm(message)
        if llm_intent:
            logger.info("Intent detected via LLM", intent=llm_intent)
            return llm_intent
    
    # Fallback para regras
    rule_intent = detect_intent_rules(message)
    logger.info("Intent detected via rules", intent=rule_intent)
    return rule_intent


async def orchestrator_node(state: StoreAgentState) -> Dict[str, Any]:
    """
    Orchestrator Node - Decide para qual agente rotear.
    
    Analisa a mensagem do usuario e determina o proximo agente.
    """
    logger.info("Orchestrator processing", session=state["session_id"])
    
    # Pegar ultima mensagem do usuario
    user_messages = [m for m in state["messages"] if m["type"] == "user"]
    
    if not user_messages:
        return {
            "next_agent": AgentRole.DISCOVERY.value,
            "current_intent": "help"
        }
    
    last_message = user_messages[-1]["content"]
    
    # Verificar se e requisicao A2A
    if state.get("a2a_request"):
        logger.info("A2A request detected", request=state["a2a_request"])
        action = state["a2a_request"].get("action", "")
        
        if action in ["search", "get_products"]:
            return {"next_agent": AgentRole.DISCOVERY.value, "current_intent": "search"}
        elif action in ["checkout", "create_order"]:
            return {"next_agent": AgentRole.SHOPPING.value, "current_intent": "checkout"}
        elif action == "recommend":
            return {"next_agent": AgentRole.RECOMMEND.value, "current_intent": "recommend"}
    
    # Detectar intencao (usa LLM se disponivel)
    intent = await detect_intent(last_message)
    logger.info("Intent detected", intent=intent, message=last_message[:50])
    
    # Mapear intencao para agente
    intent_to_agent = {
        "search": AgentRole.DISCOVERY.value,
        "recommend": AgentRole.RECOMMEND.value,
        "buy": AgentRole.SHOPPING.value,  # "quero comprar [livro]"
        "cart": AgentRole.SHOPPING.value,
        "checkout": AgentRole.SHOPPING.value,
        "discount": AgentRole.SHOPPING.value,
        "help": AgentRole.DISCOVERY.value,
    }
    
    next_agent = intent_to_agent.get(intent, AgentRole.DISCOVERY.value)
    
    return {
        "next_agent": next_agent,
        "current_intent": intent
    }


def route_to_agent(state: StoreAgentState) -> Literal["discovery", "shopping", "recommend", "end"]:
    """Funcao de roteamento para o grafo."""
    next_agent = state.get("next_agent")
    
    if next_agent == AgentRole.DISCOVERY.value:
        return "discovery"
    elif next_agent == AgentRole.SHOPPING.value:
        return "shopping"
    elif next_agent == AgentRole.RECOMMEND.value:
        return "recommend"
    else:
        return "end"
