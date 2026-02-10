"""Models do UCP Server."""
from .book import Book, BookCreate
from .checkout import CheckoutSession, LineItem, Buyer, Total, Item
from .payment import PaymentHandler, Payment

# Adapters para SDK oficial
from .adapters import (
    is_sdk_available,
    local_checkout_to_sdk,
    sdk_checkout_to_local,
    local_buyer_to_sdk,
    sdk_buyer_to_local,
    create_ucp_meta,
)

# Modelos do SDK oficial (se disponível)
try:
    from ucp_sdk.models.schemas.shopping.checkout_resp import CheckoutResponse
    from ucp_sdk.models.schemas.shopping.types.buyer import Buyer as SdkBuyer
    from ucp_sdk.models.schemas.shopping.types.line_item_resp import LineItemResponse
    SDK_MODELS_AVAILABLE = True
except ImportError:
    CheckoutResponse = None
    SdkBuyer = None
    LineItemResponse = None
    SDK_MODELS_AVAILABLE = False

__all__ = [
    # Modelos locais
    "Book", "BookCreate",
    "CheckoutSession", "LineItem", "Buyer", "Total", "Item",
    "PaymentHandler", "Payment",
    # Adapters
    "is_sdk_available",
    "local_checkout_to_sdk",
    "sdk_checkout_to_local",
    "local_buyer_to_sdk",
    "sdk_buyer_to_local",
    "create_ucp_meta",
    # SDK (se disponível)
    "CheckoutResponse",
    "SdkBuyer",
    "LineItemResponse",
    "SDK_MODELS_AVAILABLE",
]
