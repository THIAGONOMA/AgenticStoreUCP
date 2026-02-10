"""Security - AP2 e Criptografia.

Implementa o Agent Payments Protocol (AP2) seguindo o SDK oficial
do Google (google-agentic-commerce/AP2).
"""
from .key_manager import KeyManager, get_server_key_manager
from .ap2_security import AP2Security, get_ap2_security, MandatePayload, MandateValidationResult
from .signatures import RequestSigner, ConformanceHeaders, get_request_signer

# Tipos AP2 oficiais
from .ap2_types import (
    IntentMandate,
    CartMandate,
    CartContents,
    PaymentMandate,
    PaymentMandateContents,
    PaymentRequest,
    PaymentItem,
    PaymentCurrencyAmount,
    PaymentResponse,
    is_ap2_sdk_available,
    AP2_SDK_AVAILABLE,
)

# Adapters AP2
from .ap2_adapters import (
    create_intent_mandate,
    create_cart_contents,
    sign_cart_mandate,
    create_payment_mandate,
    validate_cart_mandate,
    cart_items_to_cart_mandate,
)

__all__ = [
    # Key Manager
    "KeyManager",
    "get_server_key_manager",
    # AP2 Security
    "AP2Security",
    "get_ap2_security",
    "MandatePayload",
    "MandateValidationResult",
    # Signatures
    "RequestSigner",
    "ConformanceHeaders",
    "get_request_signer",
    # Tipos AP2 oficiais
    "IntentMandate",
    "CartMandate",
    "CartContents",
    "PaymentMandate",
    "PaymentMandateContents",
    "PaymentRequest",
    "PaymentItem",
    "PaymentCurrencyAmount",
    "PaymentResponse",
    "is_ap2_sdk_available",
    "AP2_SDK_AVAILABLE",
    # Adapters AP2
    "create_intent_mandate",
    "create_cart_contents",
    "sign_cart_mandate",
    "create_payment_mandate",
    "validate_cart_mandate",
    "cart_items_to_cart_mandate",
]
