"""
Adapters AP2 - Funcoes de conversao para SDK oficial.

Este modulo fornece funcoes para criar e manipular mandatos AP2
seguindo o padrao oficial do Google (google-agentic-commerce/AP2).

Fluxo de Mandatos:
1. IntentMandate - Usuario expressa intencao de compra
2. CartMandate - Merchant assina carrinho com garantia de preco
3. PaymentMandate - Autorizacao final para pagamento
"""

import uuid
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

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
    PaymentMethodData,
    PaymentDetailsInit,
    PaymentOptions,
    is_ap2_sdk_available,
)
from .key_manager import KeyManager


def create_intent_mandate(
    description: str,
    merchants: Optional[List[str]] = None,
    skus: Optional[List[str]] = None,
    requires_confirmation: bool = True,
    requires_refundability: bool = False,
    expiry_minutes: int = 60,
) -> IntentMandate:
    """
    Criar IntentMandate para expressar intencao de compra.
    
    Args:
        description: Descricao em linguagem natural da intencao
        merchants: Lista de merchants permitidos (None = qualquer)
        skus: Lista de SKUs especificos (None = qualquer)
        requires_confirmation: Se requer confirmacao do usuario
        requires_refundability: Se itens devem ser reembolsaveis
        expiry_minutes: Tempo de expiracao em minutos
        
    Returns:
        IntentMandate configurado
    """
    expiry = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    
    return IntentMandate(
        user_cart_confirmation_required=requires_confirmation,
        natural_language_description=description,
        merchants=merchants,
        skus=skus,
        requires_refundability=requires_refundability,
        intent_expiry=expiry.isoformat(),
    )


def create_cart_contents(
    cart_id: str,
    merchant_name: str,
    items: List[Dict[str, Any]],
    currency: str = "BRL",
    requires_confirmation: bool = True,
    expiry_minutes: int = 15,
    supported_methods: Optional[List[str]] = None,
) -> CartContents:
    """
    Criar CartContents a partir de itens do carrinho.
    
    Args:
        cart_id: ID unico do carrinho
        merchant_name: Nome do merchant
        items: Lista de itens [{title, price, quantity}]
        currency: Codigo da moeda (ISO 4217)
        requires_confirmation: Se requer confirmacao do usuario
        expiry_minutes: Tempo de expiracao em minutos
        supported_methods: Metodos de pagamento aceitos
        
    Returns:
        CartContents configurado
    """
    if supported_methods is None:
        supported_methods = ["dev.ucp.mock_payment", "dev.ucp.ap2_payment"]
    
    # Criar PaymentItems para cada item
    display_items = []
    total_value = 0.0
    
    for item in items:
        price = item.get("price", 0) / 100  # Converter centavos para reais
        quantity = item.get("quantity", 1)
        item_total = price * quantity
        total_value += item_total
        
        display_items.append(PaymentItem(
            label=f"{item.get('title', 'Item')} x{quantity}",
            amount=PaymentCurrencyAmount(
                currency=currency,
                value=item_total
            ),
            pending=False,
            refund_period=30,
        ))
    
    # Total
    total_item = PaymentItem(
        label="Total",
        amount=PaymentCurrencyAmount(
            currency=currency,
            value=total_value
        ),
        pending=False,
    )
    
    # PaymentMethodData
    method_data = [
        PaymentMethodData(
            supported_methods=method,
            data={}
        )
        for method in supported_methods
    ]
    
    # PaymentDetailsInit
    details = PaymentDetailsInit(
        id=f"pd_{cart_id}",
        display_items=display_items,
        total=total_item,
        shipping_options=None,
        modifiers=None,
    )
    
    # PaymentRequest
    payment_request = PaymentRequest(
        method_data=method_data,
        details=details,
        options=PaymentOptions(
            request_payer_name=True,
            request_payer_email=True,
            request_shipping=False,
        ),
        shipping_address=None,
    )
    
    expiry = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    
    return CartContents(
        id=cart_id,
        user_cart_confirmation_required=requires_confirmation,
        payment_request=payment_request,
        cart_expiry=expiry.isoformat(),
        merchant_name=merchant_name,
    )


