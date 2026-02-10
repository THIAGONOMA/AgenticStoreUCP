"""User Agent Graph - Agente Pessoal Generico com LangGraph."""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
import structlog

from .state import UserAgentState, create_initial_state, Message, UserIntent
from .nodes import discovery_node, shopping_node, compare_node
from .llm import is_llm_enabled, detect_intent_with_llm, generate_response, USER_AGENT_SYSTEM_PROMPT

logger = structlog.get_logger()


# Mapeamento de intent para node - Agente Pessoal Generico
INTENT_TO_NODE = {
    # Geral
    "question": "question",    # Perguntas gerais
    "chat": "chat",            # Conversa casual / A2A
    "help": "help",            # Ajuda
    
    # Agentes (A2A)
    "discover_agent": "agents",
    "list_agents": "agents",
    "talk_to_agent": "chat",   # Conversa via A2A
    
    # Comercio (UCP)
    "discover": "discovery",
    "search": "discovery",
    "recommend": "discovery",
    "add_to_cart": "shopping",
    "remove_from_cart": "shopping",
    "view_cart": "shopping",
    "checkout": "shopping",
    "apply_discount": "shopping",
    "buy": "shopping",
    "compare": "compare",
    
    # Ferramentas (MCP)
    "use_tool": "mcp",
    "list_tools": "mcp"
}


async def router_node(state: UserAgentState) -> Dict[str, Any]:
    """
    Router - decidir para qual node ir usando LLM ou keywords.
    Suporta intencoes gerais, agentes, comercio e ferramentas.
    """
    user_messages = [m for m in state["messages"] if m["role"] == "user"]
    
    if not user_messages:
        return {
            "current_intent": "help",
            "intent_params": {},
            "intent_confidence": 1.0,
            "next_action": "help",
            "llm_enabled": is_llm_enabled()
        }
    
    last_message = user_messages[-1]["content"]
    
    # Verificar se esta esperando confirmacao
    if state.get("waiting_for_confirmation"):
        return await _handle_confirmation(last_message, state)
    
    # Detectar intent
    if is_llm_enabled():
        # Usar LLM para detecao - passar contexto completo
        intent_result = await detect_intent_with_llm(
            message=last_message,
            agents=list(state.get("connected_agents", {}).keys()),
            stores=list(state.get("discovered_stores", {}).keys()),
            cart_count=len(state.get("cart_items", [])),
            last_search=state.get("search_query"),
            mcp_tools=list(state.get("mcp_tools", {}).keys())
        )
    else:
        # Fallback para keywords
        intent_result = _detect_intent_keywords(last_message)
    
    intent = intent_result.get("intent", "chat")
    params = intent_result.get("params", {})
    confidence = intent_result.get("confidence", 0.5)
    
    # Mapear intent para action
    next_action = INTENT_TO_NODE.get(intent, "question")  # Default para question ao inves de chat
    
    logger.info(
        "Intent detected",
        intent=intent,
        confidence=confidence,
        next_action=next_action,
        llm=is_llm_enabled()
    )
    
    return {
        "current_intent": intent,
        "intent_params": params,
        "intent_confidence": confidence,
        "next_action": next_action,
        "llm_enabled": is_llm_enabled()
    }


async def _handle_confirmation(message: str, state: UserAgentState) -> Dict[str, Any]:
    """Processar resposta de confirmacao."""
    message_lower = message.lower().strip()
    
    # Palavras de confirmacao
    confirm_words = ["sim", "s", "yes", "y", "ok", "confirmar", "aceito", "pode", "vai"]
    cancel_words = ["nao", "n", "no", "cancelar", "desistir", "parar"]
    
    context = state.get("confirmation_context", {})
    
    if any(word in message_lower for word in confirm_words):
        # Usuario confirmou
        return {
            "current_intent": context.get("confirm_intent", "checkout"),
            "intent_params": context.get("params", {}),
            "intent_confidence": 1.0,
            "next_action": context.get("next_action", "shopping"),
            "waiting_for_confirmation": False,
            "confirmation_context": None
        }
    elif any(word in message_lower for word in cancel_words):
        # Usuario cancelou
        return {
            "current_intent": "cancel",
            "intent_params": {},
            "intent_confidence": 1.0,
            "next_action": "help",
            "waiting_for_confirmation": False,
            "confirmation_context": None
        }
    else:
        # Nao entendeu - pedir novamente
        return {
            "current_intent": "confirm_unclear",
            "next_action": "help"
        }


