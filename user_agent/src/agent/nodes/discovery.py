"""Discovery Node - Descoberta de lojas UCP."""
from typing import Dict, Any, List
import structlog

from ..state import UserAgentState, StoreInfo, Message
from ...clients import UCPClient

logger = structlog.get_logger()


async def discovery_node(state: UserAgentState) -> Dict[str, Any]:
    """
    Discovery Node - Descobrir e conectar a lojas UCP.
    
    Responsavel por:
    - Descobrir lojas por URL
    - Listar capacidades
    - Buscar produtos em lojas
    """
    logger.info("Discovery node processing", session=state["session_id"])
    
    messages = []
    discovered_stores = dict(state.get("discovered_stores", {}))
    search_results = []
    
    # Verificar intent
    intent = state.get("current_intent", "discover")
    
    # Pegar ultima mensagem do usuario
    user_messages = [m for m in state["messages"] if m["role"] == "user"]
    last_message = user_messages[-1]["content"] if user_messages else ""
    
    if intent == "discover":
        # Extrair URLs da mensagem ou usar default
        urls = _extract_urls(last_message)
        
        if not urls:
            urls = ["http://localhost:8182"]  # Loja local
        
        for url in urls:
            if url not in discovered_stores:
                store_info = await _discover_store(url)
                if store_info:
                    discovered_stores[url] = store_info
        
        response = _format_discovered_stores(discovered_stores)
        messages.append(Message(role="assistant", content=response))
    
    elif intent == "search":
        # Buscar em todas as lojas conectadas
        query = _extract_search_term(last_message)
        active_store = state.get("active_store_url")
        
        if active_store and active_store in discovered_stores:
            # Buscar apenas na loja ativa
            results = await _search_store(active_store, query)
            search_results.extend(results)
        else:
            # Buscar em todas
            for url in discovered_stores:
                results = await _search_store(url, query)
                search_results.extend(results)
        
        response = _format_search_results(search_results, query)
        messages.append(Message(role="assistant", content=response))
    
    return {
        "messages": messages,
        "discovered_stores": discovered_stores,
        "search_results": search_results,
        "search_query": _extract_search_term(last_message) if intent == "search" else None,
        "next_action": None
    }


async def _discover_store(url: str) -> StoreInfo:
    """Descobrir uma loja UCP."""
    try:
        async with UCPClient(url) as client:
            profile = await client.discover()
            
            if profile:
                logger.info("Store discovered", name=profile.name, url=url)
                return StoreInfo(
                    url=url,
                    name=profile.name,
                    version=profile.version,
                    connected=True,
                    capabilities=list(profile.capabilities.keys()) if profile.capabilities else []
                )
    except Exception as e:
        logger.error("Store discovery failed", url=url, error=str(e))
    
    return None


async def _search_store(url: str, query: str) -> List[Dict[str, Any]]:
    """Buscar produtos em uma loja."""
    results = []
    
    try:
        async with UCPClient(url) as client:
            await client.discover()
            products = await client.search_products(query)
            
            for p in products:
                results.append({
                    "store_url": url,
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "author": p.get("author"),
                    "price": p.get("price"),
                    "price_formatted": f"R$ {p.get('price', 0) / 100:.2f}",
                    "category": p.get("category")
                })
    except Exception as e:
        logger.error("Store search failed", url=url, error=str(e))
    
    return results


def _extract_urls(message: str) -> List[str]:
    """Extrair URLs da mensagem."""
    import re
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, message)
    return urls


def _extract_search_term(message: str) -> str:
    """Extrair termo de busca."""
    stop_words = [
        "buscar", "procurar", "encontrar", "quero", "preciso",
        "livro", "livros", "de", "sobre", "um", "uma", "o", "a",
        "na", "no", "em", "todas", "lojas"
    ]
    
    words = message.lower().split()
    filtered = [w for w in words if w not in stop_words and len(w) > 2]
    
    return " ".join(filtered) if filtered else ""


def _format_discovered_stores(stores: Dict[str, StoreInfo]) -> str:
    """Formatar lojas descobertas."""
    if not stores:
        return "Nenhuma loja UCP encontrada. Informe uma URL para descobrir."
    
    lines = ["**Lojas UCP Descobertas:**\n"]
    
    for url, info in stores.items():
        status = "✅" if info["connected"] else "❌"
        lines.append(f"{status} **{info['name']}**")
        lines.append(f"   URL: {url}")
        lines.append(f"   Versao: {info['version']}")
        if info["capabilities"]:
            lines.append(f"   Capacidades: {', '.join(info['capabilities'][:3])}...")
        lines.append("")
    
    lines.append("Use 'buscar [termo]' para procurar produtos.")
    
    return "\n".join(lines)


def _format_search_results(results: List[Dict], query: str) -> str:
    """Formatar resultados de busca."""
    if not results:
        return f"Nenhum resultado para '{query}'."
    
    lines = [f"**Resultados para '{query}':**\n"]
    
    current_store = None
    for i, item in enumerate(results[:10], 1):
        if item["store_url"] != current_store:
            current_store = item["store_url"]
            lines.append(f"\n📚 **{current_store}**\n")
        
        lines.append(
            f"{i}. **{item['title']}**\n"
            f"   {item['author']} - {item['price_formatted']}\n"
        )
    
    lines.append("\nDiga 'adicionar [numero]' ou 'comparar [numeros]'.")
    
    return "\n".join(lines)
