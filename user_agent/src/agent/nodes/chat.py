"""Chat Node - Conversa via A2A com Store Agent."""
from typing import Dict, Any, List
import structlog

from ..state import UserAgentState, Message, A2ASession
from ..llm import generate_response, is_llm_enabled
from ...clients import A2AClient
from ...config import settings

logger = structlog.get_logger()


async def chat_node(state: UserAgentState) -> Dict[str, Any]:
    """
    Chat Node - Conversa via A2A com Store Agent.
    
    Responsavel por:
    - Conectar via A2A a lojas
    - Enviar mensagens ao Store Agent
    - Processar respostas e manter contexto
    """
    logger.info("Chat node processing", session=state["session_id"])
    
    messages = []
    a2a_sessions = dict(state.get("a2a_sessions", {}))
    
    # Pegar ultima mensagem do usuario
    user_messages = [m for m in state["messages"] if m["role"] == "user"]
    if not user_messages:
        messages.append(Message(
            role="assistant",
            content="Como posso ajudar?",
            metadata=None
        ))
        return {"messages": messages, "next_action": None}
    
    last_message = user_messages[-1]["content"]
    intent_params = state.get("intent_params", {})
    
    # Determinar loja alvo
    active_store = state.get("active_store_url")
    discovered_stores = state.get("discovered_stores", {})
    
    if not active_store and discovered_stores:
        # Usar primeira loja descoberta
        active_store = list(discovered_stores.keys())[0]
    
    if not active_store:
        # Nenhuma loja conectada - sugerir descoberta
        response = (
            "Nenhuma loja conectada ainda.\n\n"
            "Para comecar, descubra uma loja:\n"
            "`descobrir http://localhost:8182`"
        )
        messages.append(Message(role="assistant", content=response, metadata=None))
        return {
            "messages": messages,
            "next_action": None
        }
    
    # Verificar se tem sessao A2A ativa
    session = a2a_sessions.get(active_store)
    
    if not session or not session.get("connected"):
        # Conectar via A2A
        result = await _connect_a2a(active_store, a2a_sessions)
        if result["success"]:
            a2a_sessions = result["sessions"]
            session = a2a_sessions[active_store]
        else:
            # Falhou - usar resposta alternativa
            response = await _generate_fallback_response(
                last_message, 
                state,
                f"Nao foi possivel conectar via A2A: {result.get('error')}"
            )
            messages.append(Message(role="assistant", content=response, metadata=None))
            return {
                "messages": messages,
                "a2a_sessions": a2a_sessions,
                "next_action": None
            }
    
    # Enviar mensagem via A2A
    result = await _send_a2a_message(active_store, last_message, state)
    
    if result["success"]:
        response = result["response"]
        
        # Processar dados retornados (produtos, carrinho, etc)
        response_data = result.get("data", {})
        
        # Atualizar resultados de busca se houver
        search_results = response_data.get("products", [])
        if search_results:
            # Formatar resultados
            formatted = await _format_a2a_response(response, search_results, state)
            response = formatted if formatted else response
        
        messages.append(Message(
            role="assistant",
            content=response,
            metadata={"a2a": True, "store": active_store}
        ))
        
        return {
            "messages": messages,
            "a2a_sessions": a2a_sessions,
            "active_store_url": active_store,
            "search_results": search_results if search_results else state.get("search_results", []),
            "next_action": None
        }
    else:
        # Erro na comunicacao
        error_msg = result.get("error", "Erro desconhecido")
        response = f"Erro na comunicacao com a loja: {error_msg}"
        
        messages.append(Message(role="assistant", content=response, metadata=None))
        return {
            "messages": messages,
            "a2a_sessions": a2a_sessions,
            "error": error_msg,
            "next_action": None
        }


async def _connect_a2a(
    store_url: str,
    current_sessions: Dict[str, A2ASession]
) -> Dict[str, Any]:
    """Conectar a uma loja via A2A."""
    try:
        # Construir URL do WebSocket A2A
        ws_url = store_url.replace("http://", "ws://").replace("https://", "wss://")
        
        # Se for UCP Server (8182), redirecionar para API Gateway (8000)
        if ":8182" in ws_url:
            ws_url = ws_url.replace(":8182", ":8000")
        
        async with A2AClient(ws_url) as client:
            connected = await client.connect()
            
            if connected:
                current_sessions[store_url] = A2ASession(
                    store_url=store_url,
                    agent_id=client.agent_id,
                    connected=True,
                    last_message_id=None,
                    pending_responses=[]
                )
                
                logger.info("A2A connected", store=store_url, agent=client.agent_id)
                return {"success": True, "sessions": current_sessions}
        
        return {"success": False, "error": "Connection failed", "sessions": current_sessions}
        
    except Exception as e:
        logger.error("A2A connection error", store=store_url, error=str(e))
        return {"success": False, "error": str(e), "sessions": current_sessions}


