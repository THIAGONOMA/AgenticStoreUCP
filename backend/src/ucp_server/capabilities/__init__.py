"""
UCP Capabilities - Capacidades do Universal Commerce Protocol.

Capabilities definem o que uma loja pode fazer. Cada capability
e uma unidade de funcionalidade que pode ser descoberta por agentes.

Estrutura:
- checkout.py    : Capability de checkout (criar sessao, completar, cancelar)
- discount.py    : Capability de desconto (cupons, promocoes)
- fulfillment.py : Capability de fulfillment (entrega, rastreamento)
"""
from typing import List, Optional
from pydantic import BaseModel

from .checkout import (
    CheckoutCapability,
    get_checkout_capability,
    get_operations as get_checkout_operations,
    CHECKOUT_OPERATIONS,
)

from .discount import (
    DiscountCapability,
    get_discount_capability,
    get_operations as get_discount_operations,
    DISCOUNT_TYPES,
    DISCOUNT_OPERATIONS,
)

from .fulfillment import (
    FulfillmentCapability,
    get_fulfillment_capability,
    get_operations as get_fulfillment_operations,
    FULFILLMENT_STATUS,
    FULFILLMENT_OPERATIONS,
)


class UcpCapabilitySpec(BaseModel):
    """Especificacao de capability UCP para discovery."""
    name: str
    version: str
    spec: Optional[str] = None
    schema_url: Optional[str] = None
    extends: Optional[str] = None


def get_all_capabilities() -> List[UcpCapabilitySpec]:
    """Retorna todas as capabilities da loja."""
    checkout = get_checkout_capability()
    discount = get_discount_capability()
    fulfillment = get_fulfillment_capability()
    
    return [
        UcpCapabilitySpec(
            name=checkout.name,
            version=checkout.version,
            spec=checkout.spec,
            schema_url=checkout.schema_url,
            extends=checkout.extends
        ),
        UcpCapabilitySpec(
            name=discount.name,
            version=discount.version,
            spec=discount.spec,
            schema_url=discount.schema_url,
            extends=discount.extends
        ),
        UcpCapabilitySpec(
            name=fulfillment.name,
            version=fulfillment.version,
            spec=fulfillment.spec,
            schema_url=fulfillment.schema_url,
            extends=fulfillment.extends
        ),
    ]


def get_capability_by_name(name: str):
    """Busca capability por nome."""
    capabilities = {
        "dev.ucp.shopping.checkout": get_checkout_capability,
        "dev.ucp.shopping.discount": get_discount_capability,
        "dev.ucp.shopping.fulfillment": get_fulfillment_capability,
    }
    
    factory = capabilities.get(name)
    if factory:
        return factory()
    return None


__all__ = [
    # Funcoes principais
    "get_all_capabilities",
    "get_capability_by_name",
    "UcpCapabilitySpec",
    # Checkout
    "CheckoutCapability",
    "get_checkout_capability",
    "CHECKOUT_OPERATIONS",
    # Discount
    "DiscountCapability",
    "get_discount_capability",
    "DISCOUNT_TYPES",
    "DISCOUNT_OPERATIONS",
    # Fulfillment
    "FulfillmentCapability",
    "get_fulfillment_capability",
    "FULFILLMENT_STATUS",
    "FULFILLMENT_OPERATIONS",
]
