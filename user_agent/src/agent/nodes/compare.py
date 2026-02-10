"""Compare Node - Comparacao de precos entre lojas."""
from typing import Dict, Any, List
import structlog

from ..state import UserAgentState, Message

logger = structlog.get_logger()


async def compare_node(state: UserAgentState) -> Dict[str, Any]:
    """
    Compare Node - Comparar produtos entre lojas.
    
    Responsavel por:
    - Comparar precos do mesmo produto
    - Encontrar melhores ofertas
    - Sugerir onde comprar
    """
    logger.info("Compare node processing", session=state["session_id"])
    
    messages = []
    comparison_items = list(state.get("comparison_items", []))
    
    # Pegar ultima mensagem
    user_messages = [m for m in state["messages"] if m["role"] == "user"]
    last_message = user_messages[-1]["content"].lower() if user_messages else ""
    
    if "comparar" in last_message:
        # Extrair indices para comparacao
        import re
        numbers = re.findall(r'\d+', last_message)
        
        search_results = state.get("search_results", [])
        
        if numbers and len(numbers) >= 2:
            indices = [int(n) - 1 for n in numbers]
            items_to_compare = []
            
            for idx in indices:
                if 0 <= idx < len(search_results):
                    items_to_compare.append(search_results[idx])
            
            if items_to_compare:
                comparison_items = items_to_compare
                response = _format_comparison(items_to_compare)
            else:
                response = "Nao encontrei os itens para comparar."
        else:
            # Comparar automaticamente itens similares
            response = _auto_compare(search_results)
    
    else:
        # Mostrar comparacao atual
        if comparison_items:
            response = _format_comparison(comparison_items)
        else:
            response = "Diga 'comparar [numero1] [numero2]' apos buscar produtos."
    
    messages.append(Message(role="assistant", content=response))
    
    return {
        "messages": messages,
        "comparison_items": comparison_items,
        "next_action": None
    }


def _format_comparison(items: List[Dict[str, Any]]) -> str:
    """Formatar comparacao de itens."""
    if not items:
        return "Nenhum item para comparar."
    
    lines = ["📊 **Comparacao de Precos:**\n"]
    
    # Ordenar por preco
    sorted_items = sorted(items, key=lambda x: x.get("price", 0))
    
    best_price = sorted_items[0]["price"] if sorted_items else 0
    
    for i, item in enumerate(sorted_items, 1):
        price = item.get("price", 0)
        is_best = price == best_price
        
        badge = "🏆 MELHOR PRECO" if is_best else ""
        
        lines.append(
            f"{i}. **{item.get('title', 'N/A')}** {badge}\n"
            f"   Autor: {item.get('author', 'N/A')}\n"
            f"   Preco: {item.get('price_formatted', 'N/A')}\n"
            f"   Loja: {item.get('store_url', 'N/A')}\n"
        )
    
    # Calcular economia
    if len(sorted_items) >= 2:
        savings = sorted_items[-1]["price"] - sorted_items[0]["price"]
        if savings > 0:
            lines.append(f"\n💰 **Economia potencial:** R$ {savings / 100:.2f}")
    
    lines.append("\nDiga 'adicionar [numero]' para colocar no carrinho.")
    
    return "\n".join(lines)


def _auto_compare(search_results: List[Dict[str, Any]]) -> str:
    """Comparacao automatica de resultados similares."""
    if not search_results or len(search_results) < 2:
        return "Busque produtos em multiplas lojas para comparar."
    
    # Agrupar por titulo similar
    groups = {}
    for item in search_results:
        title = item.get("title", "").lower()
        # Simplificar titulo para agrupamento
        key = title.split(":")[0].strip()[:30]
        
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    
    # Encontrar grupos com multiplos itens
    comparable = {k: v for k, v in groups.items() if len(v) > 1}
    
    if not comparable:
        return (
            "Nao encontrei produtos identicos entre lojas.\n"
            "Use 'comparar [num1] [num2]' para comparar manualmente."
        )
    
    lines = ["📊 **Produtos similares encontrados:**\n"]
    
    for key, items in list(comparable.items())[:3]:
        sorted_items = sorted(items, key=lambda x: x.get("price", 0))
        best = sorted_items[0]
        
        lines.append(f"**{best.get('title', key)}**")
        for item in sorted_items:
            price = item.get("price_formatted", "N/A")
            store = item.get("store_url", "N/A")
            is_best = item == best
            marker = " 🏆" if is_best else ""
            lines.append(f"  - {price} ({store}){marker}")
        lines.append("")
    
    return "\n".join(lines)