def compute_cart_hash(cart_contents: CartContents) -> str:
    """
    Computar hash seguro do CartContents.
    
    Usado para garantir integridade no JWT de autorizacao.
    
    Args:
        cart_contents: Conteudo do carrinho
        
    Returns:
        Hash SHA-256 em hex
    """
    # Serializar para JSON canonico
    json_str = cart_contents.model_dump_json(exclude_none=True)
    # Computar SHA-256
    return hashlib.sha256(json_str.encode()).hexdigest()


def sign_cart_mandate(
    cart_contents: CartContents,
    key_manager: KeyManager,
    audience: str = "payment-processor",
) -> CartMandate:
    """
    Assinar CartContents e criar CartMandate.
    
    Args:
        cart_contents: Conteudo do carrinho a ser assinado
        key_manager: KeyManager para assinatura
        audience: Audience do JWT (destinatario)
        
    Returns:
        CartMandate com merchant_authorization preenchido
    """
    import base64
    
    # Computar hash do carrinho
    cart_hash = compute_cart_hash(cart_contents)
    
    # Header JWT
    header = {
        "alg": "EdDSA",
        "typ": "JWT",
        "kid": key_manager.key_id
    }
    
    # Payload JWT
    now = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "iss": cart_contents.merchant_name,
        "sub": "cart-authorization",
        "aud": audience,
        "iat": now,
        "exp": now + 900,  # 15 minutos
        "jti": str(uuid.uuid4()),
        "cart_hash": cart_hash,
        "cart_id": cart_contents.id,
    }
    
    # Codificar
    def b64url_encode(data: str) -> str:
        return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")
    
    header_b64 = b64url_encode(json.dumps(header))
    payload_b64 = b64url_encode(json.dumps(payload))
    
    # Assinar
    signing_input = f"{header_b64}.{payload_b64}"
    signature = key_manager.sign(signing_input)
    
    jwt = f"{signing_input}.{signature}"
    
    return CartMandate(
        contents=cart_contents,
        merchant_authorization=jwt,
    )


def create_payment_mandate(
    cart_mandate: CartMandate,
    payment_method: str,
    key_manager: KeyManager,
    payer_name: Optional[str] = None,
    payer_email: Optional[str] = None,
) -> PaymentMandate:
    """
    Criar PaymentMandate apos usuario confirmar pagamento.
    
    Args:
        cart_mandate: CartMandate assinado
        payment_method: Metodo de pagamento escolhido
        key_manager: KeyManager para assinatura
        payer_name: Nome do pagador
        payer_email: Email do pagador
        
    Returns:
        PaymentMandate com autorizacao do usuario
    """
    import base64
    
    payment_mandate_id = f"pm_{uuid.uuid4().hex[:12]}"
    
    # Criar PaymentResponse
    payment_response = PaymentResponse(
        request_id=cart_mandate.contents.payment_request.details.id,
        method_name=payment_method,
        details={"authorized": True},
        payer_name=payer_name,
        payer_email=payer_email,
    )
    
    # Criar conteudo
    contents = PaymentMandateContents(
        payment_mandate_id=payment_mandate_id,
        payment_details_id=cart_mandate.contents.payment_request.details.id,
        payment_details_total=cart_mandate.contents.payment_request.details.total,
        payment_response=payment_response,
        merchant_agent=cart_mandate.contents.merchant_name,
    )
    
    # Criar JWT de autorizacao do usuario
    cart_hash = compute_cart_hash(cart_mandate.contents)
    contents_json = contents.model_dump_json(exclude_none=True)
    payment_hash = hashlib.sha256(contents_json.encode()).hexdigest()
    
    header = {
        "alg": "EdDSA",
        "typ": "JWT",
        "kid": key_manager.key_id
    }
    
    now = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "iss": "user-agent",
        "sub": "payment-authorization",
        "aud": cart_mandate.contents.merchant_name,
        "iat": now,
        "exp": now + 300,  # 5 minutos
        "nonce": str(uuid.uuid4()),
        "transaction_data": [cart_hash, payment_hash],
    }
    
    def b64url_encode(data: str) -> str:
        return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")
    
    header_b64 = b64url_encode(json.dumps(header))
    payload_b64 = b64url_encode(json.dumps(payload))
    
    signing_input = f"{header_b64}.{payload_b64}"
    signature = key_manager.sign(signing_input)
    
    user_authorization = f"{signing_input}.{signature}"
    
    return PaymentMandate(
        payment_mandate_contents=contents,
        user_authorization=user_authorization,
    )


