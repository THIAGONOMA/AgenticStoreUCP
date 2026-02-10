"""MCP Tools - Carrinho e descontos."""
from typing import Any, Dict
from mcp.types import Tool

from ...db.products import products_repo
from ...db.discounts import discounts_repo


def get_cart_tools() -> list[Tool]:
    """Retorna ferramentas de carrinho."""
    return [
        Tool(
            name="check_discount_code",
            description="Verificar se um codigo de desconto e valido",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Codigo do cupom de desconto"
                    },
                    "cart_total": {
                        "type": "integer",
                        "description": "Valor total do carrinho em centavos"
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="calculate_cart",
            description="Calcular total do carrinho com desconto",
            inputSchema={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "book_id": {"type": "string"},
                                "quantity": {"type": "integer"}
                            }
                        },
                        "description": "Lista de itens no carrinho"
                    },
                    "discount_code": {
                        "type": "string",
                        "description": "Codigo de desconto (opcional)"
                    }
                },
                "required": ["items"]
            }
        ),
    ]


async def check_discount_code(args: Dict[str, Any]) -> Dict[str, Any]:
    """Verificar codigo de desconto."""
    code = args.get("code", "")
    cart_total = args.get("cart_total", 0)
    
    is_valid, discount_or_error = await discounts_repo.validate_and_calculate(code, cart_total)
    
    if not is_valid:
        return {"valid": False, "error": discount_or_error}
    
    return {
        "valid": True,
        "discount_amount": discount_or_error,
        "discount_formatted": f"R$ {discount_or_error / 100:.2f}"
    }


async def calculate_cart(args: Dict[str, Any]) -> Dict[str, Any]:
    """Calcular carrinho."""
    items = args.get("items", [])
    discount_code = args.get("discount_code")
    
    cart_items = []
    subtotal = 0
    
    for item in items:
        book = await products_repo.get_by_id(item.get("book_id"))
        if book:
            quantity = item.get("quantity", 1)
            item_total = book.price * quantity
            subtotal += item_total
            cart_items.append({
                "book_id": book.id,
                "title": book.title,
                "quantity": quantity,
                "unit_price": book.price,
                "total": item_total
            })
    
    discount = 0
    if discount_code:
        is_valid, discount_or_error = await discounts_repo.validate_and_calculate(discount_code, subtotal)
        if is_valid:
            discount = discount_or_error
    
    total = subtotal - discount
    
    return {
        "items": cart_items,
        "subtotal": subtotal,
        "subtotal_formatted": f"R$ {subtotal / 100:.2f}",
        "discount": discount,
        "discount_formatted": f"R$ {discount / 100:.2f}",
        "total": total,
        "total_formatted": f"R$ {total / 100:.2f}"
    }
