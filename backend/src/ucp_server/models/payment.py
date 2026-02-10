"""Modelos de Pagamento."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class PaymentHandler(BaseModel):
    """Handler de pagamento."""
    id: str
    name: str
    version: str
    spec: Optional[str] = None
    config_schema: Optional[str] = None
    instrument_schemas: List[str] = []
    config: Dict[str, Any] = {}


class PaymentInstrument(BaseModel):
    """Instrumento de pagamento."""
    type: str
    details: Dict[str, Any] = {}


class Payment(BaseModel):
    """Pagamento."""
    handlers: List[PaymentHandler] = []
    instruments: List[PaymentInstrument] = []


class PaymentRequest(BaseModel):
    """Request de pagamento para completar checkout."""
    token: str
    mandate: Optional[str] = None  # JWT do mandato AP2
    handler_id: str
