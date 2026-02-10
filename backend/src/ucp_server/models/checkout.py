"""Modelos de Checkout UCP."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Item(BaseModel):
    """Item em uma linha do checkout."""
    id: str
    title: str
    price: Optional[int] = None


class Total(BaseModel):
    """Total calculado."""
    type: str  # 'subtotal', 'discount', 'shipping', 'total'
    amount: int


class LineItem(BaseModel):
    """Linha do checkout."""
    id: Optional[str] = None
    item: Item
    quantity: int
    totals: List[Total] = []


class Buyer(BaseModel):
    """Comprador."""
    full_name: str
    email: str
    phone: Optional[str] = None


class Allocation(BaseModel):
    """Alocacao de desconto."""
    path: str
    amount: int


class AppliedDiscount(BaseModel):
    """Desconto aplicado."""
    code: str
    title: str
    amount: int
    automatic: bool = False
    allocations: List[Allocation] = []


class Discounts(BaseModel):
    """Descontos do checkout."""
    codes: List[str] = []
    applied: List[AppliedDiscount] = []


class UcpCapability(BaseModel):
    """Capability UCP."""
    name: str
    version: str


class UcpMeta(BaseModel):
    """Metadados UCP."""
    version: str = "2026-01-11"
    capabilities: List[UcpCapability] = []


class CheckoutSession(BaseModel):
    """Sessao de checkout UCP."""
    ucp: Optional[UcpMeta] = None
    id: str
    line_items: List[LineItem]
    buyer: Buyer
    status: str = "draft"  # 'draft', 'ready_for_complete', 'completed', 'cancelled'
    currency: str = "BRL"
    totals: List[Total] = []
    links: List[dict] = []
    payment: Optional[dict] = None
    discounts: Discounts = Discounts()
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CheckoutCreate(BaseModel):
    """Request para criar checkout."""
    line_items: List[LineItem]
    buyer: Buyer
    currency: str = "BRL"
    payment: Optional[dict] = None


class CheckoutUpdate(BaseModel):
    """Request para atualizar checkout."""
    id: str
    line_items: Optional[List[LineItem]] = None
    discounts: Optional[Discounts] = None
    payment: Optional[dict] = None


class CheckoutComplete(BaseModel):
    """Request para completar checkout."""
    payment: dict