def _detect_intent_keywords(message: str) -> Dict[str, Any]:
    """Fallback: detectar intencao por palavras-chave."""
    message_lower = message.lower()
    
    intent_keywords = {
        "discover": ["descobrir", "conectar", "url", "http", "loja"],
        "search": ["buscar", "procurar", "encontrar", "pesquisar", "quero", "preciso"],
        "compare": ["comparar", "comparacao", "diferenca", "melhor preco"],
        "add_to_cart": ["adicionar", "colocar", "incluir"],
        "remove_from_cart": ["remover", "tirar", "excluir"],
        "view_cart": ["carrinho", "cart", "meu carrinho"],
        "checkout": ["comprar", "finalizar", "pagar", "checkout"],
        "apply_discount": ["cupom", "desconto", "codigo"],
        "help": ["ajuda", "help", "ola", "oi", "como"]
    }
    
    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in message_lower:
                return {"intent": intent, "params": {}, "confidence": 0.7}
    
    return {"intent": "chat", "params": {}, "confidence": 0.5}


async def chat_node(state: UserAgentState) -> Dict[str, Any]:
    """
    Chat Node - Conversa via A2A com Store Agent.
    """
    from .nodes.chat import chat_node as _chat_node
    return await _chat_node(state)


async def question_node(state: UserAgentState) -> Dict[str, Any]:
    """
    Question Node - Responder perguntas gerais usando LLM.
    """
    messages = []
    user_messages = [m for m in state["messages"] if m["role"] == "user"]
    
    if not user_messages:
        messages.append(Message(
            role="assistant",
            content="Como posso ajudar?",
            metadata=None
        ))
        return {"messages": messages, "next_action": None}
    
    last_message = user_messages[-1]["content"]
    
    # Tentar gerar resposta com LLM
    if is_llm_enabled():
        response = await generate_response(
            message=last_message,
            context={
                "agents_connected": len(state.get("connected_agents", {})),
                "stores_connected": len(state.get("discovered_stores", {})),
                "cart_items": len(state.get("cart_items", [])),
                "mcp_tools": len(state.get("mcp_tools", {}))
            },
            system_prompt=USER_AGENT_SYSTEM_PROMPT
        )
        
        if response:
            messages.append(Message(role="assistant", content=response, metadata=None))
            return {"messages": messages, "next_action": None}
    
    # Fallback - resposta generica
    response = (
        "Desculpe, nao tenho certeza de como responder isso.\n\n"
        "Posso ajudar com:\n"
        "- Perguntas gerais\n"
        "- Descobrir agentes e lojas\n"
        "- Buscar e comprar produtos\n"
        "- Usar ferramentas MCP\n\n"
        "Digite 'ajuda' para ver todos os comandos."
    )
    messages.append(Message(role="assistant", content=response, metadata=None))
    
    return {"messages": messages, "next_action": None}


async def agents_node(state: UserAgentState) -> Dict[str, Any]:
    """
    Agents Node - Gerenciar agentes A2A.
    """
    messages = []
    intent = state.get("current_intent", "list_agents")
    params = state.get("intent_params", {})
    connected_agents = dict(state.get("connected_agents", {}))
    
    if intent == "list_agents":
        # Listar agentes conectados
        if not connected_agents:
            response = (
                "Nenhum agente conectado ainda.\n\n"
                "Para descobrir um agente:\n"
                "`descobrir agente http://localhost:8000`"
            )
        else:
            lines = ["**Agentes Conectados:**\n"]
            for url, info in connected_agents.items():
                status = "✅" if info.get("connected") else "❌"
                lines.append(f"{status} **{info.get('name', 'Agente')}**")
                lines.append(f"   URL: {url}")
                if info.get("skills"):
                    lines.append(f"   Skills: {', '.join(info['skills'][:3])}")
                lines.append("")
            response = "\n".join(lines)
    
    elif intent == "discover_agent":
        # Descobrir novo agente
        url = params.get("url")
        
        # Fallback: extrair URL da mensagem se nao veio nos params
        if not url:
            import re
            user_messages = [m for m in state["messages"] if m["role"] == "user"]
            if user_messages:
                last_msg = user_messages[-1]["content"]
                urls = re.findall(r'https?://[^\s]+', last_msg)
                if urls:
                    url = urls[0]
        
        if not url:
            response = "Por favor, informe a URL do agente:\n`descobrir agente http://...`"
        else:
            # Tentar descobrir via A2A
            try:
                from ..clients import A2AClient
                client = A2AClient(url)
                profile = await client.get_agent_card()
                
                if profile:
                    agent_info = {
                        "url": url,
                        "name": profile.get("name", "Agente"),
                        "description": profile.get("description", ""),
                        "version": profile.get("version", "1.0"),
                        "skills": [s.get("name", s.get("id")) for s in profile.get("skills", [])],
                        "connected": True
                    }
                    connected_agents[url] = agent_info
                    
                    response = (
                        f"✅ Agente descoberto!\n\n"
                        f"**{agent_info['name']}**\n"
                        f"{agent_info['description']}\n\n"
                        f"Skills: {', '.join(agent_info['skills'])}"
                    )
                else:
                    response = f"❌ Nao foi possivel descobrir agente em {url}"
            except Exception as e:
                logger.error("Agent discovery failed", url=url, error=str(e))
                response = f"❌ Erro ao descobrir agente: {str(e)}"
    
    else:
        response = "Use 'listar agentes' ou 'descobrir agente http://...'"
    
    messages.append(Message(role="assistant", content=response, metadata=None))
    
    return {
        "messages": messages,
        "connected_agents": connected_agents,
        "next_action": None
    }


