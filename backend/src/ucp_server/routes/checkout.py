"""Routes de checkout UCP."""
from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional
import structlog

from ..models.checkout import (
    CheckoutSession, CheckoutCreate, CheckoutUpdate, CheckoutComplete,
    LineItem, Item, Total, UcpMeta, UcpCapability
)
from ...db.transactions import transactions_repo
from ...db.products import products_repo
from ...db.discounts import discounts_repo
from ...security import get_ap2_security, get_request_signer
from ...payments import get_psp_simulator, ProcessPaymentRequest, PaymentStatus, WalletSource

router = APIRouter()
logger = structlog.get_logger()


def validate_ucp_headers(
    ucp_agent: Optional[str],
    request_signature: Optional[str],
    idempotency_key: Optional[str],
    request_id: Optional[str],
):
    """Validar headers UCP obrigatorios."""
    if ucp_agent:
        logger.debug("UCP headers", agent=ucp_agent, idempotency_key=idempotency_key)
    
    # TODO: Validar assinatura em producao
    # signer = get_request_signer()
    # valid, error = signer.verify_request(headers, payload, method, path)


@router.post("/checkout-sessions", response_model=CheckoutSession)
async def create_checkout_session(
    data: CheckoutCreate,
    request: Request,
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    idempotency_key: Optional[str] = Header(None, alias="idempotency-key"),
    request_id: Optional[str] = Header(None, alias="request-id"),
):
    """
    Criar nova sessao de checkout.
    
    UCP Capability: dev.ucp.shopping.checkout
    """
    validate_ucp_headers(ucp_agent, request_signature, idempotency_key, request_id)
    
    # Enriquecer line items com precos do catalogo
    enriched_items = []
    for item in data.line_items:
        book = await products_repo.get_by_id(item.item.id)
        if not book:
            raise HTTPException(
                status_code=400,
                detail=f"Book not found: {item.item.id}"
            )
        
        enriched_items.append(LineItem(
            item=Item(
                id=book.id,
                title=book.title,
                price=book.price,
            ),
            quantity=item.quantity,
        ))
    
    # Criar sessao
    session = await transactions_repo.create_session(
        line_items=enriched_items,
        buyer=data.buyer,
        currency=data.currency,
    )
    
    logger.info("Checkout session created", session_id=session.id)
    
    return session


@router.get("/checkout-sessions/{session_id}", response_model=CheckoutSession)
async def get_checkout_session(
    session_id: str,
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
):
    """Obter sessao de checkout."""
    session = await transactions_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/checkout-sessions/{session_id}", response_model=CheckoutSession)
async def update_checkout_session(
    session_id: str,
    data: CheckoutUpdate,
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    idempotency_key: Optional[str] = Header(None, alias="idempotency-key"),
    request_id: Optional[str] = Header(None, alias="request-id"),
):
    """
    Atualizar sessao de checkout.
    
    Pode ser usado para aplicar descontos.
    UCP Extension: dev.ucp.shopping.discount
    """
    validate_ucp_headers(ucp_agent, request_signature, idempotency_key, request_id)
    
    session = await transactions_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Session already completed")
    
    # Aplicar descontos
    if data.discounts and data.discounts.codes:
        for code in data.discounts.codes:
            # Verificar se ja foi aplicado
            if code in [d.code for d in session.discounts.applied]:
                continue
            
            # Buscar cupom
            discount = await discounts_repo.get_by_code(code)
            if not discount:
                logger.warning("Invalid discount code", code=code)
                continue
            
            # Calcular subtotal
            subtotal = sum(t.amount for t in session.totals if t.type == "subtotal")
            
            # Verificar validade
            if not discount.is_valid(subtotal):
                logger.warning("Discount not valid", code=code, subtotal=subtotal)
                continue
            
            # Calcular e aplicar desconto
            amount = discount.calculate_discount(subtotal)
            await transactions_repo.apply_discount(
                session_id=session_id,
                code=discount.code,
                title=discount.title,
                amount=amount,
            )
            await discounts_repo.increment_usage(code)
            
            logger.info("Discount applied", code=code, amount=amount)
    
    # Retornar sessao atualizada
    return await transactions_repo.get_session(session_id)


