"""Shopping Node - Carrinho e checkout conversacional."""
from typing import Dict, Any, List, Optional
import structlog
import httpx
import os

from ..state import UserAgentState, CartItem, Message, AP2MandateInfo
from ..llm import generate_response, is_llm_enabled
from ...clients import UCPClient
from ...security import get_ap2_client
from ...wallet import get_wallet

logger = structlog.get_logger()

# URL da API do User Agent para tokens
USER_AGENT_API_URL = os.environ.get("USER_AGENT_API_URL", "http://localhost:8001")


async def generate_wallet_token_via_api() -> Optional[str]:
    """Gerar token via API do User Agent (garante que a instância correta conhece o token)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{USER_AGENT_API_URL}/wallet/token")
            if response.status_code == 200:
                data = response.json()
                return data.get("token")
            else:
                logger.warning("Failed to generate token via API", status=response.status_code)
    except httpx.ConnectError:
        logger.warning("User Agent API not available, using local wallet")
    except Exception as e:
        logger.error("Error generating token via API", error=str(e))
    return None


async def shopping_node(state: UserAgentState) -> Dict[str, Any]:
    """
    Shopping Node - Gerenciar carrinho e compras.
    
    Responsavel por:
    - Adicionar/remover itens (multi-loja)
    - Aplicar cupons de desconto
    - Criar checkouts via UCP
    - Executar pagamentos com AP2 (3 mandatos)
    """
    logger.info("Shopping node processing", session=state["session_id"])
    
    messages = []
    cart_items = list(state.get("cart_items", []))
    cart_total = state.get("cart_total", 0)
    applied_discount = state.get("applied_discount")
    discount_amount = state.get("discount_amount", 0)
    ap2_mandate = state.get("ap2_mandate")
    
    intent = state.get("current_intent", "view_cart")
    params = state.get("intent_params", {})
    
    # Pegar ultima mensagem
    user_messages = [m for m in state["messages"] if m["role"] == "user"]
    last_message = user_messages[-1]["content"].lower() if user_messages else ""
    
    result = {}
    
    if intent == "add_to_cart":
        # Adicionar item ao carrinho
        result = await _add_to_cart(params, state, cart_items)
        cart_items = result["cart_items"]
        cart_total = result["cart_total"]
        response = result["message"]
        
    elif intent == "remove_from_cart":
        # Remover item
        result = _remove_from_cart(params, cart_items)
        cart_items = result["cart_items"]
        cart_total = result["cart_total"]
        response = result["message"]
        
    elif intent == "apply_discount":
        # Aplicar cupom
        result = await _apply_discount(params, state, cart_items, cart_total)
        applied_discount = result.get("applied_discount")
        discount_amount = result.get("discount_amount", 0)
        cart_total = result.get("cart_total", cart_total)
        response = result["message"]
        
    elif intent == "execute_checkout":
        # Confirmado pelo usuario - executar compra diretamente
        if not cart_items:
            response = "Seu carrinho esta vazio! Busque e adicione produtos primeiro."
        else:
            result = await _execute_purchase(state, cart_items, discount_amount)
            response = result["message"]
            ap2_mandate = result.get("ap2_mandate")
            
            if result.get("success"):
                cart_items = []
                cart_total = 0
                applied_discount = None
                discount_amount = 0
    
    elif intent in ["checkout", "buy"]:
        # Primeira vez - pedir confirmacao
        if not cart_items:
            response = "Seu carrinho esta vazio! Busque e adicione produtos primeiro."
        else:
            response = await _prepare_checkout(cart_items, cart_total, discount_amount)
            
            messages.append(Message(role="assistant", content=response, metadata=None))
            return {
                "messages": messages,
                "cart_items": cart_items,
                "cart_total": cart_total,
                "waiting_for_confirmation": True,
                "confirmation_context": {
                    "confirm_intent": "execute_checkout",
                    "next_action": "shopping",
                    "params": {"cart_items": cart_items}
                },
                "next_action": None
            }
    
    elif intent == "view_cart":
        # Mostrar carrinho
        response = _format_cart(cart_items, cart_total, applied_discount, discount_amount)
        
    else:
        # Intent nao reconhecido - mostrar carrinho
        response = _format_cart(cart_items, cart_total, applied_discount, discount_amount)
    
    messages.append(Message(role="assistant", content=response, metadata=None))
    
    return {
        "messages": messages,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "applied_discount": applied_discount,
        "discount_amount": discount_amount,
        "ap2_mandate": ap2_mandate,
        "waiting_for_confirmation": False,
        "confirmation_context": None,
        "next_action": None
    }


async def _add_to_cart(
    params: Dict[str, Any],
    state: UserAgentState,
    cart_items: List[CartItem]
) -> Dict[str, Any]:
    """Adicionar item ao carrinho."""
    item_number = params.get("item_number")
    search_results = state.get("search_results", [])
    
    # Converter item_number para int se necessário
    if isinstance(item_number, str):
        try:
            item_number = int(item_number)
        except ValueError:
            item_number = None
    
    if item_number and search_results:
        idx = item_number - 1
        if 0 <= idx < len(search_results):
            item = search_results[idx]
            
            # Verificar se ja existe
            existing_idx = next(
                (i for i, c in enumerate(cart_items) 
                 if c["product_id"] == item.get("id") and c["store_url"] == item.get("store_url")),
                None
            )
            
            if existing_idx is not None:
                cart_items[existing_idx]["quantity"] += 1
            else:
                cart_items.append(CartItem(
                    store_url=item.get("store_url", state.get("active_store_url", "")),
                    product_id=item.get("id", ""),
                    title=item.get("title", "Produto"),
                    price=item.get("price", 0),
                    quantity=1
                ))
            
            cart_total = sum(c["price"] * c["quantity"] for c in cart_items)
            
            return {
                "cart_items": cart_items,
                "cart_total": cart_total,
                "message": (
                    f"Adicionado: **{item.get('title', 'Produto')}**\n"
                    f"Preco: R$ {item.get('price', 0) / 100:.2f}\n\n"
                    f"Total do carrinho: R$ {cart_total / 100:.2f}\n\n"
                    f"Diga `carrinho` para ver ou `comprar` para finalizar."
                )
            }
        else:
            return {
                "cart_items": cart_items,
                "cart_total": sum(c["price"] * c["quantity"] for c in cart_items),
                "message": f"Item {item_number} nao encontrado. Escolha entre 1 e {len(search_results)}."
            }
    
    return {
        "cart_items": cart_items,
        "cart_total": sum(c["price"] * c["quantity"] for c in cart_items),
        "message": "Nao encontrei o item. Busque primeiro e diga `adicionar [numero]`."
    }


def _remove_from_cart(params: Dict[str, Any], cart_items: List[CartItem]) -> Dict[str, Any]:
    """Remover item do carrinho."""
    item_number = params.get("item_number")
    
    if item_number and cart_items:
        idx = item_number - 1
        if 0 <= idx < len(cart_items):
            removed = cart_items.pop(idx)
            cart_total = sum(c["price"] * c["quantity"] for c in cart_items)
            
            return {
                "cart_items": cart_items,
                "cart_total": cart_total,
                "message": f"Removido: **{removed['title']}**\n\nTotal: R$ {cart_total / 100:.2f}"
            }
    
    return {
        "cart_items": cart_items,
        "cart_total": sum(c["price"] * c["quantity"] for c in cart_items),
        "message": "Diga `remover [numero]` para remover um item do carrinho."
    }


async def _apply_discount(
    params: Dict[str, Any],
    state: UserAgentState,
    cart_items: List[CartItem],
    cart_total: int
) -> Dict[str, Any]:
    """Aplicar cupom de desconto."""
    code = params.get("code", "").upper()
    
    if not code:
        return {
            "message": "Diga `cupom CODIGO` para aplicar um desconto."
        }
    
    if not cart_items:
        return {
            "message": "Adicione itens ao carrinho antes de aplicar um cupom."
        }
    
    # Tentar aplicar via UCP na primeira loja
    active_store = state.get("active_store_url")
    if not active_store and cart_items:
        active_store = cart_items[0]["store_url"]
    
    if active_store:
        try:
            async with UCPClient(active_store) as client:
                await client.discover()
                
                # Criar checkout temporario para verificar cupom
                line_items = [
                    {
                        "item": {"id": i["product_id"], "title": i["title"]},
                        "quantity": i["quantity"]
                    }
                    for i in cart_items if i["store_url"] == active_store
                ]
                
                session = await client.create_checkout(
                    line_items,
                    {"full_name": "Teste", "email": "test@test.com"}
                )
                
                if session:
                    updated = await client.apply_discount(session.id, code)
                    
                    if updated and updated.total < session.total:
                        discount = session.total - updated.total
                        return {
                            "applied_discount": code,
                            "discount_amount": discount,
                            "cart_total": cart_total - discount,
                            "message": (
                                f"Cupom **{code}** aplicado!\n"
                                f"Desconto: -R$ {discount / 100:.2f}\n"
                                f"Novo total: R$ {(cart_total - discount) / 100:.2f}"
                            )
                        }
        except Exception as e:
            logger.error("Failed to apply discount", code=code, error=str(e))
    
    return {
        "message": f"Cupom **{code}** nao encontrado ou invalido."
    }


async def _prepare_checkout(
    cart_items: List[CartItem],
    cart_total: int,
    discount_amount: int
) -> str:
    """Preparar mensagem de confirmacao de checkout."""
    lines = ["**Resumo do Pedido:**\n"]
    
    # Agrupar por loja
    stores = {}
    for item in cart_items:
        if item["store_url"] not in stores:
            stores[item["store_url"]] = []
        stores[item["store_url"]].append(item)
    
    for store_url, items in stores.items():
        lines.append(f"\n**Loja:** {store_url}\n")
        for item in items:
            item_total = item["price"] * item["quantity"]
            lines.append(f"- {item['title']} x{item['quantity']} = R$ {item_total / 100:.2f}")
    
    lines.append("")
    
    if discount_amount > 0:
        lines.append(f"Subtotal: R$ {(cart_total + discount_amount) / 100:.2f}")
        lines.append(f"Desconto: -R$ {discount_amount / 100:.2f}")
    
    lines.append(f"**Total: R$ {cart_total / 100:.2f}**\n")
    lines.append("Confirmar compra? (sim/nao)")
    
    return "\n".join(lines)


async def _execute_purchase(
    state: UserAgentState,
    cart_items: List[CartItem],
    discount_amount: int
) -> Dict[str, Any]:
    """Executar compra com AP2 via UCP usando carteira virtual."""
    if not cart_items:
        return {"success": False, "message": "Carrinho vazio!"}
    
    # Obter carteira virtual
    wallet = get_wallet()
    
    # Calcular total do carrinho
    cart_total = sum(item["price"] * item["quantity"] for item in cart_items)
    final_total = cart_total - discount_amount
    
    # Verificar saldo na carteira
    if not wallet.can_pay(final_total):
        return {
            "success": False,
            "message": (
                f"**Saldo insuficiente na carteira!**\n\n"
                f"Valor da compra: R$ {final_total / 100:.2f}\n"
                f"Saldo disponivel: {wallet.balance_formatted}\n\n"
                f"Adicione fundos a sua carteira para continuar."
            )
        }
    
    logger.info(
        "Wallet balance check passed",
        required=final_total,
        available=wallet.balance
    )
    
    # Agrupar por loja
    stores = {}
    for item in cart_items:
        if item["store_url"] not in stores:
            stores[item["store_url"]] = []
        stores[item["store_url"]].append(item)
    
    results = []
    ap2_client = get_ap2_client()
    ap2_mandate_info = None
    total_spent = 0
    
    for store_url, items in stores.items():
        try:
            async with UCPClient(store_url) as client:
                await client.discover()
                
                # Criar checkout UCP
                line_items = [
                    {
                        "item": {"id": i["product_id"], "title": i["title"]},
                        "quantity": i["quantity"]
                    }
                    for i in items
                ]
                
                buyer_info = {
                    "full_name": state.get("user_name", "Usuario"),
                    "email": state.get("user_email", f"{state['session_id'][:8]}@user-agent.local")
                }
                
                session = await client.create_checkout(line_items, buyer_info)
                
                if session:
                    # Aplicar desconto se houver
                    if state.get("applied_discount"):
                        await client.apply_discount(session.id, state["applied_discount"])
                    
                    # Gerar mandatos AP2
                    mandate = ap2_client.create_mandate_for_checkout(
                        checkout_total=session.total,
                        currency=session.currency,
                        store_id=store_url
                    )
                    
                    ap2_mandate_info = AP2MandateInfo(
                        intent_mandate_id=None,
                        cart_mandate_id=session.id,
                        cart_mandate_jwt=None,
                        payment_mandate_id=mandate.key_id,
                        payment_mandate_jwt=mandate.jwt,
                        total_authorized=mandate.max_amount,
                        currency=mandate.currency
                    )
                    
                    # Gerar token da carteira via API (garante sincronização)
                    wallet_token = await generate_wallet_token_via_api()
                    
                    if not wallet_token:
                        # Fallback para instância local se API não disponível
                        wallet_token = wallet.generate_payment_token(
                            checkout_session_id=session.id
                        )
                        logger.info(
                            "Wallet token generated locally",
                            session_id=session.id,
                            token=wallet_token[:15] + "..."
                        )
                    else:
                        logger.info(
                            "Wallet token generated via API",
                            session_id=session.id,
                            token=wallet_token[:15] + "..."
                        )
                    
                    # Completar pagamento com wallet_token
                    result = await client.complete_checkout(
                        session_id=session.id,
                        payment_token=wallet_token,  # Token usado como identificador
                        mandate_jwt=mandate.jwt,
                        wallet_token=wallet_token  # Token da carteira virtual
                    )
                    
                    if result.get("status") == "completed":
                        # PSP já debitou via API do User Agent, apenas registrar
                        store_total = session.total
                        total_spent += store_total
                        
                        logger.info(
                            "Payment processed via PSP",
                            store=store_url,
                            total=store_total,
                            psp_transaction_id=result.get("psp_transaction_id")
                        )
                        
                        results.append({
                            "store": store_url,
                            "order_id": result.get("order_id", result.get("id", session.id)),
                            "total": store_total,
                            "psp_transaction_id": result.get("psp_transaction_id"),
                            "success": True
                        })
                        logger.info(
                            "Purchase completed",
                            store=store_url,
                            order=result.get("order_id"),
                            wallet_balance=wallet.balance
                        )
                    else:
                        error = result.get("error", result.get("detail", "Erro desconhecido"))
                        results.append({
                            "store": store_url,
                            "error": error,
                            "success": False
                        })
        
        except Exception as e:
            logger.error("Purchase failed", store=store_url, error=str(e))
            results.append({
                "store": store_url,
                "error": str(e),
                "success": False
            })
    
    # Formatar resultado
    success_count = sum(1 for r in results if r.get("success"))
    
    if success_count == len(results):
        lines = ["**Compra realizada com sucesso!**\n"]
        for r in results:
            lines.append(f"- **{r['store']}**")
            lines.append(f"  Pedido: #{r['order_id']}")
            lines.append(f"  Total: R$ {r['total'] / 100:.2f}")
            if r.get("psp_transaction_id"):
                lines.append(f"  Transacao PSP: {r['psp_transaction_id']}")
        
        lines.append(f"\n**Carteira Virtual**")
        lines.append(f"Total gasto: R$ {total_spent / 100:.2f}")
        lines.append(f"Saldo restante: {wallet.balance_formatted}")
        lines.append("\nObrigado pela compra!")
        
        return {
            "success": True, 
            "message": "\n".join(lines),
            "ap2_mandate": ap2_mandate_info,
            "wallet_balance": wallet.balance,
            "total_spent": total_spent
        }
    
    elif success_count > 0:
        lines = ["**Algumas compras falharam:**\n"]
        for r in results:
            if r.get("success"):
                lines.append(f"- {r['store']} - Pedido #{r['order_id']}")
            else:
                lines.append(f"- {r['store']} - Erro: {r.get('error')}")
        
        return {
            "success": True, 
            "message": "\n".join(lines),
            "ap2_mandate": ap2_mandate_info
        }
    
    else:
        lines = ["**Falha na compra:**\n"]
        for r in results:
            lines.append(f"- {r['store']}: {r.get('error')}")
        
        lines.append("\nTente novamente ou verifique a conexao com a loja.")
        
        return {"success": False, "message": "\n".join(lines)}


def _format_cart(
    cart_items: List[CartItem], 
    cart_total: int,
    applied_discount: str = None,
    discount_amount: int = 0
) -> str:
    """Formatar carrinho."""
    if not cart_items:
        return (
            "**Seu carrinho esta vazio.**\n\n"
            "Busque produtos e diga `adicionar [numero]` para comecar."
        )
    
    lines = ["**Seu Carrinho:**\n"]
    
    # Agrupar por loja
    current_store = None
    for i, item in enumerate(cart_items, 1):
        if item["store_url"] != current_store:
            current_store = item["store_url"]
            lines.append(f"\n*{current_store}*")
        
        item_total = item["price"] * item["quantity"]
        lines.append(
            f"{i}. **{item['title']}**\n"
            f"   {item['quantity']}x R$ {item['price'] / 100:.2f} = R$ {item_total / 100:.2f}"
        )
    
    lines.append("")
    
    subtotal = cart_total + discount_amount
    if applied_discount and discount_amount > 0:
        lines.append(f"Subtotal: R$ {subtotal / 100:.2f}")
        lines.append(f"Cupom {applied_discount}: -R$ {discount_amount / 100:.2f}")
    
    lines.append(f"**Total: R$ {cart_total / 100:.2f}**\n")
    lines.append("Comandos: `remover [n]` | `cupom CODIGO` | `comprar`")
    
    return "\n".join(lines)
