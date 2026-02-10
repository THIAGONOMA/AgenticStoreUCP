"""
UCP Service: dev.ucp.shopping

Servico principal de shopping que agrupa as capabilities
de checkout, desconto e fulfillment.

Spec: https://ucp.dev/specs/shopping
"""
from pydantic import BaseModel
from typing import Dict, Optional


class ShoppingService(BaseModel):
    """Servico de shopping UCP."""
    name: str = "dev.ucp.shopping"
    version: str = "2026-01-11"
    spec: str = "https://ucp.dev/specs/shopping"
    description: str = "Servico de compras com checkout, descontos e fulfillment"
    
    # Endpoints REST
    rest: Dict[str, str] = {
        "schema": "https://ucp.dev/services/shopping/openapi.json",
        "endpoint": "/"
    }
    
    class Config:
        frozen = True


# Recursos disponíveis no serviço
SHOPPING_RESOURCES = [
    {
        "name": "books",
        "description": "Catalogo de livros",
        "endpoints": {
            "list": "GET /books",
            "search": "GET /books/search?q={query}",
            "get": "GET /books/{book_id}",
            "categories": "GET /books/categories"
        }
    },
    {
        "name": "checkout-sessions",
        "description": "Sessoes de checkout",
        "endpoints": {
            "create": "POST /checkout-sessions",
            "get": "GET /checkout-sessions/{session_id}",
            "update": "PUT /checkout-sessions/{session_id}",
            "complete": "POST /checkout-sessions/{session_id}/complete",
            "cancel": "DELETE /checkout-sessions/{session_id}"
        }
    },
]


def get_shopping_service(base_url: str = "http://localhost:8182") -> ShoppingService:
    """Retorna o servico de shopping configurado."""
    return ShoppingService(
        rest={
            "schema": "https://ucp.dev/services/shopping/openapi.json",
            "endpoint": f"{base_url}/"
        }
    )


def get_resources():
    """Retorna recursos do servico."""
    return SHOPPING_RESOURCES
