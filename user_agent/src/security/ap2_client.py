"""Cliente AP2 para User Agent - Mandatos para pagamentos autonomos.

Implementa o fluxo de 3 mandatos do AP2:
1. IntentMandate - Usuario expressa intencao de compra
2. CartMandate - Merchant assina carrinho (recebido do servidor)
3. PaymentMandate - Usuario autoriza pagamento final
"""
import json
import time
import base64
import hashlib
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from .key_manager import UserKeyManager, get_user_key_manager

# Tentar importar tipos do SDK oficial
try:
    from ap2.types.mandate import IntentMandate, CartMandate, PaymentMandate
    from ap2.types.payment_request import PaymentCurrencyAmount, PaymentItem
    AP2_SDK_AVAILABLE = True
except ImportError:
    AP2_SDK_AVAILABLE = False
    
    # Fallback - tipos locais
    @dataclass
    class IntentMandate:
        description: str
        allowed_merchants: List[str]
        allowed_skus: List[str]
        requires_user_confirmation: bool
        supports_refund: bool
        intent_expiry: str
    
    @dataclass
    class PaymentCurrencyAmount:
        currency: str
        value: str


@dataclass
class MandateInfo:
    """Informacoes do mandato gerado (formato legado)."""
    jwt: str
    max_amount: int
    currency: str
    beneficiary: str
    expires_at: int
    key_id: str


@dataclass
class IntentMandateInfo:
    """Informacoes do IntentMandate."""
    mandate: IntentMandate
    created_at: datetime
    expires_at: datetime


@dataclass
class PaymentMandateInfo:
    """Informacoes do PaymentMandate."""
    mandate_id: str
    jwt: str
    cart_id: str
    total: int
    currency: str
    merchant: str
    created_at: datetime


