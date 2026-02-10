"""
UCP Service: Payment Handlers

Configuracao dos handlers de pagamento suportados pela loja.
Cada handler define um metodo de pagamento que pode ser usado
para completar sessoes de checkout.

Spec: https://ucp.dev/specs/payment
"""
from pydantic import BaseModel
from typing import Dict, List, Any, Optional


class PaymentHandler(BaseModel):
    """Handler de pagamento UCP."""
    id: str
    name: str
    version: str
    spec: Optional[str] = None
    config_schema: Optional[str] = None
    instrument_schemas: List[str] = []
    config: Dict[str, Any] = {}
    
    class Config:
        frozen = True


class MockPaymentHandler(PaymentHandler):
    """Handler de pagamento mock para desenvolvimento."""
    id: str = "mock_payment"
    name: str = "dev.ucp.mock_payment"
    version: str = "2026-01-11"
    spec: str = "https://ucp.dev/specs/mock"
    config_schema: str = "https://ucp.dev/schemas/mock.json"
    instrument_schemas: List[str] = [
        "https://ucp.dev/schemas/shopping/types/card_payment_instrument.json"
    ]
    config: Dict[str, Any] = {
        "supported_tokens": ["success_token", "fail_token"],
        "test_mode": True
    }


class AP2PaymentHandler(PaymentHandler):
    """Handler de pagamento AP2 (Agent Payments Protocol)."""
    id: str = "ap2_payment"
    name: str = "dev.ucp.ap2_payment"
    version: str = "2026-01-11"
    spec: str = "https://ucp.dev/specs/ap2"
    config_schema: str = "https://ucp.dev/schemas/ap2.json"
    instrument_schemas: List[str] = [
        "https://ucp.dev/schemas/ap2/mandate.json"
    ]
    config: Dict[str, Any] = {
        "algorithm": "Ed25519",
        "audience": "livraria-ucp",
        "max_amount": 100000  # R$ 1000,00 em centavos
    }


# Handlers disponiveis
PAYMENT_HANDLERS = {
    "mock_payment": MockPaymentHandler,
    "ap2_payment": AP2PaymentHandler,
}


def get_mock_payment_handler() -> MockPaymentHandler:
    """Retorna handler de pagamento mock."""
    return MockPaymentHandler()


def get_ap2_payment_handler() -> AP2PaymentHandler:
    """Retorna handler de pagamento AP2."""
    return AP2PaymentHandler()


def get_all_payment_handlers() -> List[PaymentHandler]:
    """Retorna todos os handlers de pagamento."""
    return [
        get_mock_payment_handler(),
        get_ap2_payment_handler(),
    ]


def get_payment_handler_by_id(handler_id: str) -> Optional[PaymentHandler]:
    """Busca handler por ID."""
    handler_class = PAYMENT_HANDLERS.get(handler_id)
    if handler_class:
        return handler_class()
    return None
