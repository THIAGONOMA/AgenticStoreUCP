"""Recommend Node - Recomendacoes de livros."""
from typing import Dict, Any, List
import structlog
import random

from ..state import StoreAgentState, Message
from ..llm import generate_response_with_llm, is_llm_enabled
from ...db.products import products_repo

logger = structlog.get_logger()


async def recommend_node(state: StoreAgentState) -> Dict[str, Any]:
    """
    Recommend Node - Gera recomendacoes de livros.
    
    Responsavel por:
    - Recomendar com base em categoria
    - Recomendar com base em livro selecionado
    - Recomendar com base no carrinho
    - Recomendacoes gerais/populares
    """
    logger.info("Recommend node processing", session=state["session_id"])
    
    messages = []
    recommendations = []
    
    # Verificar se e requisicao A2A
    if state.get("a2a_request"):
        return await _handle_a2a_recommend(state)
    
    # Pegar ultima mensagem do usuario
    user_messages = [m for m in state["messages"] if m["type"] == "user"]
    last_message = user_messages[-1]["content"].lower() if user_messages else ""
    
    # Determinar tipo de recomendacao
    context = ""
    if state.get("selected_book_id"):
        # Baseado em livro selecionado
        recommendations = await _recommend_by_book(state["selected_book_id"])
        context = "Usuario viu um livro especifico e quer similares"
        fallback = _format_recommendations(recommendations, "baseado no livro que voce viu")
    
    elif state.get("cart_items"):
        # Baseado no carrinho
        categories = set()
        for item in state["cart_items"]:
            book = await products_repo.get_by_id(item["book_id"])
            if book:
                categories.add(book.category)
        
        recommendations = await _recommend_by_categories(list(categories))
        context = f"Usuario tem itens no carrinho das categorias: {', '.join(categories)}"
        fallback = _format_recommendations(recommendations, "baseado no seu carrinho")
    
    elif _extract_category(last_message):
        # Baseado em categoria mencionada
        category = _extract_category(last_message)
        recommendations = await _recommend_by_category(category)
        context = f"Usuario pediu recomendacoes na categoria {category}"
        fallback = _format_recommendations(recommendations, f"na categoria {category}")
    
    else:
        # Recomendacoes gerais
        recommendations = await _get_popular_books()
        context = "Usuario quer recomendacoes gerais de livros populares"
        fallback = _format_recommendations(recommendations, "populares")
    
    # Gerar resposta com LLM se disponivel
    response = await generate_response_with_llm(
        context=context,
        data={"books": recommendations},
        fallback_response=fallback
    )
    
    messages.append(Message(
        role="assistant",
        content=response,
        type="agent",
        metadata={"agent": "recommend", "count": len(recommendations), "llm_used": is_llm_enabled()}
    ))
    
    return {
        "messages": messages,
        "recommendations": recommendations,
        "search_results": recommendations,  # Para permitir adicionar ao carrinho
        "next_agent": None
    }


async def _recommend_by_book(book_id: str) -> List[Dict[str, Any]]:
    """Recomendar baseado em um livro."""
    book = await products_repo.get_by_id(book_id)
    if not book:
        return []
    
    # Buscar livros da mesma categoria
    same_category = await products_repo.get_by_category(book.category)
    
    # Filtrar o livro original e limitar
    recommendations = [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "price": b.price,
            "price_formatted": f"R$ {b.price / 100:.2f}",
            "category": b.category,
            "reason": f"Mesmo genero: {b.category}"
        }
        for b in same_category if b.id != book_id
    ][:5]
    
    return recommendations


async def _recommend_by_category(category: str) -> List[Dict[str, Any]]:
    """Recomendar por categoria."""
    books = await products_repo.get_by_category(category)
    
    # Embaralhar e limitar
    shuffled = list(books)
    random.shuffle(shuffled)
    
    return [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "price": b.price,
            "price_formatted": f"R$ {b.price / 100:.2f}",
            "category": b.category,
            "reason": f"Categoria: {category}"
        }
        for b in shuffled[:5]
    ]


async def _recommend_by_categories(categories: List[str]) -> List[Dict[str, Any]]:
    """Recomendar baseado em multiplas categorias."""
    recommendations = []
    
    for category in categories[:3]:  # Max 3 categorias
        books = await products_repo.get_by_category(category)
        for book in books[:2]:  # 2 por categoria
            recommendations.append({
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "price": book.price,
                "price_formatted": f"R$ {book.price / 100:.2f}",
                "category": book.category,
                "reason": f"Voce gosta de {category}"
            })
    
    return recommendations[:5]


async def _get_popular_books() -> List[Dict[str, Any]]:
    """Obter livros populares (mock - seria baseado em vendas)."""
    all_books = await products_repo.get_all()
    
    # Simular popularidade (em producao seria baseado em dados reais)
    shuffled = list(all_books)
    random.shuffle(shuffled)
    
    return [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "price": b.price,
            "price_formatted": f"R$ {b.price / 100:.2f}",
            "category": b.category,
            "reason": "Muito vendido"
        }
        for b in shuffled[:5]
    ]


async def _handle_a2a_recommend(state: StoreAgentState) -> Dict[str, Any]:
    """Processar requisicao A2A de recomendacao."""
    request = state["a2a_request"]
    payload = request.get("payload", {})
    
    logger.info("A2A Recommend request")
    
    book_id = payload.get("book_id")
    category = payload.get("category")
    limit = payload.get("limit", 5)
    
    if book_id:
        recommendations = await _recommend_by_book(book_id)
    elif category:
        recommendations = await _recommend_by_category(category)
    else:
        recommendations = await _get_popular_books()
    
    return {
        "recommendations": recommendations[:limit],
        "next_agent": None
    }


def _extract_category(message: str) -> str:
    """Extrair categoria da mensagem."""
    categories = [
        "programacao", "python", "javascript",
        "ficcao", "romance", "fantasia", "terror",
        "negocios", "autoajuda", "biografias",
        "ciencia", "historia", "filosofia"
    ]
    
    message_lower = message.lower()
    
    for cat in categories:
        if cat in message_lower:
            return cat.capitalize()
    
    return ""


def _format_recommendations(recommendations: List[Dict[str, Any]], context: str) -> str:
    """Formatar recomendacoes para exibicao."""
    if not recommendations:
        return "Nao encontrei recomendacoes no momento. Que tipo de livro voce gosta?"
    
    lines = [f"**Recomendacoes {context}:** 📚✨\n"]
    
    for i, book in enumerate(recommendations, 1):
        lines.append(
            f"**{i}. {book['title']}**\n"
            f"   Autor: {book['author']}\n"
            f"   Preco: {book['price_formatted']}\n"
            f"   _{book.get('reason', '')}_\n"
        )
    
    lines.append("\nPara adicionar ao carrinho, digite: **adicionar 1** (ou o numero do livro desejado)")
    
    return "\n".join(lines)
