"""
Tipos AP2 - Re-exportacoes do SDK oficial.

Este modulo re-exporta os tipos oficiais do Agent Payments Protocol (AP2)
do SDK google-agentic-commerce/AP2.

Tipos de Mandatos:
- IntentMandate: Intencao do usuario (o que quer comprar)
- CartMandate: Carrinho assinado pelo merchant (garantia de preco)
- PaymentMandate: Autorizacao de pagamento

Tipos de Payment Request (W3C):
- PaymentRequest: Requisicao de pagamento
- PaymentItem: Item individual
- PaymentCurrencyAmount: Valor monetario
- PaymentResponse: Resposta do pagamento
"""

from typing import TYPE_CHECKING

# Flag para verificar se SDK esta disponivel
AP2_SDK_AVAILABLE = False

try:
    # Tipos de Mandatos
    from ap2.types.mandate import (
        IntentMandate,
        CartMandate,
        CartContents,
        PaymentMandate,
        PaymentMandateContents,
        CART_MANDATE_DATA_KEY,
        INTENT_MANDATE_DATA_KEY,
        PAYMENT_MANDATE_DATA_KEY,
    )
    
    # Tipos de Payment Request (W3C)
    from ap2.types.payment_request import (
        PaymentRequest,
        PaymentItem,
        PaymentCurrencyAmount,
        PaymentResponse,
        PaymentMethodData,
        PaymentDetailsInit,
        PaymentOptions,
        PaymentShippingOption,
        PaymentDetailsModifier,
    )
    
    # Tipos de Contato
    from ap2.types.contact_picker import ContactAddress
    
    AP2_SDK_AVAILABLE = True
    
except ImportError:
    # Fallback: criar tipos basicos para compatibilidade
    from pydantic import BaseModel, Field
    from typing import Optional, List, Dict, Any
    from datetime import datetime, timezone
    
    class PaymentCurrencyAmount(BaseModel):
        """Valor monetario."""
        currency: str
        value: float
    
    class PaymentItem(BaseModel):
        """Item de pagamento."""
        label: str
        amount: PaymentCurrencyAmount
        pending: Optional[bool] = None
        refund_period: int = 30
    
    class PaymentMethodData(BaseModel):
        """Metodo de pagamento."""
        supported_methods: str
        data: Optional[Dict[str, Any]] = None
    
    class PaymentDetailsInit(BaseModel):
        """Detalhes do pagamento."""
        id: str
        display_items: List[PaymentItem]
        total: PaymentItem
        shipping_options: Optional[List] = None
        modifiers: Optional[List] = None
    
    class PaymentOptions(BaseModel):
        """Opcoes de pagamento."""
        request_payer_name: Optional[bool] = False
        request_payer_email: Optional[bool] = False
        request_payer_phone: Optional[bool] = False
        request_shipping: Optional[bool] = True
    
    class PaymentShippingOption(BaseModel):
        """Opcao de frete."""
        id: str
        label: str
        amount: PaymentCurrencyAmount
        selected: Optional[bool] = False
    
    class PaymentDetailsModifier(BaseModel):
        """Modificador de detalhes."""
        supported_methods: str
        total: Optional[PaymentItem] = None
    
    class ContactAddress(BaseModel):
        """Endereco de contato."""
        country: Optional[str] = None
        address_line: Optional[List[str]] = None
        region: Optional[str] = None
        city: Optional[str] = None
        postal_code: Optional[str] = None
    
    class PaymentRequest(BaseModel):
        """Requisicao de pagamento W3C."""
        method_data: List[PaymentMethodData]
        details: PaymentDetailsInit
        options: Optional[PaymentOptions] = None
        shipping_address: Optional[ContactAddress] = None
    
    class PaymentResponse(BaseModel):
        """Resposta de pagamento."""
        request_id: str
        method_name: str
        details: Optional[Dict[str, Any]] = None
    
    class IntentMandate(BaseModel):
        """Mandato de intencao do usuario."""
        user_cart_confirmation_required: bool = True
        natural_language_description: str
        merchants: Optional[List[str]] = None
        skus: Optional[List[str]] = None
        requires_refundability: Optional[bool] = False
        intent_expiry: str
    
    class CartContents(BaseModel):
        """Conteudo do carrinho."""
        id: str
        user_cart_confirmation_required: bool
        payment_request: PaymentRequest
        cart_expiry: str
        merchant_name: str
    
    class CartMandate(BaseModel):
        """Mandato de carrinho assinado pelo merchant."""
        contents: CartContents
        merchant_authorization: Optional[str] = None
    
    class PaymentMandateContents(BaseModel):
        """Conteudo do mandato de pagamento."""
        payment_mandate_id: str
        payment_details_id: str
        payment_details_total: PaymentItem
        payment_response: PaymentResponse
        merchant_agent: str
        timestamp: str = Field(
            default_factory=lambda: datetime.now(timezone.utc).isoformat()
        )
    
    class PaymentMandate(BaseModel):
        """Mandato de pagamento - autorizacao final."""
        payment_mandate_contents: PaymentMandateContents
        user_authorization: Optional[str] = None
    
    # Constantes
    CART_MANDATE_DATA_KEY = "ap2.mandates.CartMandate"
    INTENT_MANDATE_DATA_KEY = "ap2.mandates.IntentMandate"
    PAYMENT_MANDATE_DATA_KEY = "ap2.mandates.PaymentMandate"


def is_ap2_sdk_available() -> bool:
    """Verificar se SDK AP2 oficial esta disponivel."""
    return AP2_SDK_AVAILABLE


__all__ = [
    # Mandatos
    "IntentMandate",
    "CartMandate", 
    "CartContents",
    "PaymentMandate",
    "PaymentMandateContents",
    # Payment Request
    "PaymentRequest",
    "PaymentItem",
    "PaymentCurrencyAmount",
    "PaymentResponse",
    "PaymentMethodData",
    "PaymentDetailsInit",
    "PaymentOptions",
    "PaymentShippingOption",
    "PaymentDetailsModifier",
    # Contato
    "ContactAddress",
    # Constantes
    "CART_MANDATE_DATA_KEY",
    "INTENT_MANDATE_DATA_KEY", 
    "PAYMENT_MANDATE_DATA_KEY",
    # Utils
    "is_ap2_sdk_available",
    "AP2_SDK_AVAILABLE",
]
