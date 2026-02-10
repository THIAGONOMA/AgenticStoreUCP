"""
LLM Module - Integracao com Gemini para os Store Agents.

Este modulo fornece uma interface unificada para usar LLMs nos agentes,
permitindo respostas mais naturais e deteccao de intencao inteligente.
"""
from typing import Optional, List, Dict, Any
from functools import lru_cache
import structlog

logger = structlog.get_logger()

# Tentar importar langchain-google-genai
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("langchain-google-genai not installed. LLM features disabled.")


class LLMConfig:
    """Configuracao do LLM usando settings do Pydantic."""
    
    def __init__(self):
        # Importar settings aqui para evitar import circular
        from ..config import settings
        
        self.api_key = settings.google_api_key
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
    
    @property
    def is_configured(self) -> bool:
        """Verifica se o LLM esta configurado."""
        return bool(self.api_key and self.api_key != "your-google-api-key-here" and len(self.api_key) > 10)


@lru_cache()
def get_llm_config() -> LLMConfig:
    """Obter configuracao do LLM (cached)."""
    return LLMConfig()


def get_llm() -> Optional[Any]:
    """
    Obter instancia do LLM.
    
    Returns:
        ChatGoogleGenerativeAI ou None se nao configurado
    """
    if not GEMINI_AVAILABLE:
        return None
    
    config = get_llm_config()
    
    if not config.is_configured:
        logger.debug("LLM not configured, using rule-based fallback")
        return None
    
    try:
        llm = ChatGoogleGenerativeAI(
            model=config.model,
            google_api_key=config.api_key,
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
        )
        return llm
    except Exception as e:
        logger.error("Failed to initialize LLM", error=str(e))
        return None


# ============================================================
# Funcoes de Alto Nivel para os Agentes
# ============================================================

INTENT_DETECTION_PROMPT = """Voce e um assistente de uma livraria virtual.
Analise a mensagem do usuario e determine a intencao.

Intencoes possiveis:
- buy: O usuario quer comprar um livro especifico (ex: "quero comprar esse", "vou levar esse livro", "quero esse Clean Code")
- search: O usuario quer buscar/encontrar livros (ex: "buscar livros de python", "tem livros de fantasia?")
- recommend: O usuario quer recomendacoes de livros (ex: "me recomende", "sugira livros")
- cart: O usuario quer manipular o carrinho (ex: "adicionar ao carrinho", "ver meu carrinho", "remover item")
- checkout: O usuario quer finalizar compra/pagar (ex: "finalizar pedido", "quero pagar", "fechar compra")
- discount: O usuario quer aplicar cupom/desconto (ex: "tenho cupom", "aplicar desconto")
- help: O usuario precisa de ajuda ou esta cumprimentando (ex: "ola", "ajuda", "como funciona")

Mensagem do usuario: {message}

Responda APENAS com uma das intencoes listadas acima, nada mais."""


async def detect_intent_with_llm(message: str) -> Optional[str]:
    """
    Detectar intencao usando LLM.
    
    Args:
        message: Mensagem do usuario
        
    Returns:
        Intent detectado ou None se LLM nao disponivel
    """
    llm = get_llm()
    if not llm:
        return None
    
    try:
        prompt = INTENT_DETECTION_PROMPT.format(message=message)
        response = await llm.ainvoke(prompt)
        intent = response.content.strip().lower()
        
        # Validar intent
        valid_intents = ["buy", "search", "recommend", "cart", "checkout", "discount", "help"]
        if intent in valid_intents:
            logger.debug("LLM detected intent", intent=intent, message=message[:30])
            return intent
        
        # Tentar extrair intent se resposta mais longa
        for valid in valid_intents:
            if valid in intent:
                return valid
        
        return None
        
    except Exception as e:
        logger.error("LLM intent detection failed", error=str(e))
        return None


RESPONSE_GENERATION_PROMPT = """Voce e um assistente amigavel de uma livraria virtual chamada "Livraria Virtual UCP".
Sua personalidade e: educado, prestativo, entusiasmado com livros.

Contexto atual:
{context}

Dados disponiveis:
{data}

Gere uma resposta natural e amigavel para o usuario.
Mantenha a resposta concisa (maximo 3-4 frases por secao).
Use emojis com moderacao.
Se houver lista de livros, formate de forma clara com numeros."""


async def generate_response_with_llm(
    context: str,
    data: Dict[str, Any],
    fallback_response: str
) -> str:
    """
    Gerar resposta usando LLM.
    
    Args:
        context: Contexto da conversa (ex: "usuario buscou livros de python")
        data: Dados para incluir na resposta (ex: lista de livros)
        fallback_response: Resposta a usar se LLM nao disponivel
        
    Returns:
        Resposta gerada
    """
    llm = get_llm()
    if not llm:
        return fallback_response
    
    try:
        # Formatar dados
        data_str = _format_data_for_prompt(data)
        
        prompt = RESPONSE_GENERATION_PROMPT.format(
            context=context,
            data=data_str
        )
        
        response = await llm.ainvoke(prompt)
        generated = response.content.strip()
        
        # Validar resposta
        if len(generated) > 50:  # Resposta minimamente util
            logger.debug("LLM generated response", length=len(generated))
            return generated
        
        return fallback_response
        
    except Exception as e:
        logger.error("LLM response generation failed", error=str(e))
        return fallback_response


def _format_data_for_prompt(data: Dict[str, Any]) -> str:
    """Formatar dados para incluir no prompt."""
    lines = []
    
    if "books" in data:
        lines.append("Livros encontrados:")
        for i, book in enumerate(data["books"][:5], 1):
            price = book.get("price", 0)
            price_fmt = f"R$ {price / 100:.2f}" if isinstance(price, int) else price
            lines.append(f"  {i}. {book.get('title', 'N/A')} - {book.get('author', 'N/A')} - {price_fmt}")
    
    if "categories" in data:
        lines.append(f"Categorias: {', '.join(data['categories'])}")
    
    if "cart_items" in data:
        lines.append(f"Itens no carrinho: {len(data['cart_items'])}")
        total = data.get("cart_total", 0)
        lines.append(f"Total: R$ {total / 100:.2f}")
    
    if "message" in data:
        lines.append(f"Info: {data['message']}")
    
    return "\n".join(lines) if lines else "Nenhum dado especifico."


# ============================================================
# Funcao de Verificacao
# ============================================================

def is_llm_enabled() -> bool:
    """Verifica se o LLM esta habilitado e configurado."""
    if not GEMINI_AVAILABLE:
        return False
    
    config = get_llm_config()
    return config.is_configured


def get_llm_status() -> Dict[str, Any]:
    """Retorna status do LLM."""
    config = get_llm_config()
    
    return {
        "available": GEMINI_AVAILABLE,
        "configured": config.is_configured,
        "model": config.model if config.is_configured else None,
        "temperature": config.temperature if config.is_configured else None,
    }