@router.post("/checkout-sessions/{session_id}/complete", response_model=CheckoutSession)
async def complete_checkout_session(
    session_id: str,
    data: CheckoutComplete,
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    idempotency_key: Optional[str] = Header(None, alias="idempotency-key"),
    request_id: Optional[str] = Header(None, alias="request-id"),
):
    """
    Completar sessao de checkout com pagamento.
    
    UCP Capability: dev.ucp.shopping.checkout
    AP2: Valida mandato JWT se fornecido
    """
    validate_ucp_headers(ucp_agent, request_signature, idempotency_key, request_id)
    
    session = await transactions_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Session already completed")
    
    if session.status == "cancelled":
        raise HTTPException(status_code=400, detail="Session was cancelled")
    
    # Validar pagamento
    payment = data.payment
    if not payment.get("token") and not payment.get("mandate"):
        raise HTTPException(status_code=400, detail="Payment token or mandate required")
    
    # Calcular total da sessao
    session_total = sum(t.amount for t in session.totals if t.type == "total")
    
    # Se tem mandato AP2, validar (opcional para demo)
    mandate_jwt = payment.get("mandate")
    mandate_valid = False
    if mandate_jwt:
        ap2 = get_ap2_security()
        result = ap2.validate_mandate(
            jwt=mandate_jwt,
            expected_audience="livraria-ucp",
            required_amount=session_total
        )
        
        if not result.valid:
            logger.warning("AP2 mandate validation failed (continuing for demo)", error=result.error)
            # Nao bloqueia para demo - apenas avisa
            mandate_valid = False
        else:
            mandate_valid = True
            logger.info(
                "AP2 mandate validated",
                max_amount=result.mandate.max_amount,
                currency=result.mandate.currency,
                session_total=session_total
            )
    
    # Verificar estoque disponível antes de processar pagamento
    for item in session.line_items:
        book = await products_repo.get_by_id(item.item.id)
        if book and book.stock < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Estoque insuficiente para '{item.item.title}'. Disponível: {book.stock}, Solicitado: {item.quantity}"
            )
    
    # Processar pagamento via PSP
    wallet_token = payment.get("wallet_token") or payment.get("token", "")
    
    # Se nao tem wallet_token, criar um para o demo
    psp = get_psp_simulator()
    if not wallet_token or wallet_token == "mock_token" or wallet_token == "demo_token":
        # Criar token de carteira automaticamente para demo
        token_info = await psp.create_wallet_token()
        wallet_token = token_info.token
        logger.info("Auto-created wallet token for demo", token=wallet_token[:10] + "...")
    
    # Determinar origem da carteira
    wallet_source_str = payment.get("source", "unknown")
    try:
        wallet_source = WalletSource(wallet_source_str)
    except ValueError:
        # Inferir baseado no prefixo do token
        # wtk_* = carteira pessoal (User Agent)
        # stk_* = carteira da loja (Store)
        if wallet_token.startswith("wtk_"):
            wallet_source = WalletSource.PERSONAL
        elif wallet_token.startswith("stk_"):
            wallet_source = WalletSource.STORE
        else:
            wallet_source = WalletSource.UNKNOWN
    
    # Processar pagamento
    psp_request = ProcessPaymentRequest(
        checkout_session_id=session_id,
        amount=session_total,
        currency="BRL",
        wallet_token=wallet_token,
        mandate_jwt=mandate_jwt,
        wallet_source=wallet_source
    )
    
    psp_response = await psp.process_payment(psp_request)
    
    if not psp_response.success:
        logger.warning(
            "PSP payment failed",
            error_code=psp_response.error_code,
            message=psp_response.message
        )
        raise HTTPException(
            status_code=402, 
            detail=f"Pagamento falhou: {psp_response.message}"
        )
    
    logger.info(
        "PSP payment processed",
        transaction_id=psp_response.transaction_id,
        wallet_balance_after=psp_response.wallet_balance_after
    )
    
    # Decrementar estoque de cada item
    for item in session.line_items:
        await products_repo.update_stock(item.item.id, -item.quantity)
        logger.info("Stock updated", book_id=item.item.id, quantity=-item.quantity)
    
    # Completar sessao
    await transactions_repo.complete_session(session_id)
    
    logger.info(
        "Checkout completed",
        session_id=session_id,
        items_count=len(session.line_items),
        psp_transaction_id=psp_response.transaction_id
    )
    
    # Retornar sessao com info do PSP
    completed_session = await transactions_repo.get_session(session_id)
    
    # Adicionar metadata do PSP na resposta
    return {
        **completed_session.model_dump(),
        "psp_transaction_id": psp_response.transaction_id,
        "wallet_balance_after": psp_response.wallet_balance_after,
        "wallet_source": psp_response.wallet_source.value if psp_response.wallet_source else None
    }


@router.delete("/checkout-sessions/{session_id}")
async def cancel_checkout_session(
    session_id: str,
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
):
    """Cancelar sessao de checkout."""
    session = await transactions_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel completed session")
    
    await transactions_repo.cancel_session(session_id)
    
    logger.info("Checkout cancelled", session_id=session_id)
    
    return {"status": "cancelled", "session_id": session_id}
