"""
Adapters para compatibilidade entre modelos customizados e SDK oficial do UCP.

Este módulo fornece funções para converter entre os modelos customizados
e os modelos do SDK oficial (ucp_sdk).
"""

from typing import Optional, List
from datetime import datetime

# Modelos customizados (atuais)
from .checkout import (
    CheckoutSession as LocalCheckoutSession,
    LineItem as LocalLineItem,
    Item as LocalItem,
    Total as LocalTotal,
    Buyer as LocalBuyer,
    Discounts as LocalDiscounts,
    AppliedDiscount as LocalAppliedDiscount,
    UcpMeta as LocalUcpMeta,
    UcpCapability as LocalUcpCapability,
)

# SDK oficial
try:
    from ucp_sdk.models.schemas.shopping.checkout_resp import CheckoutResponse
    from ucp_sdk.models.schemas.shopping.checkout_create_req import CheckoutCreateRequest
    from ucp_sdk.models.schemas.shopping.types.line_item_resp import LineItemResponse
    from ucp_sdk.models.schemas.shopping.types.line_item_create_req import LineItemCreateRequest
    from ucp_sdk.models.schemas.shopping.types.item_resp import ItemResponse
    from ucp_sdk.models.schemas.shopping.types.item_create_req import ItemCreateRequest
    from ucp_sdk.models.schemas.shopping.types.total_resp import TotalResponse
    from ucp_sdk.models.schemas.shopping.types.buyer import Buyer as SdkBuyer
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    CheckoutResponse = None
    LineItemResponse = None
    ItemResponse = None
    TotalResponse = None
    SdkBuyer = None


def is_sdk_available() -> bool:
    """Verifica se o SDK oficial está disponível."""
    return SDK_AVAILABLE


# =============================================================================
# Conversores: Local -> SDK
# =============================================================================

def local_buyer_to_sdk(buyer: LocalBuyer) -> Optional[dict]:
    """Converte Buyer local para formato SDK."""
    if not SDK_AVAILABLE:
        return None
    
    return {
        "full_name": buyer.full_name,
        "email": buyer.email,
        "phone_number": buyer.phone,  # SDK usa phone_number
    }


def local_item_to_sdk(item: LocalItem) -> dict:
    """Converte Item local para formato SDK."""
    return {
        "id": item.id,
        "title": item.title,
        "unit_price": item.price,
    }


def local_total_to_sdk(total: LocalTotal) -> dict:
    """Converte Total local para formato SDK."""
    return {
        "type": total.type,
        "amount": total.amount,
    }


def local_line_item_to_sdk(line_item: LocalLineItem) -> dict:
    """Converte LineItem local para formato SDK."""
    return {
        "id": line_item.id or "",
        "item": local_item_to_sdk(line_item.item),
        "quantity": line_item.quantity,
        "totals": [local_total_to_sdk(t) for t in line_item.totals],
    }


def local_checkout_to_sdk(checkout: LocalCheckoutSession) -> dict:
    """Converte CheckoutSession local para formato SDK."""
    # Mapear status local para SDK
    status_map = {
        "draft": "incomplete",
        "ready_for_complete": "ready_for_complete",
        "completed": "completed",
        "cancelled": "canceled",
    }
    
    return {
        "id": checkout.id,
        "line_items": [local_line_item_to_sdk(li) for li in checkout.line_items],
        "buyer": local_buyer_to_sdk(checkout.buyer) if checkout.buyer else None,
        "status": status_map.get(checkout.status, "incomplete"),
        "currency": checkout.currency,
        "totals": [local_total_to_sdk(t) for t in checkout.totals],
        "links": checkout.links,
    }


# =============================================================================
# Conversores: SDK -> Local
# =============================================================================

def sdk_buyer_to_local(buyer_data: dict) -> LocalBuyer:
    """Converte Buyer SDK para formato local."""
    full_name = buyer_data.get("full_name")
    if not full_name:
        first = buyer_data.get("first_name", "")
        last = buyer_data.get("last_name", "")
        full_name = f"{first} {last}".strip() or "Unknown"
    
    return LocalBuyer(
        full_name=full_name,
        email=buyer_data.get("email", ""),
        phone=buyer_data.get("phone_number"),  # SDK usa phone_number
    )


def sdk_item_to_local(item_data: dict) -> LocalItem:
    """Converte Item SDK para formato local."""
    return LocalItem(
        id=item_data.get("id", ""),
        title=item_data.get("title", ""),
        price=item_data.get("unit_price"),
    )


def sdk_total_to_local(total_data: dict) -> LocalTotal:
    """Converte Total SDK para formato local."""
    return LocalTotal(
        type=total_data.get("type", "total"),
        amount=total_data.get("amount", 0),
    )


def sdk_line_item_to_local(line_item_data: dict) -> LocalLineItem:
    """Converte LineItem SDK para formato local."""
    return LocalLineItem(
        id=line_item_data.get("id"),
        item=sdk_item_to_local(line_item_data.get("item", {})),
        quantity=line_item_data.get("quantity", 1),
        totals=[sdk_total_to_local(t) for t in line_item_data.get("totals", [])],
    )


def sdk_checkout_to_local(checkout_data: dict) -> LocalCheckoutSession:
    """Converte CheckoutResponse SDK para CheckoutSession local."""
    # Mapear status SDK para local
    status_map = {
        "incomplete": "draft",
        "requires_escalation": "draft",
        "ready_for_complete": "ready_for_complete",
        "complete_in_progress": "ready_for_complete",
        "completed": "completed",
        "canceled": "cancelled",
    }
    
    buyer_data = checkout_data.get("buyer")
    buyer = sdk_buyer_to_local(buyer_data) if buyer_data else LocalBuyer(
        full_name="Unknown",
        email="unknown@example.com"
    )
    
    return LocalCheckoutSession(
        id=checkout_data.get("id", ""),
        line_items=[sdk_line_item_to_local(li) for li in checkout_data.get("line_items", [])],
        buyer=buyer,
        status=status_map.get(checkout_data.get("status", "incomplete"), "draft"),
        currency=checkout_data.get("currency", "BRL"),
        totals=[sdk_total_to_local(t) for t in checkout_data.get("totals", [])],
        links=checkout_data.get("links", []),
        payment=checkout_data.get("payment"),
    )


# =============================================================================
# Helpers
# =============================================================================

def create_ucp_meta(version: str = "2026-01-11", capabilities: List[str] = None) -> LocalUcpMeta:
    """Cria UcpMeta com capabilities padrão."""
    caps = capabilities or ["dev.ucp.shopping.checkout", "dev.ucp.shopping.discount"]
    return LocalUcpMeta(
        version=version,
        capabilities=[LocalUcpCapability(name=c, version="1.0") for c in caps]
    )
