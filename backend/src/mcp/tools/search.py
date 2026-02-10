"""MCP Tools - Busca de livros."""
from typing import Any, Dict
from mcp.types import Tool

from ...db.products import products_repo


def get_search_tools() -> list[Tool]:
    """Retorna ferramentas de busca."""
    return [
        Tool(
            name="search_books",
            description="Buscar livros no catalogo da livraria por termo de busca",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termo de busca (titulo, autor ou descricao)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filtrar por categoria (opcional)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Numero maximo de resultados (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_book_details",
            description="Obter detalhes completos de um livro pelo ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "string",
                        "description": "ID do livro"
                    }
                },
                "required": ["book_id"]
            }
        ),
    ]


async def search_books(args: Dict[str, Any]) -> Dict[str, Any]:
    """Buscar livros."""
    query = args.get("query", "")
    category = args.get("category")
    max_results = args.get("max_results", 10)
    
    books = await products_repo.search(query)
    
    if category:
        books = [b for b in books if b.category.lower() == category.lower()]
    
    books = books[:max_results]
    
    return {
        "count": len(books),
        "books": [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "price": b.price,
                "price_formatted": f"R$ {b.price / 100:.2f}",
                "category": b.category,
                "in_stock": b.stock > 0
            }
            for b in books
        ]
    }


async def get_book_details(args: Dict[str, Any]) -> Dict[str, Any]:
    """Obter detalhes de um livro."""
    book_id = args.get("book_id")
    book = await products_repo.get_by_id(book_id)
    
    if not book:
        return {"error": "Livro nao encontrado"}
    
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "description": book.description,
        "price": book.price,
        "price_formatted": f"R$ {book.price / 100:.2f}",
        "category": book.category,
        "isbn": book.isbn,
        "stock": book.stock,
        "in_stock": book.stock > 0
    }
