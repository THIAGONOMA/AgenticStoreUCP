"""Modelos do PSP Simulado.

Define os tipos e estruturas de dados para transacoes de pagamento.
"""
from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class PaymentStatus(str, Enum):
    """Status de uma transacao de pagamento."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class WalletSource(str, Enum):
    """Origem da carteira usada no pagamento."""
    STORE = "store_wallet"        # Carteira da loja (checkout do site)
    PERSONAL = "personal_wallet"  # Carteira pessoal do User Agent
    UNKNOWN = "unknown"           # Nao especificado


class WalletToken(BaseModel):
    """Token da carteira virtual do usuario."""
    token: str = Field(..., description="Token unico da carteira")
    wallet_id: str = Field(..., description="ID da carteira")
    user_id: str = Field(default="user_agent", description="ID do usuario")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    @classmethod
    def generate(cls, wallet_id: str, user_id: str = "user_agent") -> "WalletToken":
        """Gerar novo token de carteira."""
        return cls(
            token=f"stk_{uuid.uuid4().hex[:16]}",
            wallet_id=wallet_id,
            user_id=user_id
        )


class WalletInfo(BaseModel):
    """Informacoes da carteira virtual."""
    wallet_id: str = Field(..., description="ID unico da carteira")
    user_id: str = Field(default="user_agent", description="ID do usuario")
    balance: int = Field(default=50000, description="Saldo em centavos (R$ 500,00 inicial)")
    currency: str = Field(default="BRL", description="Moeda")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def balance_formatted(self) -> str:
        """Saldo formatado."""
        return f"R$ {self.balance / 100:.2f}"
    
    def can_debit(self, amount: int) -> bool:
        """Verificar se pode debitar valor."""
        return self.balance >= amount


class PaymentTransaction(BaseModel):
    """Transacao de pagamento processada pelo PSP."""
    id: str = Field(default_factory=lambda: f"psp_txn_{uuid.uuid4().hex[:12]}")
    checkout_session_id: str = Field(..., description="ID da sessao de checkout")
    amount: int = Field(..., description="Valor em centavos")
    currency: str = Field(default="BRL", description="Moeda")
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    
    # Dados da carteira
    wallet_id: Optional[str] = Field(None, description="ID da carteira")
    wallet_token: Optional[str] = Field(None, description="Token usado")
    wallet_source: WalletSource = Field(default=WalletSource.UNKNOWN, description="Origem da carteira")
    
    # Dados do mandato AP2
    mandate_jwt: Optional[str] = Field(None, description="JWT do mandato AP2")
    mandate_valid: bool = Field(default=False, description="Mandato foi validado")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Erro (se falhou)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Estorno
    refunded_amount: int = Field(default=0, description="Valor estornado")
    refunded_at: Optional[datetime] = None
    
    @property
    def amount_formatted(self) -> str:
        """Valor formatado."""
        return f"R$ {self.amount / 100:.2f}"
    
    @property
    def is_refundable(self) -> bool:
        """Pode ser estornado."""
        return self.status == PaymentStatus.COMPLETED and self.refunded_amount < self.amount


class ProcessPaymentRequest(BaseModel):
    """Requisicao de processamento de pagamento."""
    checkout_session_id: str
    amount: int
    currency: str = "BRL"
    wallet_token: str
    mandate_jwt: Optional[str] = None
    wallet_source: WalletSource = WalletSource.UNKNOWN  # Origem da carteira


class ProcessPaymentResponse(BaseModel):
    """Resposta do processamento de pagamento."""
    success: bool
    transaction_id: Optional[str] = None
    status: PaymentStatus
    message: str
    error_code: Optional[str] = None
    
    # Dados adicionais
    amount: Optional[int] = None
    wallet_balance_after: Optional[int] = None
    wallet_source: Optional[WalletSource] = None  # Origem da carteira usada


class RefundRequest(BaseModel):
    """Requisicao de estorno."""
    transaction_id: str
    amount: Optional[int] = None  # None = estorno total
    reason: str = "customer_request"


class RefundResponse(BaseModel):
    """Resposta do estorno."""
    success: bool
    transaction_id: str
    refunded_amount: int
    status: PaymentStatus
    message: str
    wallet_balance_after: Optional[int] = None
