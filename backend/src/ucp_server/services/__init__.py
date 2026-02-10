"""
UCP Services - Servicos do Universal Commerce Protocol.

Services agrupam capabilities relacionadas e definem
a interface REST da loja.

Estrutura:
- shopping.py : Servico principal de compras
- payment.py  : Handlers de pagamento (Mock, AP2)
"""
from typing import Dict, List
from pydantic import BaseModel

from .shopping import (
    ShoppingService,
    get_shopping_service,
    get_resources as get_shopping_resources,
    SHOPPING_RESOURCES,
)

from .payment import (
    PaymentHandler,
    MockPaymentHandler,
    AP2PaymentHandler,
    get_mock_payment_handler,
    get_ap2_payment_handler,
    get_all_payment_handlers,
    get_payment_handler_by_id,
    PAYMENT_HANDLERS,
)


class UcpService(BaseModel):
    """Servico UCP para discovery."""
    version: str
    spec: str = None
    rest: Dict[str, str] = None


class PaymentProfile(BaseModel):
    """Perfil de pagamentos para discovery."""
    handlers: List[dict] = []


def get_all_services(base_url: str = "http://localhost:8182") -> Dict[str, UcpService]:
    """Retorna todos os servicos da loja."""
    shopping = get_shopping_service(base_url)
    
    return {
        shopping.name: UcpService(
            version=shopping.version,
            spec=shopping.spec,
            rest=shopping.rest
        )
    }


def get_payment_profile() -> PaymentProfile:
    """Retorna perfil de pagamentos para discovery."""
    handlers = get_all_payment_handlers()
    
    return PaymentProfile(
        handlers=[
            {
                "id": h.id,
                "name": h.name,
                "version": h.version,
                "spec": h.spec,
                "config_schema": h.config_schema,
                "instrument_schemas": h.instrument_schemas,
                "config": h.config
            }
            for h in handlers
        ]
    )


__all__ = [
    # Funcoes principais
    "get_all_services",
    "get_payment_profile",
    "UcpService",
    "PaymentProfile",
    # Shopping
    "ShoppingService",
    "get_shopping_service",
    "SHOPPING_RESOURCES",
    # Payment
    "PaymentHandler",
    "MockPaymentHandler",
    "AP2PaymentHandler",
    "get_mock_payment_handler",
    "get_ap2_payment_handler",
    "get_all_payment_handlers",
    "get_payment_handler_by_id",
    "PAYMENT_HANDLERS",
]
