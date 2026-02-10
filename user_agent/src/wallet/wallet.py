"""Carteira Virtual do User Agent.

Gerencia saldo, historico de transacoes e tokens de pagamento.
"""
import json
import uuid
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import structlog

logger = structlog.get_logger()


@dataclass
class WalletTransaction:
    """Transacao local da carteira."""
    id: str
    type: str  # debit, credit, refund
    amount: int
    description: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    psp_transaction_id: Optional[str] = None
    checkout_session_id: Optional[str] = None
    balance_after: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionario."""
        return {
            "id": self.id,
            "type": self.type,
            "amount": self.amount,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "psp_transaction_id": self.psp_transaction_id,
            "checkout_session_id": self.checkout_session_id,
            "balance_after": self.balance_after
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletTransaction":
        """Criar de dicionario."""
        data = data.copy()
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class WalletToken:
    """Token para pagamento."""
    token: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    used: bool = False
    checkout_session_id: Optional[str] = None


class VirtualWallet:
    """
    Carteira Virtual do User Agent.
    
    Gerencia:
    - Saldo em centavos
    - Historico de transacoes
    - Tokens de pagamento
    """
    
    def __init__(
        self,
        wallet_id: str = "user_agent_wallet",
        initial_balance: int = 50000,  # R$ 500,00
        currency: str = "BRL",
        data_dir: Optional[str] = None
    ):
        """
        Inicializar carteira.
        
        Args:
            wallet_id: ID unico da carteira
            initial_balance: Saldo inicial em centavos
            currency: Moeda
            data_dir: Diretorio para persistencia
        """
        self.wallet_id = wallet_id
        self.currency = currency
        self._balance = initial_balance
        self._transactions: List[WalletTransaction] = []
        self._tokens: Dict[str, WalletToken] = {}
        
        # Diretorio de dados
        if data_dir:
            self._data_dir = Path(data_dir)
        else:
            self._data_dir = Path.home() / ".user_agent" / "wallet"
        
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._data_file = self._data_dir / f"{wallet_id}.json"
        
        # Carregar dados persistidos
        self._load()
        
        logger.info(
            "Wallet initialized",
            wallet_id=wallet_id,
            balance=self._balance,
            currency=currency
        )
    
    @property
    def balance(self) -> int:
        """Saldo em centavos."""
        return self._balance
    
    @property
    def balance_formatted(self) -> str:
        """Saldo formatado."""
        return f"R$ {self._balance / 100:.2f}"
    
    @property
    def transactions(self) -> List[WalletTransaction]:
        """Historico de transacoes."""
        return self._transactions.copy()
    
    def can_pay(self, amount: int) -> bool:
        """Verificar se pode pagar valor."""
        return self._balance >= amount
    
    def generate_payment_token(
        self,
        checkout_session_id: Optional[str] = None
    ) -> str:
        """
        Gerar token para pagamento.
        
        Returns:
            Token unico para usar no PSP
        """
        token = f"wtk_{uuid.uuid4().hex[:16]}"
        self._tokens[token] = WalletToken(
            token=token,
            checkout_session_id=checkout_session_id
        )
        
        logger.info("Payment token generated", token=token[:15] + "...")
        self._save()
        
        return token
    
    def validate_token(self, token: str) -> bool:
        """
        Validar se um token existe e nao foi usado.
        
        Args:
            token: Token a validar
            
        Returns:
            True se token valido e nao usado
        """
        if token not in self._tokens:
            logger.warning("Token not found", token=token[:15] + "...")
            return False
        
        wallet_token = self._tokens[token]
        if wallet_token.used:
            logger.warning("Token already used", token=token[:15] + "...")
            return False
        
        return True
    
    def use_token(self, token: str) -> bool:
        """
        Marcar token como usado.
        
        Args:
            token: Token a marcar
            
        Returns:
            True se marcado com sucesso
        """
        if token in self._tokens:
            self._tokens[token].used = True
            self._save()
            logger.info("Token marked as used", token=token[:15] + "...")
            return True
        return False
    
    def debit(
        self,
        amount: int,
        description: str,
        psp_transaction_id: Optional[str] = None,
        checkout_session_id: Optional[str] = None
    ) -> Optional[WalletTransaction]:
        """
        Debitar valor da carteira.
        
        Args:
            amount: Valor em centavos
            description: Descricao da transacao
            psp_transaction_id: ID da transacao no PSP
            checkout_session_id: ID da sessao de checkout
            
        Returns:
            Transacao registrada ou None se saldo insuficiente
        """
        if not self.can_pay(amount):
            logger.warning(
                "Insufficient balance for debit",
                balance=self._balance,
                required=amount
            )
            return None
        
        self._balance -= amount
        
        txn = WalletTransaction(
            id=f"wtxn_{uuid.uuid4().hex[:8]}",
            type="debit",
            amount=amount,
            description=description,
            psp_transaction_id=psp_transaction_id,
            checkout_session_id=checkout_session_id,
            balance_after=self._balance
        )
        
        self._transactions.append(txn)
        self._save()
        
        logger.info(
            "Wallet debited",
            amount=amount,
            balance_after=self._balance,
            transaction_id=txn.id
        )
        
        return txn
    
    def credit(
        self,
        amount: int,
        description: str,
        psp_transaction_id: Optional[str] = None
    ) -> WalletTransaction:
        """
        Creditar valor na carteira.
        
        Args:
            amount: Valor em centavos
            description: Descricao
            psp_transaction_id: ID da transacao de estorno
            
        Returns:
            Transacao registrada
        """
        self._balance += amount
        
        txn = WalletTransaction(
            id=f"wtxn_{uuid.uuid4().hex[:8]}",
            type="credit",
            amount=amount,
            description=description,
            psp_transaction_id=psp_transaction_id,
            balance_after=self._balance
        )
        
        self._transactions.append(txn)
        self._save()
        
        logger.info(
            "Wallet credited",
            amount=amount,
            balance_after=self._balance,
            transaction_id=txn.id
        )
        
        return txn
    
    def add_funds(self, amount: int = 10000, description: Optional[str] = None) -> WalletTransaction:
        """Adicionar fundos (para demo)."""
        return self.credit(
            amount=amount,
            description=description or f"Deposito de R$ {amount / 100:.2f}"
        )
    
    def get_recent_transactions(self, limit: int = 10) -> List[WalletTransaction]:
        """Obter transacoes recentes."""
        return sorted(
            self._transactions,
            key=lambda t: t.timestamp,
            reverse=True
        )[:limit]
    
    def get_info(self) -> Dict[str, Any]:
        """Obter informacoes da carteira."""
        return {
            "wallet_id": self.wallet_id,
            "balance": self._balance,
            "balance_formatted": self.balance_formatted,
            "currency": self.currency,
            "transactions_count": len(self._transactions),
            "recent_transactions": [
                t.to_dict() for t in self.get_recent_transactions(5)
            ]
        }
    
    def _save(self):
        """Persistir dados."""
        data = {
            "wallet_id": self.wallet_id,
            "balance": self._balance,
            "currency": self.currency,
            "transactions": [t.to_dict() for t in self._transactions],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with open(self._data_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        """Carregar dados persistidos."""
        if not self._data_file.exists():
            logger.debug("No wallet data file, using defaults")
            return
        
        try:
            with open(self._data_file, "r") as f:
                data = json.load(f)
            
            self._balance = data.get("balance", self._balance)
            self._transactions = [
                WalletTransaction.from_dict(t)
                for t in data.get("transactions", [])
            ]
            
            logger.info(
                "Wallet data loaded",
                balance=self._balance,
                transactions=len(self._transactions)
            )
        except Exception as e:
            logger.warning("Failed to load wallet data", error=str(e))


# Instancia global (singleton)
_wallet_instance: Optional[VirtualWallet] = None


def get_wallet() -> VirtualWallet:
    """Obter instancia da carteira (singleton)."""
    global _wallet_instance
    if _wallet_instance is None:
        _wallet_instance = VirtualWallet()
    return _wallet_instance