class AP2Client:
    """
    Cliente AP2 para User Agent.
    
    Gera mandatos JWT para autorizar pagamentos autonomos.
    Suporta o fluxo de 3 mandatos do AP2:
    - IntentMandate: Usuario declara intencao
    - CartMandate: Merchant assina (recebido do servidor)
    - PaymentMandate: Usuario autoriza pagamento
    """
    
    def __init__(self, key_manager: Optional[UserKeyManager] = None):
        """
        Inicializar cliente AP2.
        
        Args:
            key_manager: KeyManager do usuario
        """
        self.key_manager = key_manager or get_user_key_manager()
    
    # =========================================================================
    # Fluxo de 3 Mandatos (AP2 Oficial)
    # =========================================================================
    
    def create_intent_mandate(
        self,
        description: str,
        merchants: List[str] = None,
        skus: List[str] = None,
        requires_confirmation: bool = True,
        supports_refund: bool = False,
        expiry_minutes: int = 60
    ) -> IntentMandateInfo:
        """
        Criar IntentMandate - Usuario expressa intencao de compra.
        
        Args:
            description: Descricao da intencao em linguagem natural
            merchants: Lista de merchants permitidos
            skus: Lista de SKUs permitidos
            requires_confirmation: Exigir confirmacao antes de pagar
            supports_refund: Suportar reembolso
            expiry_minutes: Tempo de expiracao em minutos
            
        Returns:
            IntentMandateInfo com o mandato
        """
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(minutes=expiry_minutes)
        
        mandate = IntentMandate(
            description=description,
            allowed_merchants=merchants or [],
            allowed_skus=skus or [],
            requires_user_confirmation=requires_confirmation,
            supports_refund=supports_refund,
            intent_expiry=expiry.isoformat()
        )
        
        return IntentMandateInfo(
            mandate=mandate,
            created_at=now,
            expires_at=expiry
        )
    
    def create_payment_mandate(
        self,
        cart_id: str,
        cart_total: int,
        currency: str,
        merchant_id: str,
        cart_hash: str = None,
        expiry_seconds: int = 300
    ) -> PaymentMandateInfo:
        """
        Criar PaymentMandate - Usuario autoriza pagamento.
        
        Este e o ultimo passo do fluxo AP2.
        O CartMandate ja foi recebido e validado do merchant.
        
        Args:
            cart_id: ID do carrinho/checkout session
            cart_total: Total em centavos
            currency: Moeda (BRL, USD)
            merchant_id: ID do merchant (URL da loja)
            cart_hash: Hash do carrinho (se disponivel)
            expiry_seconds: Tempo de expiracao
            
        Returns:
            PaymentMandateInfo com JWT assinado
        """
        mandate_id = f"pm_{hashlib.sha256(f'{cart_id}{time.time()}'.encode()).hexdigest()[:12]}"
        
        # Header JWT
        header = {
            "alg": "EdDSA",
            "typ": "JWT",
            "kid": self.key_manager.key_id
        }
        
        # Payload
        now = int(time.time())
        exp = now + expiry_seconds
        
        transaction_data = [cart_hash] if cart_hash else []
        
        payload = {
            "iss": "user-agent",
            "sub": "payment-authorization",
            "aud": merchant_id,
            "iat": now,
            "exp": exp,
            "nonce": mandate_id,
            "payment_mandate_id": mandate_id,
            "cart_id": cart_id,
            "amount": cart_total,
            "currency": currency,
            "transaction_data": transaction_data
        }
        
        # Assinar
        header_b64 = self._base64url_encode(json.dumps(header))
        payload_b64 = self._base64url_encode(json.dumps(payload))
        
        signing_input = f"{header_b64}.{payload_b64}"
        signature = self.key_manager.sign(signing_input)
        
        jwt = f"{signing_input}.{signature}"
        
        return PaymentMandateInfo(
            mandate_id=mandate_id,
            jwt=jwt,
            cart_id=cart_id,
            total=cart_total,
            currency=currency,
            merchant=merchant_id,
            created_at=datetime.now(timezone.utc)
        )
    
    def validate_cart_mandate_jwt(self, cart_mandate_jwt: str) -> Dict[str, Any]:
        """
        Validar CartMandate JWT recebido do merchant.
        
        Args:
            cart_mandate_jwt: JWT do CartMandate
            
        Returns:
            Dict com dados do carrinho se valido
        """
        try:
            parts = cart_mandate_jwt.split(".")
            if len(parts) != 3:
                return {"valid": False, "error": "Invalid JWT format"}
            
            # Decodificar payload
            payload_b64 = parts[1]
            # Adicionar padding se necessario
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            
            # Verificar expiracao
            exp = payload.get("exp", 0)
            if exp < time.time():
                return {"valid": False, "error": "Cart mandate expired"}
            
            return {
                "valid": True,
                "cart_id": payload.get("cart_id"),
                "cart_hash": payload.get("cart_hash"),
                "merchant": payload.get("iss"),
                "expires_at": exp
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    # =========================================================================
    # Mandato Legado (Compatibilidade)
    # =========================================================================
    
    def create_mandate(
        self,
        amount: int,
        currency: str,
        beneficiary: str,
        expiry_seconds: int = 3600
    ) -> MandateInfo:
        """
        Criar mandato de pagamento (formato legado).
        
        Args:
            amount: Valor maximo em centavos
            currency: Moeda (BRL, USD)
            beneficiary: Identificador do comerciante
            expiry_seconds: Tempo de expiracao
            
        Returns:
            MandateInfo com JWT e metadados
        """
        # Header
        header = {
            "alg": "EdDSA",
            "typ": "JWT",
            "kid": self.key_manager.key_id
        }
        
        # Payload
        now = int(time.time())
        exp = now + expiry_seconds
        
        payload = {
            "iss": "user-agent",
            "sub": "agent-autonomous-action",
            "aud": beneficiary,
            "iat": now,
            "exp": exp,
            "scope": "ucp:payment",
            "mandate": {
                "max_amount": amount,
                "currency": currency
            }
        }
        
        # Codificar e assinar
        header_b64 = self._base64url_encode(json.dumps(header))
        payload_b64 = self._base64url_encode(json.dumps(payload))
        
        signing_input = f"{header_b64}.{payload_b64}"
        signature = self.key_manager.sign(signing_input)
        
        jwt = f"{signing_input}.{signature}"
        
        return MandateInfo(
            jwt=jwt,
            max_amount=amount,
            currency=currency,
            beneficiary=beneficiary,
            expires_at=exp,
            key_id=self.key_manager.key_id
        )
    
    def create_mandate_for_checkout(
        self,
        checkout_total: int,
        currency: str,
        store_id: str,
        margin_percent: int = 10
    ) -> MandateInfo:
        """
        Criar mandato para um checkout especifico.
        
        Adiciona margem de seguranca ao valor.
        
        Args:
            checkout_total: Total do checkout em centavos
            currency: Moeda
            store_id: ID da loja
            margin_percent: Margem adicional (para taxas, etc)
            
        Returns:
            MandateInfo
        """
        # Adicionar margem
        max_amount = int(checkout_total * (1 + margin_percent / 100))
        
        return self.create_mandate(
            amount=max_amount,
            currency=currency,
            beneficiary=store_id
        )
    
    # =========================================================================
    # Fluxo Completo
    # =========================================================================
    
    def get_full_mandate_flow(
        self,
        description: str,
        cart_id: str,
        cart_total: int,
        currency: str,
        merchant_id: str,
        merchants: List[str] = None
    ) -> Dict[str, Any]:
        """
        Gerar fluxo completo de mandatos AP2.
        
        Args:
            description: Descricao da intencao
            cart_id: ID do carrinho
            cart_total: Total em centavos
            currency: Moeda
            merchant_id: ID do merchant
            merchants: Lista de merchants permitidos
            
        Returns:
            Dict com os 3 mandatos
        """
        # 1. IntentMandate
        intent = self.create_intent_mandate(
            description=description,
            merchants=merchants or [merchant_id]
        )
        
        # 2. CartMandate - seria recebido do servidor
        # Aqui apenas simulamos a estrutura
        
        # 3. PaymentMandate
        payment = self.create_payment_mandate(
            cart_id=cart_id,
            cart_total=cart_total,
            currency=currency,
            merchant_id=merchant_id
        )
        
        return {
            "intent_mandate": intent,
            "cart_mandate": None,  # Recebido do servidor
            "payment_mandate": payment,
            "sdk_available": AP2_SDK_AVAILABLE
        }
    
    def _base64url_encode(self, data: str) -> str:
        """Codificar em base64url."""
        return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")
    
    @staticmethod
    def is_sdk_available() -> bool:
        """Verificar se SDK oficial esta disponivel."""
        return AP2_SDK_AVAILABLE


# Instancia global
_ap2_client: Optional[AP2Client] = None


def get_ap2_client() -> AP2Client:
    """Obter cliente AP2 (singleton)."""
    global _ap2_client
    if _ap2_client is None:
        _ap2_client = AP2Client()
    return _ap2_client