async def mcp_node(state: UserAgentState) -> Dict[str, Any]:
    """
    MCP Node - Gerenciar e usar ferramentas MCP.
    """
    messages = []
    intent = state.get("current_intent", "list_tools")
    params = state.get("intent_params", {})
    mcp_tools = dict(state.get("mcp_tools", {}))
    
    if intent == "list_tools":
        # Listar ferramentas disponiveis
        if not mcp_tools:
            response = (
                "Nenhuma ferramenta MCP disponivel.\n\n"
                "Ferramentas MCP permitem acesso a:\n"
                "- Busca na web\n"
                "- Acesso a arquivos\n"
                "- Execucao de codigo\n"
                "- E muito mais!\n\n"
                "*Configure servidores MCP para habilitar ferramentas.*"
            )
        else:
            lines = ["**Ferramentas MCP Disponiveis:**\n"]
            for name, info in mcp_tools.items():
                lines.append(f"🔧 **{name}**")
                lines.append(f"   {info.get('description', 'Sem descricao')}")
                lines.append("")
            lines.append("\nUse: `usar ferramenta [nome] [parametros]`")
            response = "\n".join(lines)
    
    elif intent == "use_tool":
        # Usar ferramenta
        tool_name = params.get("tool_name")
        if not tool_name:
            response = "Qual ferramenta deseja usar? Digite 'listar ferramentas' para ver opcoes."
        elif tool_name not in mcp_tools:
            response = f"Ferramenta '{tool_name}' nao encontrada. Digite 'listar ferramentas'."
        else:
            # TODO: Implementar chamada real ao MCP
            response = f"🔧 Executando ferramenta '{tool_name}'...\n\n*[MCP call em desenvolvimento]*"
    
    else:
        response = "Use 'listar ferramentas' ou 'usar ferramenta [nome]'"
    
    messages.append(Message(role="assistant", content=response, metadata=None))
    
    return {
        "messages": messages,
        "mcp_tools": mcp_tools,
        "next_action": None
    }


async def help_node(state: UserAgentState) -> Dict[str, Any]:
    """Help Node - Ajuda do Agente Pessoal Generico."""
    messages = []
    
    intent = state.get("current_intent", "help")
    
    if intent == "cancel":
        response = "Operacao cancelada. Como posso ajudar?"
    elif intent == "confirm_unclear":
        response = "Nao entendi. Por favor, responda 'sim' ou 'nao'."
    else:
        # Gerar ajuda - Agente Pessoal Generico
        cart_count = len(state.get("cart_items", []))
        stores_count = len(state.get("discovered_stores", {}))
        agents_count = len(state.get("connected_agents", {}))
        tools_count = len(state.get("mcp_tools", {}))
        
        lines = [
            "**User Agent - Seu Assistente Pessoal**\n",
            "Sou seu agente autonomo. Posso:",
            "",
            "📝 **Conversar**",
            "   Faca perguntas sobre qualquer assunto",
            "",
            "🤖 **Gerenciar Agentes (A2A)**",
            "   `descobrir agente http://...` - Conectar a agente",
            "   `listar agentes` - Ver agentes conectados",
            "",
            "🛒 **Fazer Compras (UCP)**",
            "   `descobrir http://...` - Conectar a loja",
            "   `buscar [termo]` - Buscar produtos",
            "   `adicionar [n]` - Adicionar ao carrinho",
            "   `carrinho` - Ver carrinho",
            "   `comprar` - Finalizar compra (AP2)",
            "",
            "🔧 **Usar Ferramentas (MCP)**",
            "   `listar ferramentas` - Ver ferramentas",
            "   `usar ferramenta [nome]` - Executar",
            "",
            "---"
        ]
        
        # Status atual
        status = []
        if agents_count > 0:
            status.append(f"🤖 {agents_count} agente(s)")
        if stores_count > 0:
            status.append(f"🏪 {stores_count} loja(s)")
        if cart_count > 0:
            status.append(f"🛒 {cart_count} item(ns)")
        if tools_count > 0:
            status.append(f"🔧 {tools_count} ferramenta(s)")
        
        if status:
            lines.append("*" + " | ".join(status) + "*")
        
        response = "\n".join(lines)
    
    messages.append(Message(role="assistant", content=response, metadata=None))
    
    return {
        "messages": messages,
        "next_action": None
    }


