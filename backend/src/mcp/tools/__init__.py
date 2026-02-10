"""
MCP Tools - Ferramentas do Model Context Protocol.

Estrutura:
- search.py     : Busca de livros (search_books, get_book_details)
- catalog.py    : Catalogo e categorias (list_categories, get_books_by_category)
- cart.py       : Carrinho e descontos (check_discount_code, calculate_cart)
- recommendations.py : Recomendacoes (get_recommendations)
- payments.py   : Pagamentos e transacoes (get_wallet_balance, list_transactions, get_transaction)
"""

from .search import (
    get_search_tools,
    search_books,
    get_book_details,
)

from .catalog import (
    get_catalog_tools,
    list_categories,
    get_books_by_category,
)

from .cart import (
    get_cart_tools,
    check_discount_code,
    calculate_cart,
)

from .recommendations import (
    get_recommendation_tools,
    get_recommendations,
)

from .payments import (
    get_payment_tools,
    get_wallet_balance,
    list_transactions,
    get_transaction,
)


def get_all_tools():
    """Retorna todas as ferramentas MCP."""
    return (
        get_search_tools() +
        get_catalog_tools() +
        get_cart_tools() +
        get_recommendation_tools() +
        get_payment_tools()
    )


# Mapeamento de nome -> funcao handler
TOOL_HANDLERS = {
    "search_books": search_books,
    "get_book_details": get_book_details,
    "list_categories": list_categories,
    "get_books_by_category": get_books_by_category,
    "check_discount_code": check_discount_code,
    "calculate_cart": calculate_cart,
    "get_recommendations": get_recommendations,
    "get_wallet_balance": get_wallet_balance,
    "list_transactions": list_transactions,
    "get_transaction": get_transaction,
}


async def call_tool_handler(name: str, arguments: dict):
    """Chama o handler de uma ferramenta pelo nome."""
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    
    # list_categories nao recebe argumentos
    if name == "list_categories":
        return await handler()
    
    return await handler(arguments)


__all__ = [
    # Funcoes de tools
    "get_all_tools",
    "call_tool_handler",
    "TOOL_HANDLERS",
    # Search
    "get_search_tools",
    "search_books",
    "get_book_details",
    # Catalog
    "get_catalog_tools",
    "list_categories",
    "get_books_by_category",
    # Cart
    "get_cart_tools",
    "check_discount_code",
    "calculate_cart",
    # Recommendations
    "get_recommendation_tools",
    "get_recommendations",
]
