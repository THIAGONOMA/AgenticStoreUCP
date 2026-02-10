"""PSP Simulator - Payment Service Provider Simulado.

Simula o processamento de pagamentos integrando:
- Validacao de mandatos AP2
- Debito em carteira virtual
- Registro de transacoes
- Integracao com carteira pessoal do User Agent
"""
import asyncio
import os
from typing import Optional
from datetime import datetime
import structlog
import httpx

from .models import (
    PaymentStatus,
    PaymentTransaction,
    ProcessPaymentRequest,
    ProcessPaymentResponse,
    RefundRequest,
    RefundResponse,
    WalletInfo,
    WalletSource,
)
from ..db.payments import payments_repo
from ..security import get_ap2_security

logger = structlog.get_logger()

# URL da API do User Agent
USER_AGENT_API_URL = os.environ.get("USER_AGENT_API_URL", "http://localhost:8001")


class PSPSimulator:
    """
    Payment Service Provider Simulado.
    
    Processa pagamentos validando:
    1. Token da carteira virtual
    2. Mandato AP2 (opcional mas recomendado)
    3. Saldo disponivel
    """
    
    def __init__(self):
        """Inicializar PSP."""
        self.name = "PSP Simulado UCP"
        self.version = "1.0.0"
        self._initialized = False
    
    async def initialize(self):
        """Inicializar tabelas e dados."""
        if self._initialized:
            return
        await payments_repo.init_tables()
        self._initialized = True
        logger.info("PSP Simulator initialized")
    
    async def _process_personal_wallet_payment(
        self,
        request: ProcessPaymentRequest,
        mandate_valid: bool
    ) -> ProcessPaymentResponse:
        """
        Processar pagamento via carteira pessoal do User Agent.
        
        Chama a API do User Agent para validar e debitar.
        """
        logger.info(
            "Processing payment via personal wallet",
            token=request.wallet_token[:15] + "...",
            amount=request.amount
        )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1. Processar pagamento via User Agent API
                response = await client.post(
                    f"{USER_AGENT_API_URL}/wallet/process-payment",
                    json={
                        "token": request.wallet_token,
                        "amount": request.amount,
                        "description": f"Compra via UCP - {request.checkout_session_id}",
                        "psp_transaction_id": None,  # Sera preenchido depois
                        "checkout_session_id": request.checkout_session_id
                    }
                )
                
                result = response.json()
                
                if not result.get("success"):
                    logger.warning(
                        "Personal wallet payment failed",
                        error=result.get("error")
                    )
                    return ProcessPaymentResponse(
                        success=False,
                        status=PaymentStatus.FAILED,
                        message=result.get("error", "Falha no pagamento"),
                        error_code="PERSONAL_WALLET_ERROR"
                    )
                
                # 2. Registrar transacao no PSP local (para historico)
                txn = await payments_repo.create_transaction(
                    checkout_session_id=request.checkout_session_id,
                    amount=request.amount,
                    currency=request.currency,
                    wallet_id="personal_wallet",
                    wallet_token=request.wallet_token,
                    mandate_jwt=request.mandate_jwt,
                    wallet_source=WalletSource.PERSONAL
                )
                
                # 3. Marcar como completada
                await payments_repo.update_transaction_status(
                    txn.id,
                    PaymentStatus.COMPLETED,
                    mandate_valid=mandate_valid
                )
                
                logger.info(
                    "Personal wallet payment completed",
                    transaction_id=txn.id,
                    ua_transaction_id=result.get("transaction_id"),
                    new_balance=result.get("new_balance")
                )
                
                return ProcessPaymentResponse(
                    success=True,
                    transaction_id=txn.id,
                    status=PaymentStatus.COMPLETED,
                    message="Pagamento processado via carteira pessoal!",
                    amount=request.amount,
                    wallet_balance_after=result.get("new_balance"),
                    wallet_source=WalletSource.PERSONAL
                )
                
        except httpx.ConnectError:
            logger.error("User Agent API not available")
            return ProcessPaymentResponse(
                success=False,
                status=PaymentStatus.FAILED,
                message="Carteira pessoal indisponivel. Execute: make up-ua-api",
                error_code="USER_AGENT_UNAVAILABLE"
            )
        except Exception as e:
            logger.error("Personal wallet payment error", error=str(e))
            return ProcessPaymentResponse(
                success=False,
                status=PaymentStatus.FAILED,
                message=f"Erro ao processar pagamento: {str(e)}",
                error_code="PAYMENT_ERROR"
            )

    async def process_payment(
        self,
        request: ProcessPaymentRequest
    ) -> ProcessPaymentResponse:
        """
        Processar pagamento.
        
        Fluxo:
        1. Detectar tipo de carteira (pessoal ou loja)
        2. Validar mandato AP2 (se fornecido)
        3. Processar via carteira apropriada
        """
        logger.info(
            "Processing payment",
            checkout_session_id=request.checkout_session_id,
            amount=request.amount,
            has_mandate=bool(request.mandate_jwt),
            wallet_source=request.wallet_source.value,
            token_prefix=request.wallet_token[:4] if request.wallet_token else None
        )
        
        # Garantir inicializacao
        await self.initialize()
        
        # Validar mandato AP2 (se fornecido)
        mandate_valid = False
        if request.mandate_jwt:
            ap2 = get_ap2_security()
            result = ap2.validate_mandate(
                jwt=request.mandate_jwt,
                expected_audience="livraria-ucp",
                required_amount=request.amount
            )
            mandate_valid = result.valid
            
            if not mandate_valid:
                logger.warning("Invalid AP2 mandate", error=result.error)
                # Continuar mesmo sem mandato valido (para demo)
        
        # Detectar carteira pessoal (tokens wtk_* do User Agent)
        if request.wallet_token and request.wallet_token.startswith("wtk_"):
            return await self._process_personal_wallet_payment(request, mandate_valid)
        
        # Fluxo padrao: carteira da loja (tokens stk_*)
        # 1. Validar token da carteira
        wallet = await payments_repo.validate_token(request.wallet_token)
        if not wallet:
            logger.warning("Invalid wallet token", token=request.wallet_token[:10] + "...")
            return ProcessPaymentResponse(
                success=False,
                status=PaymentStatus.FAILED,
                message="Token de carteira invalido",
                error_code="INVALID_WALLET_TOKEN"
            )
        
        # 2. Verificar saldo
        if not wallet.can_debit(request.amount):
            logger.warning(
                "Insufficient balance",
                wallet_id=wallet.wallet_id,
                balance=wallet.balance,
                required=request.amount
            )
            return ProcessPaymentResponse(
                success=False,
                status=PaymentStatus.FAILED,
                message=f"Saldo insuficiente. Disponivel: {wallet.balance_formatted}",
                error_code="INSUFFICIENT_BALANCE",
                wallet_balance_after=wallet.balance
            )
        
        # 3. Criar transacao
        txn = await payments_repo.create_transaction(
            checkout_session_id=request.checkout_session_id,
            amount=request.amount,
            currency=request.currency,
            wallet_id=wallet.wallet_id,
            wallet_token=request.wallet_token,
            mandate_jwt=request.mandate_jwt,
            wallet_source=request.wallet_source
        )
        
        # 4. Atualizar status para processing
        await payments_repo.update_transaction_status(
            txn.id,
            PaymentStatus.PROCESSING,
            mandate_valid=mandate_valid
        )
        
        # Simular delay de processamento
        await asyncio.sleep(0.5)
        
        # 5. Debitar carteira
        updated_wallet = await payments_repo.debit_wallet(wallet.wallet_id, request.amount)
        if not updated_wallet:
            await payments_repo.update_transaction_status(
                txn.id,
                PaymentStatus.FAILED,
                error_code="DEBIT_FAILED",
                error_message="Falha ao debitar carteira"
            )
            return ProcessPaymentResponse(
                success=False,
                transaction_id=txn.id,
                status=PaymentStatus.FAILED,
                message="Falha ao debitar carteira",
                error_code="DEBIT_FAILED"
            )
        
        # 6. Marcar token como usado
        await payments_repo.mark_token_used(request.wallet_token)
        
        # 7. Completar transacao
        await payments_repo.update_transaction_status(
            txn.id,
            PaymentStatus.COMPLETED,
            mandate_valid=mandate_valid
        )
        
        logger.info(
            "Payment completed",
            transaction_id=txn.id,
            amount=request.amount,
            wallet_balance_after=updated_wallet.balance
        )
        
        return ProcessPaymentResponse(
            success=True,
            transaction_id=txn.id,
            status=PaymentStatus.COMPLETED,
            message="Pagamento processado com sucesso!",
            amount=request.amount,
            wallet_balance_after=updated_wallet.balance,
            wallet_source=request.wallet_source
        )
    
    async def refund(self, request: RefundRequest) -> RefundResponse:
        """
        Processar estorno.
        
        Fluxo:
        1. Buscar transacao original
        2. Verificar se pode estornar
        3. Creditar carteira
        4. Atualizar transacao
        """
        logger.info("Processing refund", transaction_id=request.transaction_id)
        
        # Garantir inicializacao
        await self.initialize()
        
        # 1. Buscar transacao
        txn = await payments_repo.get_transaction(request.transaction_id)
        if not txn:
            return RefundResponse(
                success=False,
                transaction_id=request.transaction_id,
                refunded_amount=0,
                status=PaymentStatus.FAILED,
                message="Transacao nao encontrada"
            )
        
        # 2. Verificar se pode estornar
        if not txn.is_refundable:
            return RefundResponse(
                success=False,
                transaction_id=request.transaction_id,
                refunded_amount=0,
                status=txn.status,
                message="Transacao nao pode ser estornada"
            )
        
        # 3. Calcular valor do estorno
        refund_amount = request.amount or (txn.amount - txn.refunded_amount)
        max_refundable = txn.amount - txn.refunded_amount
        
        if refund_amount > max_refundable:
            refund_amount = max_refundable
        
        # 4. Creditar carteira
        wallet = None
        if txn.wallet_id:
            wallet = await payments_repo.credit_wallet(txn.wallet_id, refund_amount)
        
        # 5. Atualizar transacao
        await payments_repo.refund_transaction(txn.id, refund_amount)
        
        # Buscar transacao atualizada
        updated_txn = await payments_repo.get_transaction(txn.id)
        
        logger.info(
            "Refund completed",
            transaction_id=txn.id,
            refunded_amount=refund_amount,
            wallet_balance=wallet.balance if wallet else None
        )
        
        return RefundResponse(
            success=True,
            transaction_id=txn.id,
            refunded_amount=refund_amount,
            status=updated_txn.status,
            message=f"Estorno de R$ {refund_amount / 100:.2f} processado",
            wallet_balance_after=wallet.balance if wallet else None
        )
    
    async def get_transaction(self, transaction_id: str) -> Optional[PaymentTransaction]:
        """Buscar transacao por ID."""
        await self.initialize()
        return await payments_repo.get_transaction(transaction_id)
    
    async def get_wallet(self, wallet_id: str = "default_wallet") -> Optional[WalletInfo]:
        """Buscar carteira."""
        await self.initialize()
        return await payments_repo.get_wallet(wallet_id)
    
    async def create_wallet_token(
        self,
        wallet_id: str = "default_wallet",
        user_id: str = "user_agent"
    ):
        """Criar token de carteira para pagamento."""
        await self.initialize()
        return await payments_repo.create_wallet_token(wallet_id, user_id)
    
    async def add_funds(
        self,
        wallet_id: str = "default_wallet",
        amount: int = 10000  # R$ 100,00
    ) -> Optional[WalletInfo]:
        """Adicionar fundos a carteira (para demo)."""
        await self.initialize()
        return await payments_repo.credit_wallet(wallet_id, amount)
    
    async def list_transactions(
        self,
        limit: int = 50,
        status: Optional[PaymentStatus] = None
    ):
        """Listar transacoes."""
        await self.initialize()
        return await payments_repo.list_transactions(limit=limit, status=status)


# Instancia global (singleton)
_psp_instance: Optional[PSPSimulator] = None


def get_psp_simulator() -> PSPSimulator:
    """Obter instancia do PSP Simulator."""
    global _psp_instance
    if _psp_instance is None:
        _psp_instance = PSPSimulator()
    return _psp_instance