def route_to_node(state: UserAgentState) -> Literal[
    "question", "agents", "mcp", "discovery", "shopping", "compare", "chat", "help", "end"
]:
    """Funcao de roteamento - Agente Pessoal Generico."""
    action = state.get("next_action")
    
    # Mapeamento direto
    valid_nodes = ["question", "agents", "mcp", "discovery", "shopping", "compare", "chat", "help"]
    
    if action in valid_nodes:
        return action
    else:
        return "end"


def create_user_agent_graph() -> StateGraph:
    """Criar grafo do User Agent - Agente Pessoal Generico."""
    workflow = StateGraph(UserAgentState)
    
    # Adicionar nodes - Geral
    workflow.add_node("router", router_node)
    workflow.add_node("question", question_node)  # Perguntas gerais
    workflow.add_node("chat", chat_node)          # Conversa A2A
    workflow.add_node("help", help_node)          # Ajuda
    
    # Adicionar nodes - Agentes (A2A)
    workflow.add_node("agents", agents_node)
    
    # Adicionar nodes - Comercio (UCP)
    workflow.add_node("discovery", discovery_node)
    workflow.add_node("shopping", shopping_node)
    workflow.add_node("compare", compare_node)
    
    # Adicionar nodes - Ferramentas (MCP)
    workflow.add_node("mcp", mcp_node)
    
    # Entry point
    workflow.set_entry_point("router")
    
    # Edges condicionais
    workflow.add_conditional_edges(
        "router",
        route_to_node,
        {
            "question": "question",
            "agents": "agents",
            "mcp": "mcp",
            "discovery": "discovery",
            "shopping": "shopping",
            "compare": "compare",
            "chat": "chat",
            "help": "help",
            "end": END
        }
    )
    
    # Todos terminam apos executar
    workflow.add_edge("question", END)
    workflow.add_edge("agents", END)
    workflow.add_edge("mcp", END)
    workflow.add_edge("discovery", END)
    workflow.add_edge("shopping", END)
    workflow.add_edge("compare", END)
    workflow.add_edge("chat", END)
    workflow.add_edge("help", END)
    
    return workflow.compile()


# Grafo compilado
user_agent_graph = create_user_agent_graph()


