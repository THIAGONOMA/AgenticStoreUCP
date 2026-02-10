"""Repository de transacoes (checkout sessions)."""
from typing import Optional, List
from datetime import datetime
import uuid
import structlog

from .database import transactions_db, products_db
from ..ucp_server.models.checkout import (
    CheckoutSession, LineItem, Buyer, Total, Item,
    Discounts, AppliedDiscount, Allocation, UcpMeta, UcpCapability
)

logger = structlog.get_logger()


class TransactionsRepository:
    """Repository para checkout sessions."""
    
    async def create_buyer(self, buyer: Buyer) -> str:
        """Criar ou obter buyer."""
        # Verificar se ja existe
        row = await transactions_db.fetch_one(
            "SELECT id FROM buyers WHERE email = ?",
            (buyer.email,)
        )
        if row:
            return row["id"]
        
        # Criar novo
        buyer_id = f"buyer_{uuid.uuid4().hex[:8]}"
        await transactions_db.execute(
            """
            INSERT INTO buyers (id, full_name, email, phone)
            VALUES (?, ?, ?, ?)
            """,
            (buyer_id, buyer.full_name, buyer.email, buyer.phone)
        )
        return buyer_id
    
    async def create_session(
        self,
        line_items: List[LineItem],
        buyer: Buyer,
        currency: str = "BRL"
    ) -> CheckoutSession:
        """Criar nova sessao de checkout."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        buyer_id = await self.create_buyer(buyer)
        now = datetime.utcnow()
        
        # Calcular subtotal
        subtotal = sum(
            (item.item.price or 0) * item.quantity 
            for item in line_items
        )
        
        # Criar sessao
        await transactions_db.execute(
            """
            INSERT INTO checkout_sessions (id, buyer_id, status, currency, subtotal, total, created_at, updated_at)
            VALUES (?, ?, 'ready_for_complete', ?, ?, ?, ?, ?)
            """,
            (session_id, buyer_id, currency, subtotal, subtotal, now, now)
        )
        
        # Criar line items
        for item in line_items:
            item_id = f"li_{uuid.uuid4().hex[:8]}"
            item_subtotal = (item.item.price or 0) * item.quantity
            await transactions_db.execute(
                """
                INSERT INTO line_items (id, session_id, book_id, quantity, unit_price, subtotal, total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    session_id,
                    item.item.id,
                    item.quantity,
                    item.item.price or 0,
                    item_subtotal,
                    item_subtotal,
                )
            )
        
        return await self.get_session(session_id)
    
    async def get_session(self, session_id: str) -> Optional[CheckoutSession]:
        """Obter sessao por ID."""
        row = await transactions_db.fetch_one(
            """
            SELECT cs.*, b.full_name, b.email, b.phone
            FROM checkout_sessions cs
            JOIN buyers b ON cs.buyer_id = b.id
            WHERE cs.id = ?
            """,
            (session_id,)
        )
        if not row:
            return None
        
        row_dict = dict(row)
        
        # Buscar line items
        items_rows = await transactions_db.fetch_all(
            "SELECT * FROM line_items WHERE session_id = ?",
            (session_id,)
        )
        
        line_items = []
        for item_row in items_rows:
            item_dict = dict(item_row)
            line_items.append(LineItem(
                id=item_dict["id"],
                item=Item(
                    id=item_dict["book_id"],
                    title=item_dict["book_id"],  # Simplificado
                    price=item_dict["unit_price"],
                ),
                quantity=item_dict["quantity"],
                totals=[
                    Total(type="subtotal", amount=item_dict["subtotal"]),
                    Total(type="total", amount=item_dict["total"]),
                ],
            ))
        
        # Buscar descontos aplicados
        discount_rows = await transactions_db.fetch_all(
            "SELECT * FROM applied_discounts WHERE session_id = ?",
            (session_id,)
        )
        
        applied_discounts = []
        discount_codes = []
        for d_row in discount_rows:
            d_dict = dict(d_row)
            discount_codes.append(d_dict["code"])
            applied_discounts.append(AppliedDiscount(
                code=d_dict["code"],
                title=d_dict["title"],
                amount=d_dict["amount"],
                automatic=bool(d_dict["automatic"]),
                allocations=[Allocation(path=d_dict["allocation_path"] or "subtotal", amount=d_dict["amount"])],
            ))
        
        # Montar totais
        totals = [
            Total(type="subtotal", amount=row_dict["subtotal"]),
        ]
        if row_dict["discount_total"] > 0:
            totals.append(Total(type="discount", amount=row_dict["discount_total"]))
        if row_dict["shipping_total"] > 0:
            totals.append(Total(type="shipping", amount=row_dict["shipping_total"]))
        totals.append(Total(type="total", amount=row_dict["total"]))
        
        return CheckoutSession(
            ucp=UcpMeta(
                version="2026-01-11",
                capabilities=[
                    UcpCapability(name="dev.ucp.shopping.checkout", version="2026-01-11")
                ]
            ),
            id=session_id,
            line_items=line_items,
            buyer=Buyer(
                full_name=row_dict["full_name"],
                email=row_dict["email"],
                phone=row_dict["phone"],
            ),
            status=row_dict["status"],
            currency=row_dict["currency"],
            totals=totals,
            discounts=Discounts(codes=discount_codes, applied=applied_discounts),
        )
    
    async def apply_discount(
        self,
        session_id: str,
        code: str,
        title: str,
        amount: int
    ) -> bool:
        """Aplicar desconto a uma sessao."""
        discount_id = f"disc_{uuid.uuid4().hex[:8]}"
        
        await transactions_db.execute(
            """
            INSERT INTO applied_discounts (id, session_id, code, title, amount, allocation_path)
            VALUES (?, ?, ?, ?, ?, 'subtotal')
            """,
            (discount_id, session_id, code, title, amount)
        )
        
        # Atualizar totais da sessao
        row = await transactions_db.fetch_one(
            "SELECT subtotal, discount_total FROM checkout_sessions WHERE id = ?",
            (session_id,)
        )
        if row:
            new_discount_total = row["discount_total"] + amount
            new_total = row["subtotal"] - new_discount_total
            await transactions_db.execute(
                """
                UPDATE checkout_sessions 
                SET discount_total = ?, total = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_discount_total, new_total, datetime.utcnow(), session_id)
            )
        
        return True
    
    async def complete_session(self, session_id: str) -> bool:
        """Marcar sessao como completa.
        
        Nota: A baixa de estoque é feita em checkout.py ANTES de chamar este metodo.
        """
        # Marcar sessão como completa
        now = datetime.utcnow()
        await transactions_db.execute(
            """
            UPDATE checkout_sessions 
            SET status = 'completed', completed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (now, now, session_id)
        )
        logger.info("Session marked as completed", session_id=session_id)
        return True
    
    async def cancel_session(self, session_id: str) -> bool:
        """Cancelar sessao."""
        await transactions_db.execute(
            "UPDATE checkout_sessions SET status = 'cancelled', updated_at = ? WHERE id = ?",
            (datetime.utcnow(), session_id)
        )
        return True


# Instancia global
transactions_repo = TransactionsRepository()
