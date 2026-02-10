"""MCP Tools - Recomendacoes de livros."""
from typing import Any, Dict
from mcp.types import Tool

from ...db.products import products_repo


def get_recommendation_tools() -> list[Tool]:
    """Retorna ferramentas de recomendacao."""
    return [
        Tool(
            name="get_recommendations",
            description="Obter recomendacoes de livros baseado em um livro ou categoria",
            inputSchema={
                "type": "object",
                "properties": {
                    "based_on_book_id": {
                        "type": "string",
                        "description": "ID do livro base para recomendacoes"
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoria para buscar recomendacoes"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Numero maximo de recomendacoes",
                        "default": 5
                    }
                }
            }
        ),
    ]


async def get_recommendations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Recomendacoes de livros."""
    book_id = args.get("based_on_book_id")
    category = args.get("category")
    max_results = args.get("max_results", 5)
    
    # Se temos um livro base, pegar sua categoria
    if book_id:
        base_book = await products_repo.get_by_id(book_id)
        if base_book:
            category = base_book.category
    
    if category:
        books = await products_repo.get_by_category(category)
        # Remover o livro base se existir
        books = [b for b in books if b.id != book_id]
    else:
        # Retornar livros aleatorios
        books = await products_repo.get_all()
    
    books = books[:max_results]
    
    return {
        "based_on": book_id or category or "all",
        "recommendations": [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "price_formatted": f"R$ {b.price / 100:.2f}",
                "category": b.category
            }
            for b in books
        ]
    }
