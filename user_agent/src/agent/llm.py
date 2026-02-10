"""LLM Integration - Gemini para User Agent."""
import json
from typing import Dict, Any, Optional, List
import structlog

from ..config import settings

logger = structlog.get_logger()

# Flag para verificar se LLM está disponível
_llm_available: Optional[bool] = None
_llm_instance = None


def is_llm_enabled() -> bool:
    """Verificar se LLM está habilitado e configurado."""
    global _llm_available
    
    if _llm_available is not None:
        return _llm_available
    
    # Verificar se tem chave do Google
    if settings.google_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            _llm_available = True
            logger.info("LLM enabled", provider="google", model=settings.gemini_model)
            return True
        except ImportError:
            logger.warning("langchain-google-genai not installed")
    
    # Verificar fallbacks
    if settings.openai_api_key:
        try:
            from langchain_openai import ChatOpenAI
            _llm_available = True
            logger.info("LLM enabled", provider="openai", model=settings.llm_model)
            return True
        except ImportError:
            pass
    
    _llm_available = False
    logger.warning("LLM not available - using keyword detection")
    return False


def get_llm():
    """Obter instância do LLM."""
    global _llm_instance
    
    if _llm_instance is not None:
        return _llm_instance
    
    if not is_llm_enabled():
        return None
    
    # Tentar Gemini primeiro
    if settings.google_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            _llm_instance = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.google_api_key,
                temperature=0.3,
                convert_system_message_to_human=True
            )
            logger.info("Using Gemini", model=settings.gemini_model)
            return _llm_instance
        except Exception as e:
            logger.error("Failed to init Gemini", error=str(e))
    
    # Fallback para OpenAI
    if settings.openai_api_key:
        try:
            from langchain_openai import ChatOpenAI
            _llm_instance = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.openai_api_key,
                temperature=0.3
            )
            logger.info("Using OpenAI", model=settings.llm_model)
            return _llm_instance
        except Exception as e:
            logger.error("Failed to init OpenAI", error=str(e))
    
    return None


# System prompt para o User Agent - Agente Pessoal Generico
USER_AGENT_SYSTEM_PROMPT = """Voce e um assistente pessoal inteligente chamado User Agent.
Voce e o agente autonomo do usuario, capaz de realizar diversas tarefas e interagir com outros agentes.

Suas capacidades principais:

1. CONVERSACAO GERAL
   - Responder perguntas gerais sobre qualquer assunto
   - Ajudar com tarefas do dia-a-dia
   - Fornecer informacoes e explicacoes

2. DESCOBERTA DE AGENTES (A2A)
   - Descobrir outros agentes por URL
   - Conectar e conversar com agentes especializados
   - Delegar tarefas para agentes apropriados

3. COMERCIO AUTONOMO (UCP)
   - Descobrir lojas UCP por URL
   - Buscar produtos em multiplas lojas
   - Comparar precos entre lojas
   - Gerenciar carrinho de compras (multi-loja)
   - Finalizar compras com pagamento autonomo (AP2)

4. FERRAMENTAS EXTERNAS (MCP)
   - Usar ferramentas disponibilizadas por servidores MCP
   - Executar acoes no mundo real quando necessario

Voce e o representante autonomo do usuario. Quando precisar fazer uma compra,
VOCE gera o mandato de pagamento (AP2) - a autorizacao esta com voce.

Responda de forma concisa, util e amigavel em portugues brasileiro."""


