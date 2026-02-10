"""Repository de Pagamentos PSP.

Gerencia transacoes e carteiras virtuais no banco de dados.
"""
from typing import Optional, List
from datetime import datetime
import uuid
import structlog

from .database import products_db
from ..payments.models import (
    PaymentTransaction,
    PaymentStatus,
    WalletInfo,
    WalletToken,
    WalletSource,
)

logger = structlog.get_logger()


class PaymentsRepository:
    """Repository para transacoes PSP e carteiras."""
    
    async def init_tables(self):
        """Criar tabelas de pagamentos se nao existirem."""
        # Tabela de transacoes PSP
        await products_db.execute("""
            CREATE TABLE IF NOT EXISTS psp_transactions (
                id TEXT PRIMARY KEY,
                checkout_session_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                currency TEXT DEFAULT 'BRL',
                status TEXT DEFAULT 'pending',
                wallet_id TEXT,
                wallet_token TEXT,
                wallet_source TEXT DEFAULT 'unknown',
                mandate_jwt TEXT,
                mandate_valid INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_code TEXT,
                error_message TEXT,
                refunded_amount INTEGER DEFAULT 0,
                refunded_at TIMESTAMP
            )
        """)
        
        # Tabela de carteiras virtuais
        await products_db.execute("""
            CREATE TABLE IF NOT EXISTS virtual_wallets (
                wallet_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                balance INTEGER DEFAULT 50000,
                currency TEXT DEFAULT 'BRL',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de tokens de carteira
        await products_db.execute("""
            CREATE TABLE IF NOT EXISTS wallet_tokens (
                token TEXT PRIMARY KEY,
                wallet_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                used INTEGER DEFAULT 0,
                FOREIGN KEY (wallet_id) REFERENCES virtual_wallets(wallet_id)
            )
        """)
        
        # Criar carteira padrao se nao existir
        await self._ensure_default_wallet()
        
        logger.info("Payment tables initialized")
    
    async def _ensure_default_wallet(self):
        """Garantir que existe uma carteira padrao."""
        existing = await self.get_wallet("default_wallet")
        if not existing:
            await self.create_wallet(
                wallet_id="default_wallet",
                user_id="user_agent",
                initial_balance=50000  # R$ 500,00
            )
            logger.info("Default wallet created with R$ 500,00")
    
    # =========================================================================
    # Transacoes
    # =========================================================================
    
    async def create_transaction(
        self,
        checkout_session_id: str,
        amount: int,
        currency: str = "BRL",
        wallet_id: Optional[str] = None,
        wallet_token: Optional[str] = None,
        mandate_jwt: Optional[str] = None,
        wallet_source: WalletSource = WalletSource.UNKNOWN
    ) -> PaymentTransaction:
        """Criar nova transacao de pagamento."""
        txn_id = f"psp_txn_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        await products_db.execute(
            """
            INSERT INTO psp_transactions 
            (id, checkout_session_id, amount, currency, status, wallet_id, 
             wallet_token, wallet_source, mandate_jwt, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (txn_id, checkout_session_id, amount, currency, PaymentStatus.PENDING.value,
             wallet_id, wallet_token, wallet_source.value, mandate_jwt, now)
        )
        
        logger.info("Transaction created", txn_id=txn_id, amount=amount, wallet_source=wallet_source.value)
        return await self.get_transaction(txn_id)
    
    async def get_transaction(self, txn_id: str) -> Optional[PaymentTransaction]:
        """Buscar transacao por ID."""
        row = await products_db.fetch_one(
            "SELECT * FROM psp_transactions WHERE id = ?",
            (txn_id,)
        )
        if not row:
            return None
        return self._row_to_transaction(row)
    
    async def get_transaction_by_checkout(self, checkout_session_id: str) -> Optional[PaymentTransaction]:
        """Buscar transacao por checkout session."""
        row = await products_db.fetch_one(
            "SELECT * FROM psp_transactions WHERE checkout_session_id = ?",
            (checkout_session_id,)
        )
        if not row:
            return None
        return self._row_to_transaction(row)
    
    async def list_transactions(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[PaymentStatus] = None
    ) -> List[PaymentTransaction]:
        """Listar transacoes."""
        if status:
            rows = await products_db.fetch_all(
                """SELECT * FROM psp_transactions 
                   WHERE status = ? 
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (status.value, limit, offset)
            )
        else:
            rows = await products_db.fetch_all(
                """SELECT * FROM psp_transactions 
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (limit, offset)
            )
        return [self._row_to_transaction(row) for row in rows]
    
    async def update_transaction_status(
        self,
        txn_id: str,
        status: PaymentStatus,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        mandate_valid: bool = False
    ) -> bool:
        """Atualizar status da transacao."""
        now = datetime.utcnow()
        
        updates = ["status = ?", "mandate_valid = ?"]
        params = [status.value, 1 if mandate_valid else 0]
        
        if status == PaymentStatus.PROCESSING:
            updates.append("processing_at = ?")
            params.append(now)
        elif status == PaymentStatus.COMPLETED:
            updates.append("completed_at = ?")
            params.append(now)
        
        if error_code:
            updates.append("error_code = ?")
            params.append(error_code)
        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)
        
        params.append(txn_id)
        
        await products_db.execute(
            f"UPDATE psp_transactions SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        
        logger.info("Transaction status updated", txn_id=txn_id, status=status.value)
        return True
    
    async def refund_transaction(
        self,
        txn_id: str,
        amount: int
    ) -> bool:
        """Registrar estorno na transacao."""
        now = datetime.utcnow()
        
        await products_db.execute(
            """UPDATE psp_transactions 
               SET refunded_amount = refunded_amount + ?, 
                   refunded_at = ?,
                   status = CASE 
                       WHEN refunded_amount + ? >= amount THEN ?
                       ELSE ?
                   END
               WHERE id = ?""",
            (amount, now, amount, PaymentStatus.REFUNDED.value, 
             PaymentStatus.PARTIALLY_REFUNDED.value, txn_id)
        )
        
        logger.info("Transaction refunded", txn_id=txn_id, amount=amount)
        return True
    
    def _row_to_transaction(self, row) -> PaymentTransaction:
        """Converter row do banco para PaymentTransaction."""
        data = dict(row)
        data["status"] = PaymentStatus(data["status"])
        data["mandate_valid"] = bool(data.get("mandate_valid", 0))
        # Converter wallet_source para enum, com fallback para UNKNOWN
        if data.get("wallet_source"):
            try:
                data["wallet_source"] = WalletSource(data["wallet_source"])
            except ValueError:
                data["wallet_source"] = WalletSource.UNKNOWN
        else:
            data["wallet_source"] = WalletSource.UNKNOWN
        return PaymentTransaction(**data)
    
    # =========================================================================
    # Carteiras
    # =========================================================================
    
    async def create_wallet(
        self,
        wallet_id: str,
        user_id: str,
        initial_balance: int = 50000,
        currency: str = "BRL"
    ) -> WalletInfo:
        """Criar nova carteira virtual."""
        now = datetime.utcnow()
        
        await products_db.execute(
            """
            INSERT INTO virtual_wallets (wallet_id, user_id, balance, currency, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (wallet_id, user_id, initial_balance, currency, now, now)
        )
        
        logger.info("Wallet created", wallet_id=wallet_id, balance=initial_balance)
        return await self.get_wallet(wallet_id)
    
    async def get_wallet(self, wallet_id: str) -> Optional[WalletInfo]:
        """Buscar carteira por ID."""
        row = await products_db.fetch_one(
            "SELECT * FROM virtual_wallets WHERE wallet_id = ?",
            (wallet_id,)
        )
        if not row:
            return None
        return WalletInfo(**dict(row))
    
    async def get_wallet_by_token(self, token: str) -> Optional[WalletInfo]:
        """Buscar carteira pelo token."""
        row = await products_db.fetch_one(
            """SELECT w.* FROM virtual_wallets w
               JOIN wallet_tokens t ON w.wallet_id = t.wallet_id
               WHERE t.token = ? AND t.used = 0""",
            (token,)
        )
        if not row:
            return None
        return WalletInfo(**dict(row))
    
    async def update_wallet_balance(
        self,
        wallet_id: str,
        amount: int
    ) -> Optional[WalletInfo]:
        """Atualizar saldo da carteira (positivo = credito, negativo = debito)."""
        now = datetime.utcnow()
        
        await products_db.execute(
            """UPDATE virtual_wallets 
               SET balance = balance + ?, updated_at = ?
               WHERE wallet_id = ?""",
            (amount, now, wallet_id)
        )
        
        wallet = await self.get_wallet(wallet_id)
        logger.info("Wallet balance updated", 
                    wallet_id=wallet_id, 
                    change=amount, 
                    new_balance=wallet.balance if wallet else None)
        return wallet
    
    async def debit_wallet(self, wallet_id: str, amount: int) -> Optional[WalletInfo]:
        """Debitar valor da carteira."""
        wallet = await self.get_wallet(wallet_id)
        if not wallet or wallet.balance < amount:
            return None
        return await self.update_wallet_balance(wallet_id, -amount)
    
    async def credit_wallet(self, wallet_id: str, amount: int) -> Optional[WalletInfo]:
        """Creditar valor na carteira."""
        return await self.update_wallet_balance(wallet_id, amount)
    
    async def get_wallet_balance(self, wallet_id: str) -> int:
        """Obter apenas o saldo da carteira."""
        wallet = await self.get_wallet(wallet_id)
        return wallet.balance if wallet else 0
    
    # =========================================================================
    # Tokens
    # =========================================================================
    
    async def create_wallet_token(
        self,
        wallet_id: str,
        user_id: str = "user_agent"
    ) -> WalletToken:
        """Criar token de carteira."""
        token = WalletToken.generate(wallet_id, user_id)
        
        await products_db.execute(
            """
            INSERT INTO wallet_tokens (token, wallet_id, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (token.token, token.wallet_id, token.user_id, token.created_at, token.expires_at)
        )
        
        logger.info("Wallet token created", token=token.token[:10] + "...", wallet_id=wallet_id)
        return token
    
    async def validate_token(self, token: str) -> Optional[WalletInfo]:
        """Validar token e retornar carteira associada."""
        return await self.get_wallet_by_token(token)
    
    async def mark_token_used(self, token: str) -> bool:
        """Marcar token como usado."""
        await products_db.execute(
            "UPDATE wallet_tokens SET used = 1 WHERE token = ?",
            (token,)
        )
        return True


# Instancia global
payments_repo = PaymentsRepository()
