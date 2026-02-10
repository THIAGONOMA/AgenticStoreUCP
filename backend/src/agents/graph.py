"""Store Agents Graph - LangGraph principal."""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
import structlog

from .state import StoreAgentState, create_initial_state, Message
from .nodes.orchestrator import orchestrator_node, route_to_agent
from .nodes.discovery import discovery_node
from .nodes.shopping import shopping_node
from .nodes.recommend import recommend_node

logger = structlog.get_logger()


def create_store_agents_graph() -> StateGraph:
    """
    Criar grafo de agentes da loja.
    
    Fluxo:
    1. Orchestrator recebe mensagem e decide rota
    2. Agente especializado processa
    3. Retorna resposta
    
    Returns:
        StateGraph compilado
    """
    # Criar grafo
    workflow = StateGraph(StoreAgentState)
    
    # Adicionar nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("discovery", discovery_node)
    workflow.add_node("shopping", shopping_node)
    workflow.add_node("recommend", recommend_node)
    
    # Definir entry point
    workflow.set_entry_point("orchestrator")
    
    # Adicionar edges condicionais
    workflow.add_conditional_edges(
        "orchestrator",
        route_to_agent,
        {
            "discovery": "discovery",
            "shopping": "shopping",
            "recommend": "recommend",
            "end": END
        }
    )
    
    # Agentes terminam o fluxo
    workflow.add_edge("discovery", END)
    workflow.add_edge("shopping", END)
    workflow.add_edge("recommend", END)
    
    return workflow.compile()


# Grafo compilado
store_graph = create_store_agents_graph()


class StoreAgentRunner:
    """
    Runner para executar o grafo de agentes.
    
    Mantém estado entre invocações para cada sessão.
    """
    
    def __init__(self):
        self.sessions: Dict[str, StoreAgentState] = {}
    
    def get_or_create_session(self, session_id: str) -> StoreAgentState:
        """Obter ou criar estado de sessão."""
        if session_id not in self.sessions:
            self.sessions[session_id] = create_initial_state(session_id)
        return self.sessions[session_id]
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Processar mensagem do usuário.
        
        Args:
            session_id: ID da sessão
            message: Mensagem do usuário
            user_id: ID do usuário (opcional)
            
        Returns:
            Resposta do agente
        """
        # Obter estado
        state = self.get_or_create_session(session_id)
        
        # Adicionar mensagem do usuário
        user_msg = Message(
            role="user",
            content=message,
            type="user",
            metadata={"user_id": user_id}
        )
        
        # Criar novo estado com mensagem
        input_state = {
            **state,
            "messages": state["messages"] + [user_msg],
            "user_id": user_id
        }
        
        logger.info("Processing message", session=session_id, message=message[:50])
        
        # Executar grafo
        result = await store_graph.ainvoke(input_state)
        
        # Atualizar estado da sessão
        self.sessions[session_id] = result
        
        # Extrair resposta do agente
        agent_messages = [
            m for m in result.get("messages", [])
            if m.get("type") == "agent"
        ]
        
        response = agent_messages[-1] if agent_messages else None
        
        return {
            "session_id": session_id,
            "response": response["content"] if response else "Desculpe, não entendi.",
            "metadata": response.get("metadata", {}) if response else {},
            "cart_items": result.get("cart_items", []),
            "cart_total": result.get("cart_total", 0),
            "search_results": result.get("search_results", []),
            "recommendations": result.get("recommendations", [])
        }
    
    async def process_a2a_request(
        self,
        session_id: str,
        agent_id: str,
        action: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processar requisição A2A de agente externo.
        
        Args:
            session_id: ID da sessão
            agent_id: ID do agente externo
            action: Ação a executar
            payload: Dados da requisição
            
        Returns:
            Resposta A2A
        """
        state = self.get_or_create_session(session_id)
        
        # Criar estado com requisição A2A
        input_state = {
            **state,
            "external_agent_id": agent_id,
            "a2a_request": {
                "action": action,
                "payload": payload
            }
        }
        
        logger.info("Processing A2A request", agent=agent_id, action=action)
        
        # Executar grafo
        result = await store_graph.ainvoke(input_state)
        
        # Limpar a2a_request do estado
        result["a2a_request"] = None
        self.sessions[session_id] = result
        
        return {
            "status": "success",
            "action": action,
            "data": {
                "search_results": result.get("search_results", []),
                "recommendations": result.get("recommendations", []),
                "checkout_session_id": result.get("checkout_session_id"),
                "checkout_status": result.get("checkout_status"),
                "cart_total": result.get("cart_total", 0)
            }
        }
    
    def clear_session(self, session_id: str):
        """Limpar sessão."""
        if session_id in self.sessions:
            del self.sessions[session_id]


# Runner global
store_agent_runner = StoreAgentRunner()
