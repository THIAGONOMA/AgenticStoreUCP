"""Repository de cupons de desconto."""
from typing import Optional, List
from datetime import datetime

from .database import products_db


class DiscountCode:
    """Cupom de desconto."""
    def __init__(
        self,
        code: str,
        title: str,
        type: str,  # 'percentage' ou 'fixed'
        value: int,
        min_purchase: int = 0,
        max_uses: Optional[int] = None,
        current_uses: int = 0,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
        active: bool = True,
    ):
        self.code = code
        self.title = title
        self.type = type
        self.value = value
        self.min_purchase = min_purchase
        self.max_uses = max_uses
        self.current_uses = current_uses
        self.valid_from = valid_from
        self.valid_until = valid_until
        self.active = active
    
    def is_valid(self, subtotal: int) -> bool:
        """Verificar se cupom e valido."""
        if not self.active:
            return False
        
        if subtotal < self.min_purchase:
            return False
        
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        
        now = datetime.utcnow()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        
        return True
    
    def calculate_discount(self, subtotal: int) -> int:
        """Calcular valor do desconto."""
        if self.type == "percentage":
            return int(subtotal * self.value / 100)
        else:  # fixed
            return min(self.value, subtotal)


class DiscountsRepository:
    """Repository para cupons de desconto."""
    
    async def get_by_code(self, code: str) -> Optional[DiscountCode]:
        """Buscar cupom por codigo."""
        row = await products_db.fetch_one(
            "SELECT * FROM discount_codes WHERE code = ?",
            (code.upper(),)
        )
        if row:
            return DiscountCode(**dict(row))
        return None
    
    async def create(self, discount: DiscountCode) -> DiscountCode:
        """Criar novo cupom."""
        await products_db.execute(
            """
            INSERT INTO discount_codes (code, title, type, value, min_purchase, max_uses, current_uses, valid_from, valid_until, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                discount.code.upper(),
                discount.title,
                discount.type,
                discount.value,
                discount.min_purchase,
                discount.max_uses,
                discount.current_uses,
                discount.valid_from,
                discount.valid_until,
                1 if discount.active else 0,
            )
        )
        return discount
    
    async def increment_usage(self, code: str) -> bool:
        """Incrementar uso do cupom."""
        await products_db.execute(
            "UPDATE discount_codes SET current_uses = current_uses + 1 WHERE code = ?",
            (code.upper(),)
        )
        return True
    
    async def get_all_active(self) -> List[DiscountCode]:
        """Listar cupons ativos."""
        rows = await products_db.fetch_all(
            "SELECT * FROM discount_codes WHERE active = 1"
        )
        return [DiscountCode(**dict(row)) for row in rows]
    
    async def validate_and_calculate(self, code: str, cart_total: int) -> tuple[bool, any]:
        """
        Validar cupom e calcular desconto.
        
        Args:
            code: Codigo do cupom
            cart_total: Total do carrinho em centavos
            
        Returns:
            Tuple (is_valid, discount_amount_or_error)
        """
        discount = await self.get_by_code(code)
        
        if not discount:
            return False, "Cupom não encontrado"
        
        if not discount.is_valid(cart_total):
            if not discount.active:
                return False, "Cupom inativo"
            if cart_total < discount.min_purchase:
                return False, f"Valor mínimo: R$ {discount.min_purchase / 100:.2f}"
            if discount.max_uses and discount.current_uses >= discount.max_uses:
                return False, "Cupom esgotado"
            return False, "Cupom inválido"
        
        discount_amount = discount.calculate_discount(cart_total)
        return True, discount_amount


# Instancia global
discounts_repo = DiscountsRepository()
