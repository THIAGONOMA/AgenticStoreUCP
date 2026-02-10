"""MCP Tools - Pagamentos e Transacoes."""
from typing import Any, Dict
from mcp.types import Tool


def get_payment_tools() -> list[Tool]:
    """Retorna ferramentas de pagamentos."""
    return [
        Tool(
            name="get_wallet_balance",
            description="Consultar saldo da carteira virtual da loja",
            inputSchema={
                "type": "object",
                "properties": {
                    "wallet_id": {
                        "type": "string",
                        "description": "ID da carteira (opcional, usa default)"
                    }
                }
            }
        ),
        Tool(
            name="list_transactions",
            description="Listar transacoes de pagamento recentes",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Numero maximo de transacoes (default: 10)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filtrar por status (success, failed, pending)"
                    },
                    "wallet_source": {
                        "type": "string",
                        "description": "Filtrar por origem (store_wallet, personal_wallet)"
                    }
                }
            }
        ),
        Tool(
            name="get_transaction",
            description="Obter detalhes de uma transacao especifica",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "ID da transacao"
                    }
                },
                "required": ["transaction_id"]
            }
        ),
    ]


async def get_wallet_balance(args: Dict[str, Any]) -> Dict[str, Any]:
    """Consultar saldo da carteira."""
    # Importacao lazy para evitar ciclo
    from ...db.payments import payments_repo
    
    wallet_id = args.get("wallet_id", "default_wallet")
    
    balance = await payments_repo.get_wallet_balance(wallet_id)
    
    return {
        "wallet_id": wallet_id,
        "balance": balance,
        "balance_formatted": f"R$ {balance / 100:.2f}",
        "currency": "BRL",
        "type": "store_wallet"
    }


async def list_transactions(args: Dict[str, Any]) -> Dict[str, Any]:
    """Listar transacoes."""
    # Importacao lazy para evitar ciclo
    from ...db.payments import payments_repo
    from ...payments.models import PaymentStatus
    
    limit = args.get("limit", 10)
    status_str = args.get("status")
    wallet_source = args.get("wallet_source")
    
    # Converter string para enum se fornecido
    status = None
    if status_str:
        try:
            status = PaymentStatus(status_str)
        except ValueError:
            pass
    
    transactions = await payments_repo.list_transactions(
        limit=limit,
        status=status
    )
    
    # Filtrar por wallet_source se especificado
    if wallet_source:
        transactions = [
            t for t in transactions 
            if t.wallet_source.value == wallet_source or t.wallet_source == wallet_source
        ]
    
    return {
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "amount_formatted": f"R$ {t.amount / 100:.2f}",
                "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
                "wallet_source": t.wallet_source.value if hasattr(t.wallet_source, 'value') else str(t.wallet_source),
                "checkout_session_id": t.checkout_session_id,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in transactions
        ],
        "count": len(transactions)
    }


async def get_transaction(args: Dict[str, Any]) -> Dict[str, Any]:
    """Obter detalhes de uma transacao."""
    # Importacao lazy para evitar ciclo
    from ...db.payments import payments_repo
    
    transaction_id = args.get("transaction_id")
    
    if not transaction_id:
        return {"error": "transaction_id is required"}
    
    t = await payments_repo.get_transaction(transaction_id)
    
    if not t:
        return {"error": f"Transaction {transaction_id} not found"}
    
    return {
        "id": t.id,
        "amount": t.amount,
        "amount_formatted": f"R$ {t.amount / 100:.2f}",
        "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
        "wallet_source": t.wallet_source.value if hasattr(t.wallet_source, 'value') else str(t.wallet_source),
        "wallet_token": t.wallet_token[:20] + "..." if t.wallet_token and len(t.wallet_token) > 20 else t.wallet_token,
        "checkout_session_id": t.checkout_session_id,
        "created_at": t.created_at.isoformat() if t.created_at else None
    }
