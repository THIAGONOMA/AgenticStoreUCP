"""Seguranca AP2 - Mandatos JWT para pagamentos autonomos.

Implementa o Agent Payments Protocol (AP2) seguindo o padrao oficial
do Google (google-agentic-commerce/AP2).

Tipos de Mandatos (SDK Oficial):
- IntentMandate: Intencao do usuario (o que quer comprar)
- CartMandate: Carrinho assinado pelo merchant (garantia de preco)
- PaymentMandate: Autorizacao final para pagamento

Compatibilidade:
- Mantem suporte ao mandato simples (max_amount/currency) para retrocompatibilidade
- Adiciona suporte completo aos 3 tipos de mandatos oficiais
"""
import json
import time
import uuid
import base64
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .key_manager import KeyManager, get_server_key_manager

# Imports do SDK AP2 oficial (com fallback)
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
)
from .ap2_adapters import (
    create_intent_mandate,
    create_cart_contents,
    sign_cart_mandate,
    create_payment_mandate,
    validate_cart_mandate,
    cart_items_to_cart_mandate,
)


@dataclass
class MandatePayload:
    """Payload do mandato AP2 (formato legado)."""
    max_amount: int  # em centavos
    currency: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_amount": self.max_amount,
            "currency": self.currency
        }


@dataclass
class MandateValidationResult:
    """Resultado da validacao de um mandato."""
    valid: bool
    error: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    mandate: Optional[MandatePayload] = None
    # Novos campos para mandatos oficiais
    intent_mandate: Optional[IntentMandate] = None
    cart_mandate: Optional[CartMandate] = None
    payment_mandate: Optional[PaymentMandate] = None


