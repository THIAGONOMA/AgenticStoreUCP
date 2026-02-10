"""
UCP Capability: dev.ucp.shopping.discount

Capability de desconto que estende checkout para suportar
cupons e codigos promocionais.

Spec: https://ucp.dev/specs/shopping/discount
"""
from pydantic import BaseModel
from typing import Optional


class DiscountCapability(BaseModel):
    """Especificacao da capability de desconto."""
    name: str = "dev.ucp.shopping.discount"
    version: str = "2026-01-11"
    spec: str = "https://ucp.dev/specs/shopping/discount"
    schema_url: str = "https://ucp.dev/schemas/shopping/discount.json"
    extends: str = "dev.ucp.shopping.checkout"
    
    class Config:
        frozen = True


# Tipos de desconto suportados
DISCOUNT_TYPES = {
    "percentage": "Desconto percentual (ex: 10%)",
    "fixed": "Desconto fixo em centavos (ex: R$ 10,00)",
    "buy_x_get_y": "Compre X leve Y",
    "free_shipping": "Frete gratis"
}


# Operacoes de desconto
DISCOUNT_OPERATIONS = [
    {
        "name": "apply_discount",
        "description": "Aplicar codigo de desconto a uma sessao",
        "endpoint": "POST /checkout-sessions/{session_id}/discounts",
        "request_schema": "ApplyDiscountRequest",
        "response_schema": "CheckoutSession"
    },
    {
        "name": "remove_discount",
        "description": "Remover desconto de uma sessao",
        "endpoint": "DELETE /checkout-sessions/{session_id}/discounts/{code}",
        "response_schema": "CheckoutSession"
    },
    {
        "name": "validate_discount",
        "description": "Validar codigo de desconto",
        "endpoint": "POST /discounts/validate",
        "request_schema": "ValidateDiscountRequest",
        "response_schema": "DiscountValidation"
    },
]


def get_discount_capability() -> DiscountCapability:
    """Retorna a capability de desconto."""
    return DiscountCapability()


def get_operations():
    """Retorna operacoes da capability."""
    return DISCOUNT_OPERATIONS