INTENT_DETECTION_PROMPT = """Analise a mensagem do usuario e retorne um JSON com a intencao detectada.

REGRAS IMPORTANTES:
1. "comprar", "finalizar", "pagar", "checkout" -> checkout (NAO discover!)
2. "descobrir http://..." ou "conectar loja" -> discover (loja UCP)
3. "descobrir agente" ou "conectar agente" -> discover_agent (A2A)

INTENCOES GERAIS:
- question: pergunta geral que requer resposta direta (sobre qualquer assunto)
- chat: conversa casual, saudacao ou comentario

INTENCOES DE AGENTES (A2A) - use APENAS se mencionar "agente" explicitamente:
- discover_agent: SOMENTE se disser "descobrir AGENTE" ou "conectar AGENTE" (extrair URL)
- list_agents: listar agentes conectados (ex: "listar agentes", "meus agentes")
- talk_to_agent: enviar mensagem para um agente especifico

INTENCOES DE COMERCIO (UCP):
- checkout: "comprar", "finalizar compra", "pagar", "checkout", "concluir" -> USAR ESTA!
- discover: "descobrir loja", "conectar loja", URL sem "comprar" -> descobrir loja UCP
- search: buscar produtos (extrair termo de busca)
- compare: comparar produtos (extrair numeros dos itens)
- add_to_cart: adicionar item ao carrinho (extrair numero do item)
- remove_from_cart: remover item do carrinho (extrair numero)
- view_cart: ver carrinho atual
- apply_discount: aplicar cupom de desconto (extrair codigo)

INTENCOES DE FERRAMENTAS (MCP):
- use_tool: usar uma ferramenta MCP especifica (extrair nome da ferramenta)
- list_tools: listar ferramentas disponiveis

OUTRAS:
- help: pedido de ajuda sobre o que o agente pode fazer

EXTRACAO DE PARAMETROS - MUITO IMPORTANTE:
- Se a mensagem contem uma URL (http:// ou https://), SEMPRE extraia em params.url
- Se a mensagem contem um numero de item, extraia em params.item_number
- Se a mensagem contem termo de busca, extraia em params.query

Mensagem do usuario: {message}

Contexto:
- Agentes conectados: {agents}
- Lojas conectadas: {stores}
- Itens no carrinho: {cart_count}
- Ultima busca: {last_search}
- Ferramentas MCP disponiveis: {mcp_tools}

Responda APENAS com JSON no formato:
{{"intent": "...", "params": {{"key": "value"}}, "confidence": 0.0-1.0}}"""


async def detect_intent_with_llm(
    message: str,
    agents: List[str] = None,
    stores: List[str] = None,
    cart_count: int = 0,
    last_search: str = None,
    mcp_tools: List[str] = None
) -> Dict[str, Any]:
    """
    Detectar intencao usando LLM.
    
    Args:
        message: Mensagem do usuario
        agents: Lista de agentes conectados (A2A)
        stores: Lista de lojas conectadas (UCP)
        cart_count: Quantidade de itens no carrinho
        last_search: Ultimo termo buscado
        mcp_tools: Lista de ferramentas MCP disponiveis
        
    Returns:
        Dict com intent, params e confidence
    """
    llm = get_llm()
    
    if not llm:
        # Fallback para detecção por keywords
        return _detect_intent_keywords(message)
    
    try:
        prompt = INTENT_DETECTION_PROMPT.format(
            message=message,
            agents=", ".join(agents) if agents else "nenhum",
            stores=", ".join(stores) if stores else "nenhuma",
            cart_count=cart_count,
            last_search=last_search or "nenhuma",
            mcp_tools=", ".join(mcp_tools) if mcp_tools else "nenhuma"
        )
        
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        
        # Extrair JSON da resposta
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        result = json.loads(content)
        
        logger.info(
            "Intent detected via LLM",
            intent=result.get("intent"),
            confidence=result.get("confidence")
        )
        
        return result
        
    except Exception as e:
        logger.warning("LLM intent detection failed, using keywords", error=str(e))
        return _detect_intent_keywords(message)