def validate_cart_mandate(
    cart_mandate: CartMandate,
    key_manager: KeyManager,
) -> Dict[str, Any]:
    """
    Validar CartMandate e sua assinatura.
    
    Args:
        cart_mandate: CartMandate a ser validado
        key_manager: KeyManager para verificacao
        
    Returns:
        Dict com resultado da validacao
    """
    import base64
    
    result = {
        "valid": False,
        "error": None,
        "cart_id": cart_mandate.contents.id,
        "merchant": cart_mandate.contents.merchant_name,
        "total": None,
        "expired": False,
    }
    
    if not cart_mandate.merchant_authorization:
        result["error"] = "Missing merchant authorization"
        return result
    
    try:
        # Separar partes do JWT
        parts = cart_mandate.merchant_authorization.split(".")
        if len(parts) != 3:
            result["error"] = "Invalid JWT format"
            return result
        
        header_b64, payload_b64, signature = parts
        
        # Verificar assinatura
        signing_input = f"{header_b64}.{payload_b64}"
        if not key_manager.verify(signing_input, signature):
            result["error"] = "Invalid signature"
            return result
        
        # Decodificar payload
        def b64url_decode(data: str) -> str:
            padded = data + "=" * (4 - len(data) % 4)
            return base64.urlsafe_b64decode(padded).decode()
        
        payload = json.loads(b64url_decode(payload_b64))
        
        # Verificar expiracao
        exp = payload.get("exp", 0)
        if datetime.now(timezone.utc).timestamp() > exp:
            result["expired"] = True
            result["error"] = "Cart mandate expired"
            return result
        
        # Verificar hash do carrinho
        expected_hash = compute_cart_hash(cart_mandate.contents)
        if payload.get("cart_hash") != expected_hash:
            result["error"] = "Cart hash mismatch - contents may have been tampered"
            return result
        
        # Sucesso
        result["valid"] = True
        result["total"] = cart_mandate.contents.payment_request.details.total.amount.value
        result["currency"] = cart_mandate.contents.payment_request.details.total.amount.currency
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def local_mandate_to_intent(
    amount: int,
    currency: str,
    description: str = "Compra na Livraria Virtual",
    merchant: str = "livraria-ucp",
) -> IntentMandate:
    """
    Converter mandato local simples para IntentMandate.
    
    Compatibilidade com o sistema atual que usa apenas amount/currency.
    
    Args:
        amount: Valor em centavos
        currency: Codigo da moeda
        description: Descricao da compra
        merchant: ID do merchant
        
    Returns:
        IntentMandate compativel
    """
    return create_intent_mandate(
        description=f"{description} - R$ {amount/100:.2f}",
        merchants=[merchant],
        requires_confirmation=True,
        expiry_minutes=60,
    )


def cart_items_to_cart_mandate(
    cart_items: List[Dict[str, Any]],
    cart_id: str,
    merchant_name: str,
    key_manager: KeyManager,
    currency: str = "BRL",
) -> CartMandate:
    """
    Converter itens do carrinho em CartMandate assinado.
    
    Args:
        cart_items: Lista de itens do carrinho
        cart_id: ID do carrinho/sessao
        merchant_name: Nome do merchant
        key_manager: KeyManager para assinatura
        currency: Codigo da moeda
        
    Returns:
        CartMandate assinado
    """
    # Converter itens para formato esperado
    items = []
    for item in cart_items:
        items.append({
            "title": item.get("title") or item.get("name", "Item"),
            "price": item.get("price", 0),
            "quantity": item.get("quantity", 1),
        })
    
    # Criar conteudo
    contents = create_cart_contents(
        cart_id=cart_id,
        merchant_name=merchant_name,
        items=items,
        currency=currency,
    )
    
    # Assinar e retornar
    return sign_cart_mandate(contents, key_manager)


__all__ = [
    # Criacao de mandatos
    "create_intent_mandate",
    "create_cart_contents",
    "sign_cart_mandate",
    "create_payment_mandate",
    # Validacao
    "validate_cart_mandate",
    "compute_cart_hash",
    # Compatibilidade
    "local_mandate_to_intent",
    "cart_items_to_cart_mandate",
]
