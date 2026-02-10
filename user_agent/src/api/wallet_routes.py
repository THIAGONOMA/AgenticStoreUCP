"""Rotas REST da Carteira Pessoal.

Endpoints para gerenciar a carteira virtual do User Agent.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

from ..wallet import get_wallet

logger = structlog.get_logger()
router = APIRouter(prefix="/wallet", tags=["Wallet"])


# =========================================================================
# Request/Response Models
# =========================================================================

class WalletInfoResponse(BaseModel):
    """Informacoes da carteira."""
    wallet_id: str
    balance: int
    balance_formatted: str
    currency: str
    transaction_count: int


class WalletTokenResponse(BaseModel):
    """Token de pagamento gerado."""
    token: str
    wallet_id: str


class AddFundsRequest(BaseModel):
    """Request para adicionar fundos."""
    amount: int  # Em centavos


class AddFundsResponse(BaseModel):
    """Resposta ao adicionar fundos."""
    success: bool
    new_balance: int
    new_balance_formatted: str


class TransactionResponse(BaseModel):
    """Uma transacao da carteira."""
    id: str
    type: str
    amount: int
    description: str
    timestamp: str
    balance_after: int
    psp_transaction_id: Optional[str] = None
    checkout_session_id: Optional[str] = None


class TransactionListResponse(BaseModel):
    """Lista de transacoes."""
    transactions: List[TransactionResponse]
    total_count: int


class DebitRequest(BaseModel):
    """Request para debitar da carteira."""
    amount: int
    description: str
    psp_transaction_id: Optional[str] = None
    checkout_session_id: Optional[str] = None


class DebitResponse(BaseModel):
    """Resposta do debito."""
    success: bool
    transaction_id: str
    new_balance: int
    new_balance_formatted: str


class ValidateTokenRequest(BaseModel):
    """Request para validar token."""
    token: str


class ValidateTokenResponse(BaseModel):
    """Resposta da validacao de token."""
    valid: bool
    wallet_id: Optional[str] = None
    balance: Optional[int] = None
    can_pay: Optional[bool] = None


class ProcessPaymentRequest(BaseModel):
    """Request para processar pagamento via token."""
    token: str
    amount: int
    description: str
    psp_transaction_id: Optional[str] = None
    checkout_session_id: Optional[str] = None


class ProcessPaymentResponse(BaseModel):
    """Resposta do processamento de pagamento."""
    success: bool
    transaction_id: Optional[str] = None
    new_balance: Optional[int] = None
    new_balance_formatted: Optional[str] = None
    error: Optional[str] = None


# =========================================================================
# Endpoints
# =========================================================================

@router.get("", response_model=WalletInfoResponse)
@router.get("/", response_model=WalletInfoResponse)
async def get_wallet_info():
    """
    Obter informacoes da carteira pessoal.
    
    Retorna saldo, moeda e contagem de transacoes.
    """
    wallet = get_wallet()
    
    logger.info("Wallet info requested", wallet_id=wallet.wallet_id)
    
    return WalletInfoResponse(
        wallet_id=wallet.wallet_id,
        balance=wallet.balance,
        balance_formatted=wallet.balance_formatted,
        currency=wallet.currency,
        transaction_count=len(wallet._transactions)
    )


@router.post("/token", response_model=WalletTokenResponse)
async def create_payment_token():
    """
    Gerar token de pagamento.
    
    O token pode ser usado para autorizar um pagamento via PSP.
    """
    wallet = get_wallet()
    
    # generate_payment_token retorna string diretamente
    token = wallet.generate_payment_token()
    
    logger.info(
        "Wallet token created",
        wallet_id=wallet.wallet_id,
        token=token[:15] + "..."
    )
    
    return WalletTokenResponse(
        token=token,
        wallet_id=wallet.wallet_id
    )


@router.post("/add-funds", response_model=AddFundsResponse)
async def add_funds(request: AddFundsRequest):
    """
    Adicionar fundos na carteira (simulado).
    
    Usado para demonstracao.
    """
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")
    
    if request.amount > 1000000:  # Max R$ 10.000,00
        raise HTTPException(status_code=400, detail="Valor maximo excedido")
    
    wallet = get_wallet()
    wallet.add_funds(request.amount, "Deposito simulado")
    
    logger.info(
        "Funds added to personal wallet",
        amount=request.amount,
        wallet_id=wallet.wallet_id,
        new_balance=wallet.balance
    )
    
    return AddFundsResponse(
        success=True,
        new_balance=wallet.balance,
        new_balance_formatted=wallet.balance_formatted
    )


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(limit: int = 20):
    """
    Listar transacoes recentes da carteira.
    """
    wallet = get_wallet()
    
    transactions = wallet.get_recent_transactions(limit)
    
    return TransactionListResponse(
        transactions=[
            TransactionResponse(
                id=t.id,
                type=t.type,
                amount=t.amount,
                description=t.description,
                timestamp=t.timestamp.isoformat(),
                balance_after=t.balance_after,
                psp_transaction_id=t.psp_transaction_id,
                checkout_session_id=t.checkout_session_id
            )
            for t in transactions
        ],
        total_count=len(wallet._transactions)
    )


@router.post("/debit", response_model=DebitResponse)
async def debit_wallet(request: DebitRequest):
    """
    Debitar valor da carteira.
    
    Usado pelo PSP ou simulacao para registrar pagamentos.
    """
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")
    
    wallet = get_wallet()
    
    if not wallet.can_pay(request.amount):
        raise HTTPException(
            status_code=402,
            detail=f"Saldo insuficiente. Disponivel: {wallet.balance_formatted}"
        )
    
    transaction = wallet.debit(
        amount=request.amount,
        description=request.description,
        psp_transaction_id=request.psp_transaction_id,
        checkout_session_id=request.checkout_session_id
    )
    
    logger.info(
        "Wallet debited",
        amount=request.amount,
        transaction_id=transaction.id,
        new_balance=wallet.balance
    )
    
    return DebitResponse(
        success=True,
        transaction_id=transaction.id,
        new_balance=wallet.balance,
        new_balance_formatted=wallet.balance_formatted
    )


@router.get("/can-pay/{amount}")
async def check_can_pay(amount: int):
    """
    Verificar se pode pagar um valor.
    """
    wallet = get_wallet()
    
    return {
        "can_pay": wallet.can_pay(amount),
        "balance": wallet.balance,
        "amount": amount,
        "difference": wallet.balance - amount
    }


@router.post("/validate-token", response_model=ValidateTokenResponse)
async def validate_token(request: ValidateTokenRequest):
    """
    Validar token de pagamento.
    
    Usado pelo PSP para verificar se o token e valido.
    """
    wallet = get_wallet()
    
    is_valid = wallet.validate_token(request.token)
    
    if is_valid:
        logger.info(
            "Token validated successfully",
            token=request.token[:15] + "..."
        )
        return ValidateTokenResponse(
            valid=True,
            wallet_id=wallet.wallet_id,
            balance=wallet.balance,
            can_pay=True
        )
    
    return ValidateTokenResponse(valid=False)


@router.post("/process-payment", response_model=ProcessPaymentResponse)
async def process_payment(request: ProcessPaymentRequest):
    """
    Processar pagamento usando token.
    
    Usado pelo PSP para debitar a carteira pessoal.
    """
    wallet = get_wallet()
    
    # Validar token
    if not wallet.validate_token(request.token):
        logger.warning(
            "Invalid token for payment",
            token=request.token[:15] + "..."
        )
        return ProcessPaymentResponse(
            success=False,
            error="Token invalido ou ja usado"
        )
    
    # Verificar saldo
    if not wallet.can_pay(request.amount):
        logger.warning(
            "Insufficient balance for payment",
            amount=request.amount,
            balance=wallet.balance
        )
        return ProcessPaymentResponse(
            success=False,
            error=f"Saldo insuficiente. Disponivel: {wallet.balance_formatted}"
        )
    
    # Debitar carteira
    transaction = wallet.debit(
        amount=request.amount,
        description=request.description,
        psp_transaction_id=request.psp_transaction_id,
        checkout_session_id=request.checkout_session_id
    )
    
    if not transaction:
        return ProcessPaymentResponse(
            success=False,
            error="Falha ao debitar carteira"
        )
    
    # Marcar token como usado
    wallet.use_token(request.token)
    
    logger.info(
        "Payment processed via personal wallet",
        amount=request.amount,
        transaction_id=transaction.id,
        new_balance=wallet.balance
    )
    
    return ProcessPaymentResponse(
        success=True,
        transaction_id=transaction.id,
        new_balance=wallet.balance,
        new_balance_formatted=wallet.balance_formatted
    )