def _detect_intent_keywords(message: str) -> Dict[str, Any]:
    """Fallback: detectar intencao por palavras-chave."""
    message_lower = message.lower()
    
    # Verificar primeiro se é sobre agentes (mais específico)
    is_agent_related = "agente" in message_lower
    
    # Mapeamento de keywords para intencoes (ordem importa - mais especifico primeiro)
    intent_keywords = {
        # Agentes (A2A) - APENAS se mencionar "agente"
        "discover_agent": ["descobrir agente", "conectar agente", "agente em", "agente http"],
        "list_agents": ["listar agentes", "meus agentes", "agentes conectados"],
        "talk_to_agent": ["falar com agente", "perguntar ao agente", "enviar para agente"],
        
        # CHECKOUT PRIMEIRO - "comprar" deve ser checkout, nao discover
        "checkout": ["comprar", "finalizar", "pagar", "checkout", "concluir compra", "finalizar compra"],
        
        # Comercio (UCP) - Padrao para URLs sem "agente"
        "discover": ["descobrir http", "conectar http", "loja http", "descobrir loja", "conectar loja"],
        "search": ["buscar", "procurar", "encontrar", "pesquisar"],
        "compare": ["comparar", "comparacao", "diferenca", "melhor preco", "versus"],
        "add_to_cart": ["adicionar", "colocar no carrinho", "incluir", "add"],
        "remove_from_cart": ["remover", "tirar", "excluir do carrinho", "deletar"],
        "view_cart": ["carrinho", "cart", "ver carrinho", "meu carrinho"],
        "apply_discount": ["cupom", "desconto", "codigo promocional", "promocao"],
        
        # Ferramentas (MCP)
        "use_tool": ["usar ferramenta", "executar", "rodar"],
        "list_tools": ["listar ferramentas", "ferramentas disponiveis", "quais ferramentas"],
        
        # Geral
        "help": ["ajuda", "help", "opcoes", "o que voce pode", "comandos"],
        "question": ["o que e", "como funciona", "por que", "quando", "onde", "quem", 
                     "explique", "me diga", "qual", "quantos", "quanto"],
        "chat": []  # Default para conversas casuais
    }
    
    # Detectar intent - verificar keywords mais específicas primeiro
    detected_intent = "chat"
    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in message_lower:
                detected_intent = intent
                break
        if detected_intent != "chat":
            break
    
    # Se começa com saudação, é chat
    greetings = ["oi", "ola", "bom dia", "boa tarde", "boa noite", "e ai", "hey"]
    first_word = message_lower.split()[0] if message_lower.split() else ""
    if first_word in greetings and detected_intent == "chat":
        detected_intent = "chat"
    
    # Extrair parametros
    params = {}
    
    # URLs
    import re
    urls = re.findall(r'https?://[^\s]+', message)
    if urls:
        params["url"] = urls[0]
        # Se tem URL e nao detectou intent especifico
        if detected_intent == "chat":
            # Verificar se menciona "agente" - se sim, discover_agent, senao discover (loja)
            if "agente" in message_lower:
                detected_intent = "discover_agent"
            else:
                detected_intent = "discover"  # Padrao: loja UCP
    
    # Numeros (para adicionar/remover itens)
    numbers = re.findall(r'\b\d+\b', message)
    if numbers:
        params["item_number"] = int(numbers[0])
    
    # Termo de busca (remover stop words)
    if detected_intent == "search":
        stop_words = ["buscar", "procurar", "encontrar", "quero", "preciso", 
                      "livro", "livros", "produto", "produtos",
                      "de", "sobre", "um", "uma", "o", "a", "para", "por"]
        words = message_lower.split()
        search_terms = [w for w in words if w not in stop_words and len(w) > 2]
        if search_terms:
            params["query"] = " ".join(search_terms)
    
    # Se é uma pergunta (termina com ?), provavelmente é question
    if message.strip().endswith("?") and detected_intent == "chat":
        detected_intent = "question"
        params["question"] = message
    
    return {
        "intent": detected_intent,
        "params": params,
        "confidence": 0.7  # Keywords tem confianca menor
    }


async def generate_response(
    message: str,
    context: Dict[str, Any] = None,
    system_prompt: str = None
) -> str:
    """
    Gerar resposta usando LLM.
    
    Args:
        message: Mensagem para responder
        context: Contexto adicional (carrinho, busca, etc)
        system_prompt: Prompt de sistema customizado
        
    Returns:
        Resposta gerada
    """
    llm = get_llm()
    
    if not llm:
        return None
    
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = [
            SystemMessage(content=system_prompt or USER_AGENT_SYSTEM_PROMPT)
        ]
        
        # Adicionar contexto se disponível
        if context:
            context_str = f"\nContexto atual:\n{json.dumps(context, indent=2, ensure_ascii=False)}"
            messages.append(HumanMessage(content=f"{message}{context_str}"))
        else:
            messages.append(HumanMessage(content=message))
        
        response = await llm.ainvoke(messages)
        return response.content
        
    except Exception as e:
        logger.error("LLM response generation failed", error=str(e))
        return None


async def format_search_results_with_llm(
    results: List[Dict[str, Any]],
    query: str
) -> str:
    """Formatar resultados de busca de forma natural usando LLM."""
    llm = get_llm()
    
    if not llm or not results:
        return None
    
    try:
        prompt = f"""Formate os seguintes resultados de busca de forma amigavel e concisa.
        
Busca: "{query}"
Resultados:
{json.dumps(results[:10], indent=2, ensure_ascii=False)}

Inclua:
- Numero do item para referencia (1, 2, 3...)
- Titulo, autor e preco
- Agrupe por loja se houver multiplas
- Instrucao de como adicionar ao carrinho

Responda em portugues brasileiro."""

        response = await llm.ainvoke(prompt)
        return response.content
        
    except Exception as e:
        logger.error("Failed to format results with LLM", error=str(e))
        return None