class AP2Security:
    """
    Gerenciador de seguranca AP2.
    
    Cria e valida mandatos JWT para pagamentos autonomos entre agentes.
    """
    
    def __init__(self, key_manager: Optional[KeyManager] = None):
        """
        Inicializar AP2 Security.
        
        Args:
            key_manager: KeyManager para assinaturas (usa servidor se nao fornecido)
        """
        self.key_manager = key_manager or get_server_key_manager()
    
    def create_mandate(
        self,
        amount: int,
        currency: str,
        beneficiary: str,
        expiry_seconds: int = 3600,
        issuer: str = "livraria-ucp",
        subject: str = "agent-autonomous-action"
    ) -> str:
        """
        Criar mandato JWT para pagamento autonomo.
        
        Args:
            amount: Valor maximo em centavos
            currency: Moeda (BRL, USD, etc)
            beneficiary: Identificador do beneficiario (audience)
            expiry_seconds: Tempo de expiracao em segundos
            issuer: Emissor do mandato
            subject: Sujeito do mandato
            
        Returns:
            JWT assinado
        """
        # Header
        header = {
            "alg": "EdDSA",
            "typ": "JWT",
            "kid": self.key_manager.key_id
        }
        
        # Payload
        now = int(time.time())
        payload = {
            "iss": issuer,
            "sub": subject,
            "aud": beneficiary,
            "iat": now,
            "exp": now + expiry_seconds,
            "scope": "ucp:payment",
            "mandate": {
                "max_amount": amount,
                "currency": currency
            }
        }
        
        # Codificar
        header_b64 = self._base64url_encode(json.dumps(header))
        payload_b64 = self._base64url_encode(json.dumps(payload))
        
        # Assinar
        signing_input = f"{header_b64}.{payload_b64}"
        signature = self.key_manager.sign(signing_input)
        
        return f"{signing_input}.{signature}"
    
    def validate_mandate(
        self,
        jwt: str,
        expected_audience: Optional[str] = None,
        required_amount: Optional[int] = None
    ) -> MandateValidationResult:
        """
        Validar mandato JWT.
        
        Args:
            jwt: Token JWT
            expected_audience: Audience esperado (opcional)
            required_amount: Valor requerido para validar contra max_amount
            
        Returns:
            Resultado da validacao
        """
        try:
            # Separar partes
            parts = jwt.split(".")
            if len(parts) != 3:
                return MandateValidationResult(valid=False, error="Invalid JWT format")
            
            header_b64, payload_b64, signature = parts
            
            # Decodificar header
            header = json.loads(self._base64url_decode(header_b64))
            
            # Verificar algoritmo
            if header.get("alg") != "EdDSA":
                return MandateValidationResult(valid=False, error="Invalid algorithm")
            
            # Verificar assinatura
            signing_input = f"{header_b64}.{payload_b64}"
            if not self.key_manager.verify(signing_input, signature):
                return MandateValidationResult(valid=False, error="Invalid signature")
            
            # Decodificar payload
            payload = json.loads(self._base64url_decode(payload_b64))
            
            # Verificar expiracao
            exp = payload.get("exp", 0)
            if time.time() > exp:
                return MandateValidationResult(valid=False, error="Token expired")
            
            # Verificar scope
            if payload.get("scope") != "ucp:payment":
                return MandateValidationResult(valid=False, error="Invalid scope")
            
            # Verificar audience
            if expected_audience and payload.get("aud") != expected_audience:
                return MandateValidationResult(valid=False, error="Invalid audience")
            
            # Extrair mandato
            mandate_data = payload.get("mandate", {})
            mandate = MandatePayload(
                max_amount=mandate_data.get("max_amount", 0),
                currency=mandate_data.get("currency", "BRL")
            )
            
            # Verificar valor
            if required_amount is not None and required_amount > mandate.max_amount:
                return MandateValidationResult(
                    valid=False,
                    error=f"Amount {required_amount} exceeds mandate limit {mandate.max_amount}"
                )
            
            return MandateValidationResult(
                valid=True,
                payload=payload,
                mandate=mandate
            )
            
        except json.JSONDecodeError:
            return MandateValidationResult(valid=False, error="Invalid JSON in token")
        except Exception as e:
            return MandateValidationResult(valid=False, error=str(e))
    
    def _base64url_encode(self, data: str) -> str:
        """Codificar em base64url."""
        return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")
    
    def _base64url_decode(self, data: str) -> str:
        """Decodificar de base64url."""
        # Adicionar padding
        padded = data + "=" * (4 - len(data) % 4)
        return base64.urlsafe_b64decode(padded).decode()
    
    # ==========================================================================
    # Novos metodos para mandatos oficiais AP2 (SDK Google)
    # ==========================================================================
    
    def create_intent_mandate(
        self,
        description: str,
        merchants: Optional[List[str]] = None,
        skus: Optional[List[str]] = None,
        requires_confirmation: bool = True,
        expiry_minutes: int = 60,
    ) -> IntentMandate:
        """
        Criar IntentMandate - expressa intencao de compra do usuario.
        
        Este e o primeiro mandato no fluxo AP2. O usuario declara
        o que deseja comprar em linguagem natural.
        
        Args:
            description: Descricao em linguagem natural da intencao
            merchants: Lista de merchants permitidos (None = qualquer)
            skus: Lista de SKUs especificos permitidos
            requires_confirmation: Se requer confirmacao do usuario
            expiry_minutes: Tempo de expiracao em minutos
            
        Returns:
            IntentMandate configurado
        """
        return create_intent_mandate(
            description=description,
            merchants=merchants,
            skus=skus,
            requires_confirmation=requires_confirmation,
            expiry_minutes=expiry_minutes,
        )
    
    def create_cart_mandate(
        self,
        cart_items: List[Dict[str, Any]],
        cart_id: str,
        merchant_name: str = "Livraria Virtual UCP",
        currency: str = "BRL",
    ) -> CartMandate:
        """
        Criar CartMandate - carrinho assinado pelo merchant.
        
        Este e o segundo mandato no fluxo AP2. O merchant assina
        o carrinho garantindo precos e disponibilidade.
        
        Args:
            cart_items: Lista de itens [{title, price, quantity}]
            cart_id: ID do carrinho/sessao
            merchant_name: Nome do merchant
            currency: Codigo da moeda
            
        Returns:
            CartMandate assinado com JWT
        """
        return cart_items_to_cart_mandate(
            cart_items=cart_items,
            cart_id=cart_id,
            merchant_name=merchant_name,
            key_manager=self.key_manager,
            currency=currency,
        )
    
    def create_payment_mandate(
        self,
        cart_mandate: CartMandate,
        payment_method: str = "dev.ucp.mock_payment",
        payer_name: Optional[str] = None,
        payer_email: Optional[str] = None,
    ) -> PaymentMandate:
        """
        Criar PaymentMandate - autorizacao final de pagamento.
        
        Este e o terceiro mandato no fluxo AP2. Apos o usuario
        confirmar o carrinho, este mandato autoriza o pagamento.
        
        Args:
            cart_mandate: CartMandate assinado
            payment_method: Metodo de pagamento escolhido
            payer_name: Nome do pagador
            payer_email: Email do pagador
            
        Returns:
            PaymentMandate com autorizacao do usuario
        """
        return create_payment_mandate(
            cart_mandate=cart_mandate,
            payment_method=payment_method,
            key_manager=self.key_manager,
            payer_name=payer_name,
            payer_email=payer_email,
        )
    
    def validate_cart_mandate(
        self,
        cart_mandate: CartMandate,
    ) -> MandateValidationResult:
        """
        Validar CartMandate e sua assinatura JWT.
        
        Args:
            cart_mandate: CartMandate a ser validado
            
        Returns:
            MandateValidationResult com detalhes da validacao
        """
        result = validate_cart_mandate(cart_mandate, self.key_manager)
        
        if result.get("valid"):
            return MandateValidationResult(
                valid=True,
                payload=result,
                cart_mandate=cart_mandate,
            )
        else:
            return MandateValidationResult(
                valid=False,
                error=result.get("error"),
            )
    
    def get_full_mandate_flow(
        self,
        cart_items: List[Dict[str, Any]],
        cart_id: str,
        description: str = "Compra de livros",
        payment_method: str = "dev.ucp.mock_payment",
        payer_name: Optional[str] = None,
        payer_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executar fluxo completo de mandatos AP2.
        
        Gera os 3 mandatos em sequencia:
        1. IntentMandate
        2. CartMandate
        3. PaymentMandate
        
        Args:
            cart_items: Itens do carrinho
            cart_id: ID do carrinho
            description: Descricao da intencao
            payment_method: Metodo de pagamento
            payer_name: Nome do pagador
            payer_email: Email do pagador
            
        Returns:
            Dict com os 3 mandatos e metadados
        """
        # 1. Intent Mandate
        intent = self.create_intent_mandate(
            description=description,
            merchants=["livraria-ucp"],
        )
        
        # 2. Cart Mandate
        cart = self.create_cart_mandate(
            cart_items=cart_items,
            cart_id=cart_id,
        )
        
        # 3. Payment Mandate
        payment = self.create_payment_mandate(
            cart_mandate=cart,
            payment_method=payment_method,
            payer_name=payer_name,
            payer_email=payer_email,
        )
        
        return {
            "intent_mandate": intent,
            "cart_mandate": cart,
            "payment_mandate": payment,
            "flow_id": cart_id,
            "sdk_available": is_ap2_sdk_available(),
        }
    
    @staticmethod
    def is_sdk_available() -> bool:
        """Verificar se SDK AP2 oficial esta disponivel."""
        return is_ap2_sdk_available()


# Instancia global
_ap2_security: Optional[AP2Security] = None


def get_ap2_security() -> AP2Security:
    """Obter instancia AP2Security (singleton)."""
    global _ap2_security
    if _ap2_security is None:
        _ap2_security = AP2Security()
    return _ap2_security
