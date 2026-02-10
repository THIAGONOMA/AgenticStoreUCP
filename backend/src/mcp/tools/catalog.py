"""MCP Tools - Catalogo e categorias."""
from typing import Any, Dict
from mcp.types import Tool

from ...db.products import products_repo


def get_catalog_tools() -> list[Tool]:
    """Retorna ferramentas de catalogo."""
    return [
        Tool(
            name="list_categories",
            description="Listar todas as categorias de livros disponiveis",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_books_by_category",
            description="Listar livros de uma categoria especifica",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Nome da categoria"
                    }
                },
                "required": ["category"]
            }
        ),
    ]


async def list_categories() -> Dict[str, Any]:
    """Listar categorias."""
    books = await products_repo.get_all()
    categories = list(set(b.category for b in books))
    
    return {
        "count": len(categories),
        "categories": sorted(categories)
    }


async def get_books_by_category(args: Dict[str, Any]) -> Dict[str, Any]:
    """Livros por categoria."""
    category = args.get("category", "")
    books = await products_repo.get_by_category(category)
    
    return {
        "category": category,
        "count": len(books),
        "books": [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "price_formatted": f"R$ {b.price / 100:.2f}"
            }
            for b in books
        ]
    }
