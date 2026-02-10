"""
UCP Capability: dev.ucp.shopping.checkout

Capability principal de checkout que permite criar sessoes de compra,
adicionar itens, e completar transacoes.

Spec: https://ucp.dev/specs/shopping/checkout
"""
from pydantic import BaseModel
from typing import Optional


class CheckoutCapability(BaseModel):
    """Especificacao da capability de checkout."""
    name: str = "dev.ucp.shopping.checkout"
    version: str = "2026-01-11"
    spec: str = "https://ucp.dev/specs/shopping/checkout"
    schema_url: str = "https://ucp.dev/schemas/shopping/checkout.json"
    extends: Optional[str] = None
    
    class Config:
        frozen = True


# Operacoes suportadas pela capability
CHECKOUT_OPERATIONS = [
    {
        "name": "create_session",
        "description": "Criar uma nova sessao de checkout",
        "endpoint": "POST /checkout-sessions",
        "request_schema": "CreateCheckoutRequest",
        "response_schema": "CheckoutSession"
    },
    {
        "name": "get_session",
        "description": "Obter detalhes de uma sessao",
        "endpoint": "GET /checkout-sessions/{session_id}",
        "response_schema": "CheckoutSession"
    },
    {
        "name": "update_session",
        "description": "Atualizar sessao (adicionar/remover itens)",
        "endpoint": "PUT /checkout-sessions/{session_id}",
        "request_schema": "UpdateCheckoutRequest",
        "response_schema": "CheckoutSession"
    },
    {
        "name": "complete_session",
        "description": "Completar checkout com pagamento",
        "endpoint": "POST /checkout-sessions/{session_id}/complete",
        "request_schema": "CheckoutComplete",
        "response_schema": "CheckoutSession"
    },
    {
        "name": "cancel_session",
        "description": "Cancelar sessao de checkout",
        "endpoint": "DELETE /checkout-sessions/{session_id}",
        "response_schema": "CheckoutSession"
    },
]


def get_checkout_capability() -> CheckoutCapability:
    """Retorna a capability de checkout."""
    return CheckoutCapability()


def get_operations():
    """Retorna operacoes da capability."""
    return CHECKOUT_OPERATIONS