class UserAgentRunner:
    """Runner para o User Agent - Agente Pessoal Generico."""
    
    def __init__(self):
        self.state: UserAgentState = None
        self._a2a_client = None
    
    def initialize(
        self, 
        session_id: str, 
        user_name: str = None,
        user_email: str = None
    ):
        """Inicializar estado do Agente Pessoal."""
        self.state = create_initial_state(session_id, user_name, user_email)
        logger.info(
            "User Agent initialized",
            session_id=session_id,
            llm_enabled=is_llm_enabled()
        )
    
    async def process_message(self, message: str) -> str:
        """Processar mensagem do usuario."""
        if not self.state:
            self.initialize("default")
        
        # Adicionar mensagem
        user_msg = Message(role="user", content=message, metadata=None)
        
        input_state = {
            **self.state,
            "messages": self.state["messages"] + [user_msg]
        }
        
        # Executar grafo
        result = await user_agent_graph.ainvoke(input_state)
        
        # Atualizar estado
        self.state = result
        
        # Extrair resposta
        assistant_msgs = [m for m in result.get("messages", []) if m["role"] == "assistant"]
        
        if assistant_msgs:
            return assistant_msgs[-1]["content"]
        
        return "Desculpe, nao entendi. Digite 'ajuda' para ver opcoes."
    
    # === Informacoes Gerais ===
    
    def is_llm_enabled(self) -> bool:
        """Verificar se LLM esta habilitado."""
        return is_llm_enabled()
    
    def get_status(self) -> Dict[str, Any]:
        """Obter status geral do agente."""
        if not self.state:
            return {}
        
        return {
            "session_id": self.state.get("session_id"),
            "llm_enabled": is_llm_enabled(),
            "agents_count": len(self.state.get("connected_agents", {})),
            "stores_count": len(self.state.get("discovered_stores", {})),
            "cart_count": len(self.state.get("cart_items", [])),
            "tools_count": len(self.state.get("mcp_tools", {}))
        }
    
    # === Agentes (A2A) ===
    
    def get_connected_agents(self) -> Dict[str, Any]:
        """Obter agentes A2A conectados."""
        if not self.state:
            return {}
        return self.state.get("connected_agents", {})
    
    def get_a2a_sessions(self) -> Dict[str, Any]:
        """Obter sessoes A2A ativas."""
        if not self.state:
            return {}
        return self.state.get("a2a_sessions", {})
    
    async def connect_agent(self, agent_url: str) -> bool:
        """Conectar a um agente via A2A."""
        from ..clients import A2AClient
        
        try:
            client = A2AClient(agent_url)
            profile = await client.get_agent_card()
            
            if profile:
                self.state["connected_agents"][agent_url] = {
                    "url": agent_url,
                    "name": profile.get("name", "Agente"),
                    "description": profile.get("description", ""),
                    "version": profile.get("version", "1.0"),
                    "skills": [s.get("name", s.get("id")) for s in profile.get("skills", [])],
                    "connected": True
                }
                return True
        except Exception as e:
            logger.error("Failed to connect agent", url=agent_url, error=str(e))
        
        return False
    
    # === Lojas (UCP) ===
    
    def get_discovered_stores(self) -> Dict[str, Any]:
        """Obter lojas UCP descobertas."""
        if not self.state:
            return {}
        return self.state.get("discovered_stores", {})
    
    def get_cart_summary(self) -> Dict[str, Any]:
        """Obter resumo do carrinho."""
        if not self.state:
            return {"items": [], "total": 0, "discount": 0}
        
        return {
            "items": self.state.get("cart_items", []),
            "total": self.state.get("cart_total", 0),
            "discount": self.state.get("discount_amount", 0),
            "applied_discount": self.state.get("applied_discount")
        }
    
    async def connect_store_a2a(self, store_url: str) -> bool:
        """Conectar a uma loja via A2A."""
        from ..clients import A2AClient
        
        try:
            client = A2AClient(store_url)
            connected = await client.connect()
            
            if connected:
                self.state["a2a_sessions"][store_url] = {
                    "store_url": store_url,
                    "agent_id": client.agent_id,
                    "connected": True,
                    "last_message_id": None,
                    "pending_responses": []
                }
                self._a2a_client = client
                return True
        except Exception as e:
            logger.error("Failed to connect A2A", store=store_url, error=str(e))
        
        return False
    
    async def disconnect_a2a(self):
        """Desconectar sessao A2A."""
        if self._a2a_client:
            await self._a2a_client.disconnect()
            self._a2a_client = None
    
    # === Ferramentas (MCP) ===
    
    def get_mcp_tools(self) -> Dict[str, Any]:
        """Obter ferramentas MCP disponiveis."""
        if not self.state:
            return {}
        return self.state.get("mcp_tools", {})
    
    async def register_mcp_server(self, server_url: str) -> bool:
        """Registrar servidor MCP e descobrir ferramentas."""
        try:
            from ..clients import MCPClient
            
            client = MCPClient(server_url)
            tools = await client.list_tools()
            
            if tools:
                for tool in tools:
                    self.state["mcp_tools"][tool.name] = {
                        "name": tool.name,
                        "description": tool.description,
                        "server_url": server_url,
                        "input_schema": tool.input_schema
                    }
                
                if server_url not in self.state["mcp_servers"]:
                    self.state["mcp_servers"].append(server_url)
                
                return True
        except Exception as e:
            logger.error("Failed to register MCP server", url=server_url, error=str(e))
        
        return False