async def _send_a2a_message(
    store_url: str,
    message: str,
    state: UserAgentState
) -> Dict[str, Any]:
    """Enviar mensagem via A2A e aguardar resposta."""
    try:
        # Construir URL do WebSocket A2A
        ws_url = store_url.replace("http://", "ws://").replace("https://", "wss://")
        if ":8182" in ws_url:
            ws_url = ws_url.replace(":8182", ":8000")
        
        async with A2AClient(ws_url) as client:
            if not await client.connect():
                return {"success": False, "error": "Connection failed"}
            
            # Determinar acao baseada no contexto
            intent = state.get("current_intent", "chat")
            
            if intent == "search" or "buscar" in message.lower():
                # Busca de produtos
                query = state.get("intent_params", {}).get("query", message)
                result = await client.search(query)
                
                if result.success:
                    products = result.data.get("products", result.data.get("results", []))
                    return {
                        "success": True,
                        "response": result.data.get("message", f"Encontrei {len(products)} resultado(s)"),
                        "data": {"products": products}
                    }
                else:
                    return {"success": False, "error": result.error}
            
            elif intent == "recommend":
                # Recomendacoes
                result = await client.get_recommendations()
                if result.success:
                    return {
                        "success": True,
                        "response": result.data.get("message", "Recomendacoes"),
                        "data": result.data
                    }
                else:
                    return {"success": False, "error": result.error}
            
            else:
                # Mensagem generica - enviar como chat
                # O A2A client nao tem metodo de chat generico, 
                # vamos usar busca como fallback
                result = await client.search(message)
                
                if result.success:
                    return {
                        "success": True,
                        "response": result.data.get("message", "Resposta da loja"),
                        "data": result.data
                    }
                else:
                    # Gerar resposta local
                    response = await _generate_fallback_response(message, state)
                    return {"success": True, "response": response, "data": {}}
                    
    except Exception as e:
        logger.error("A2A message error", error=str(e))
        return {"success": False, "error": str(e)}


async def _format_a2a_response(
    original_response: str,
    products: List[Dict[str, Any]],
    state: UserAgentState
) -> str:
    """Formatar resposta A2A com produtos encontrados."""
    if not products:
        return original_response
    
    # Adicionar URL da loja aos produtos
    active_store = state.get("active_store_url", "")
    for p in products:
        if "store_url" not in p:
            p["store_url"] = active_store
    
    # Formatar lista de produtos
    lines = [f"**Encontrei {len(products)} produto(s):**\n"]
    
    for i, p in enumerate(products[:10], 1):
        price = p.get("price", 0)
        price_fmt = f"R$ {price / 100:.2f}" if price else "Preco nao disponivel"
        
        lines.append(
            f"{i}. **{p.get('title', 'Sem titulo')}**\n"
            f"   {p.get('author', 'Autor desconhecido')} - {price_fmt}"
        )
    
    lines.append("\nDiga `adicionar [numero]` para colocar no carrinho.")
    
    return "\n".join(lines)


async def _generate_fallback_response(
    message: str,
    state: UserAgentState,
    context: str = None
) -> str:
    """Gerar resposta quando A2A nao esta disponivel."""
    if is_llm_enabled():
        # Usar LLM para gerar resposta
        try:
            ctx = {
                "stores": list(state.get("discovered_stores", {}).keys()),
                "cart_items": len(state.get("cart_items", [])),
                "context": context
            }
            
            response = await generate_response(
                message,
                context=ctx,
                system_prompt=(
                    "Voce e um assistente de compras. "
                    "A conexao A2A com a loja nao esta disponivel no momento. "
                    "Ajude o usuario de forma alternativa ou sugira usar UCP diretamente."
                )
            )
            
            if response:
                return response
        except Exception as e:
            logger.error("LLM fallback failed", error=str(e))
    
    # Fallback simples
    if context:
        return f"{context}\n\nTente usar 'buscar [termo]' para pesquisar via UCP."
    
    return (
        "Nao consegui processar sua mensagem via A2A.\n\n"
        "Voce pode:\n"
        "- `buscar [termo]` - Buscar produtos via UCP\n"
        "- `descobrir [url]` - Conectar a outra loja\n"
        "- `carrinho` - Ver seu carrinho"
    )
