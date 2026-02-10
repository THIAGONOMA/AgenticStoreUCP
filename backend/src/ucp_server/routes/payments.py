"""Rotas de Pagamentos PSP.

Endpoints para gerenciar transacoes e carteiras virtuais.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import structlog

from ...payments import (
    PaymentStatus,
    PaymentTransaction,
    WalletInfo,
    ProcessPaymentRequest,
    RefundRequest,
    get_psp_simulator,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/payments", tags=["Payments"])


# =========================================================================
# Request/Response Models
# =========================================================================

class WalletResponse(BaseModel):
    """Resposta com dados da carteira."""
    wallet_id: str
    user_id: str
    balance: int
    balance_formatted: str
    currency: str


class WalletTokenResponse(BaseModel):
    """Resposta com token de carteira."""
    token: str
    wallet_id: str
    message: str


class AddFundsRequest(BaseModel):
    """Requisicao para adicionar fundos."""
    amount: int = 10000  # R$ 100,00 padrao


class TransactionListResponse(BaseModel):
    """Lista de transacoes."""
    transactions: list
    total: int


class RefundRequestBody(BaseModel):
    """Corpo da requisicao de estorno."""
    amount: Optional[int] = None
    reason: str = "customer_request"


# =========================================================================
# Endpoints de Carteira
# =========================================================================

@router.get("/wallet", response_model=WalletResponse)
async def get_wallet(wallet_id: str = "default_wallet"):
    """Obter dados da carteira virtual."""
    psp = get_psp_simulator()
    wallet = await psp.get_wallet(wallet_id)
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Carteira nao encontrada")
    
    return WalletResponse(
        wallet_id=wallet.wallet_id,
        user_id=wallet.user_id,
        balance=wallet.balance,
        balance_formatted=wallet.balance_formatted,
        currency=wallet.currency
    )


@router.post("/wallet/token", response_model=WalletTokenResponse)
async def create_wallet_token(wallet_id: str = "default_wallet"):
    """Criar token de carteira para pagamento."""
    psp = get_psp_simulator()
    
    # Verificar se carteira existe
    wallet = await psp.get_wallet(wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Carteira nao encontrada")
    
    token = await psp.create_wallet_token(wallet_id)
    
    return WalletTokenResponse(
        token=token.token,
        wallet_id=token.wallet_id,
        message="Token criado com sucesso. Use-o para realizar pagamentos."
    )


@router.post("/wallet/add-funds", response_model=WalletResponse)
async def add_funds(
    request: AddFundsRequest,
    wallet_id: str = "default_wallet"
):
    """Adicionar fundos a carteira (para demo)."""
    psp = get_psp_simulator()
    
    wallet = await psp.add_funds(wallet_id, request.amount)
    if not wallet:
        raise HTTPException(status_code=404, detail="Carteira nao encontrada")
    
    logger.info("Funds added to wallet", wallet_id=wallet_id, amount=request.amount)
    
    return WalletResponse(
        wallet_id=wallet.wallet_id,
        user_id=wallet.user_id,
        balance=wallet.balance,
        balance_formatted=wallet.balance_formatted,
        currency=wallet.currency
    )


# =========================================================================
# Endpoints de Transacoes
# =========================================================================

@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None
):
    """Listar transacoes de pagamento."""
    psp = get_psp_simulator()
    
    filter_status = None
    if status:
        try:
            filter_status = PaymentStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status invalido: {status}")
    
    transactions = await psp.list_transactions(limit=limit, status=filter_status)
    
    # Converter para dict para serializar
    txn_list = [
        {
            "id": t.id,
            "checkout_session_id": t.checkout_session_id,
            "amount": t.amount,
            "amount_formatted": t.amount_formatted,
            "currency": t.currency,
            "status": t.status.value,
            "wallet_id": t.wallet_id,
            "mandate_valid": t.mandate_valid,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "refunded_amount": t.refunded_amount,
            "error_message": t.error_message
        }
        for t in transactions
    ]
    
    return TransactionListResponse(
        transactions=txn_list,
        total=len(txn_list)
    )


@router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Obter detalhes de uma transacao."""
    psp = get_psp_simulator()
    txn = await psp.get_transaction(transaction_id)
    
    if not txn:
        raise HTTPException(status_code=404, detail="Transacao nao encontrada")
    
    return {
        "id": txn.id,
        "checkout_session_id": txn.checkout_session_id,
        "amount": txn.amount,
        "amount_formatted": txn.amount_formatted,
        "currency": txn.currency,
        "status": txn.status.value,
        "wallet_id": txn.wallet_id,
        "wallet_token": txn.wallet_token[:10] + "..." if txn.wallet_token else None,
        "mandate_valid": txn.mandate_valid,
        "created_at": txn.created_at.isoformat() if txn.created_at else None,
        "processing_at": txn.processing_at.isoformat() if txn.processing_at else None,
        "completed_at": txn.completed_at.isoformat() if txn.completed_at else None,
        "refunded_amount": txn.refunded_amount,
        "refunded_at": txn.refunded_at.isoformat() if txn.refunded_at else None,
        "error_code": txn.error_code,
        "error_message": txn.error_message,
        "is_refundable": txn.is_refundable
    }


@router.post("/transactions/{transaction_id}/refund")
async def refund_transaction(
    transaction_id: str,
    request: RefundRequestBody
):
    """Estornar uma transacao."""
    psp = get_psp_simulator()
    
    refund_request = RefundRequest(
        transaction_id=transaction_id,
        amount=request.amount,
        reason=request.reason
    )
    
    response = await psp.refund(refund_request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    
    return {
        "success": response.success,
        "transaction_id": response.transaction_id,
        "refunded_amount": response.refunded_amount,
        "refunded_amount_formatted": f"R$ {response.refunded_amount / 100:.2f}",
        "status": response.status.value,
        "message": response.message,
        "wallet_balance_after": response.wallet_balance_after,
        "wallet_balance_formatted": f"R$ {response.wallet_balance_after / 100:.2f}" if response.wallet_balance_after else None
    }


# =========================================================================
# Endpoint de Status
# =========================================================================

@router.get("/status")
async def psp_status():
    """Status do PSP Simulator."""
    psp = get_psp_simulator()
    await psp.initialize()
    
    wallet = await psp.get_wallet()
    transactions = await psp.list_transactions(limit=5)
    
    return {
        "name": psp.name,
        "version": psp.version,
        "status": "operational",
        "default_wallet": {
            "wallet_id": wallet.wallet_id if wallet else None,
            "balance": wallet.balance if wallet else 0,
            "balance_formatted": wallet.balance_formatted if wallet else "R$ 0,00"
        },
        "recent_transactions": len(transactions)
    }
