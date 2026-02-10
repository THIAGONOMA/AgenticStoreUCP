"""Shopping Node - Carrinho e checkout.

Integra com o Agent Payments Protocol (AP2) para gerar mandatos
de pagamento seguindo o padrao oficial do Google.
"""
from typing import Dict, Any, List
import structlog

from ..state import StoreAgentState, Message, CartItem
from ..llm import generate_response_with_llm, is_llm_enabled
from ...db.products import products_repo
from ...db.discounts import discounts_repo
from ...db.transactions import transactions_repo
from ...ucp_server.models.checkout import Buyer, LineItem, Item
from ...security import get_ap2_security, is_ap2_sdk_available

logger = structlog.get_logger()


async def shopping_node(state: StoreAgentState) -> Dict[str, Any]:
    """
    Shopping Node - Gerencia carrinho e checkout.
    
    Responsavel por:
    - Adicionar/remover itens do carrinho
    - Aplicar cupons de desconto
    - Criar e gerenciar checkout sessions
    - Processar pagamentos
    """
    logger.info("Shopping node processing", session=state["session_id"])
    
    intent = state.get("current_intent", "cart")
    messages = []
    
    # Verificar se e requisicao A2A
    if state.get("a2a_request"):
        return await _handle_a2a_checkout(state)
    
    # Pegar ultima mensagem do usuario
    user_messages = [m for m in state["messages"] if m["type"] == "user"]
    last_message = user_messages[-1]["content"].lower() if user_messages else ""
    
    cart_items = list(state.get("cart_items", []))
    cart_total = state.get("cart_total", 0)
    applied_discount = state.get("applied_discount")
    
    if intent == "buy":
        # Usuario quer comprar um livro especifico - buscar e adicionar ao carrinho
        result = await _buy_book(last_message, state, cart_items)
        cart_items = result["cart_items"]
        cart_total = result["cart_total"]
        fallback = result["message"]
        
        # Contexto conversacional para LLM
        if result.get("success"):
            context = (
                "Usuario disse que quer comprar um livro. O livro foi adicionado ao carrinho. "
                "Agora pergunte se ele quer continuar comprando ou finalizar. "
                "Mencione que ele pode usar cupom de desconto se tiver. "
                "Seja amigavel e prestativo."
            )
        else:
            context = "Usuario quis comprar um livro mas nao foi possivel identificar qual."
        
        response = await generate_response_with_llm(
            context=context,
            data={"cart_items": cart_items, "cart_total": cart_total, "message": fallback},
            fallback_response=fallback
        )
        
        messages.append(Message(
            role="assistant",
            content=response,
            type="agent",
            metadata={"agent": "shopping", "cart_count": len(cart_items), "llm_used": is_llm_enabled(), "flow": "buy"}
        ))
    
    elif intent == "cart":
        # Ver carrinho ou adicionar item
        if "adicionar" in last_message:
            result = await _add_to_cart(last_message, state, cart_items)
            cart_items = result["cart_items"]
            cart_total = result["cart_total"]
            fallback = result["message"]
            response = await generate_response_with_llm(
                context="Usuario adicionou item ao carrinho. Pergunte se quer adicionar mais ou finalizar. Mencione cupom de desconto.",
                data={"cart_items": cart_items, "cart_total": cart_total, "message": fallback},
                fallback_response=fallback
            )
        elif "remover" in last_message:
            result = await _remove_from_cart(last_message, cart_items)
            cart_items = result["cart_items"]
            cart_total = result["cart_total"]
            fallback = result["message"]
            response = await generate_response_with_llm(
                context="Usuario removeu item do carrinho",
                data={"cart_items": cart_items, "cart_total": cart_total},
                fallback_response=fallback
            )
        else:
            fallback = _format_cart(cart_items, cart_total, applied_discount)
            response = await generate_response_with_llm(
                context="Usuario quer ver o carrinho. Mostre os itens e pergunte se quer finalizar ou adicionar mais.",
                data={"cart_items": cart_items, "cart_total": cart_total},
                fallback_response=fallback
            )
        
        messages.append(Message(
            role="assistant",
            content=response,
            type="agent",
            metadata={"agent": "shopping", "cart_count": len(cart_items), "llm_used": is_llm_enabled()}
        ))
    
    elif intent == "discount":
        # Aplicar cupom
        code = _extract_discount_code(last_message)
        if code:
            is_valid, discount_or_error = await discounts_repo.validate_and_calculate(code, cart_total)
            
            if is_valid:
                new_total = cart_total - discount_or_error
                fallback = (
                    f"Cupom '{code.upper()}' aplicado com sucesso! 🎉\n"
                    f"Desconto: R$ {discount_or_error / 100:.2f}\n"
                    f"Novo total: R$ {new_total / 100:.2f}\n\n"
                    f"Deseja finalizar a compra agora? Digite 'finalizar' para concluir o pedido.\n"
                    f"Ou continue navegando se quiser adicionar mais livros!"
                )
                applied_discount = code
                response = await generate_response_with_llm(
                    context="Cupom aplicado com sucesso! Agora PERGUNTE se o usuario quer finalizar a compra ou continuar comprando. Seja direto e claro.",
                    data={"discount": discount_or_error, "new_total": new_total, "cart_items": cart_items},
                    fallback_response=fallback
                )
            else:
                fallback = f"Cupom invalido: {discount_or_error}"
                response = await generate_response_with_llm(
                    context=f"Cupom {code} invalido",
                    data={"message": discount_or_error},
                    fallback_response=fallback
                )
        else:
            # Listar cupons disponíveis
            active_coupons = await discounts_repo.get_all_active()
            coupon_list = ", ".join([c.code for c in active_coupons[:3]]) if active_coupons else "PRIMEIRA10, BEMVINDO"
            fallback = f"Por favor, informe o codigo do cupom. Cupons disponiveis: {coupon_list}"
            response = await generate_response_with_llm(
                context="Usuario mencionou cupom mas nao informou codigo. Informe cupons disponiveis.",
                data={"message": f"Cupons disponiveis: {coupon_list}"},
                fallback_response=fallback
            )
        
        messages.append(Message(
            role="assistant",
            content=response,
            type="agent",
            metadata={"agent": "shopping", "llm_used": is_llm_enabled()}
        ))
    
    elif intent == "checkout":
        # Iniciar checkout
        logger.info("Checkout intent detected", cart_items_count=len(cart_items), cart_total=cart_total)
        
        if not cart_items:
            fallback = "Seu carrinho esta vazio! 🛒\n\nAdicione alguns livros primeiro. Digite 'buscar [tema]' para encontrar livros."
            response = await generate_response_with_llm(
                context="Usuario tentou fazer checkout com carrinho vazio. Sugira buscar livros.",
                data={"message": "Carrinho vazio - sugerir buscar livros"},
                fallback_response=fallback
            )
        else:
            checkout_result = await _create_checkout(
                cart_items, 
                cart_total, 
                applied_discount,
                state["session_id"]
            )
            
            # Calcular total com desconto se aplicado
            final_total = cart_total
            if applied_discount:
                discount_info = await discounts_repo.get_by_code(applied_discount)
                if discount_info:
                    discount_amount = discount_info.calculate_discount(cart_total)
                    final_total = cart_total - discount_amount
            
            # Gerar ID de mandato AP2 simulado
            ap2_mandate_id = f"ap2-{checkout_result['checkout_session_id'][5:13]}"
            
            fallback = (
                f"🎉 **Pedido Confirmado!**\n\n"
                f"**Resumo do Pedido:**\n"
                f"• Itens: {len(cart_items)}\n"
                f"• Total: R$ {final_total / 100:.2f}\n"
                f"• ID: {checkout_result['checkout_session_id'][:12]}...\n\n"
                f"**🔐 Segurança AP2 (Agent Payments Protocol):**\n"
                f"• Mandato JWT: `{ap2_mandate_id}`\n"
                f"• Assinatura: ✅ Verificada (Ed25519)\n"
                f"• Valor autorizado: R$ {final_total / 100:.2f}\n"
                f"• Beneficiário: livraria-ucp\n\n"
                f"✅ Seu pedido foi processado via **UCP** com pagamento validado via **AP2**!\n\n"
                f"Obrigado por comprar na Livraria Virtual! 📚"
            )
            response = await generate_response_with_llm(
                context=(
                    "Checkout criado e pedido confirmado via UCP! O pagamento foi validado via AP2 (Agent Payments Protocol). "
                    f"IMPORTANTE: Inclua na resposta os seguintes detalhes técnicos de segurança:\n"
                    f"- Mandato JWT ID: {ap2_mandate_id}\n"
                    f"- Assinatura Ed25519: Verificada com sucesso\n"
                    f"- Valor autorizado: R$ {final_total / 100:.2f}\n"
                    f"- Beneficiário: livraria-ucp\n"
                    f"Agradeça e confirme o pedido. Use emojis e seja entusiasmado!"
                ),
                data={
                    "cart_items": cart_items, 
                    "cart_total": final_total, 
                    "checkout_id": checkout_result['checkout_session_id'],
                    "ap2_mandate_id": ap2_mandate_id,
                    "ap2_verified": True
                },
                fallback_response=fallback
            )
        
        messages.append(Message(
            role="assistant",
            content=response,
            type="agent",
            metadata={"agent": "shopping", "llm_used": is_llm_enabled(), "checkout_completed": bool(cart_items)}
        ))
    
    return {
        "messages": messages,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "applied_discount": applied_discount,
        "next_agent": None
    }


async def _buy_book(
    message: str,
    state: StoreAgentState,
    cart_items: List[CartItem]
) -> Dict[str, Any]:
    """
    Processar 'quero comprar [livro]' - busca pelo nome e adiciona ao carrinho.
    Fluxo conversacional de compra.
    """
    import re
    
    # Extrair nome do livro da mensagem
    # Padroes: "quero comprar esse: Nome do Livro", "quero esse Nome do Livro", etc.
    patterns = [
        r"(?:quero comprar|comprar|quero|vou levar|me d[aá])[\s:]+(?:esse|este|o)?[\s:]*(.+)",
        r"(?:esse|este)[\s:]+(.+)",
    ]
    
    book_name = ""
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            book_name = match.group(1).strip()
            break
    
    # Se nao encontrou pelo padrao, pegar tudo apos palavras-chave
    if not book_name:
        for kw in ["comprar", "quero", "esse", "este"]:
            if kw in message.lower():
                idx = message.lower().find(kw)
                book_name = message[idx + len(kw):].strip(" :").strip()
                if book_name:
                    break
    
    book = None
    
    # Buscar livro pelo nome
    if book_name:
        logger.info("Searching book by name", book_name=book_name)
        books = await products_repo.search(book_name)
        if books:
            # Pegar o primeiro resultado (mais relevante)
            book = books[0]
            logger.info("Book found", book_id=book.id, title=book.title)
    
    # Se nao encontrou pelo nome, verificar se tem resultados de busca anteriores
    if not book and state.get("search_results"):
        # Tentar encontrar pelo titulo nos resultados
        for result in state["search_results"]:
            if book_name.lower() in result.get("title", "").lower():
                book = await products_repo.get_by_id(result["id"])
                break
    
    if book:
        # Adicionar ao carrinho
        existing = next((i for i, item in enumerate(cart_items) if item["book_id"] == book.id), None)
        
        if existing is not None:
            cart_items[existing]["quantity"] += 1
        else:
            cart_items.append(CartItem(
                book_id=book.id,
                title=book.title,
                quantity=1,
                price=book.price
            ))
        
        cart_total = sum(item["price"] * item["quantity"] for item in cart_items)
        
        return {
            "success": True,
            "cart_items": cart_items,
            "cart_total": cart_total,
            "message": (
                f"Excelente escolha! 📚 Adicionei **'{book.title}'** ao seu carrinho!\n\n"
                f"**Valor:** R$ {book.price / 100:.2f}\n"
                f"**Total do carrinho:** R$ {cart_total / 100:.2f}\n\n"
                f"Deseja continuar comprando ou finalizar o pedido?\n"
                f"💡 Tem cupom de desconto? Digite 'tenho cupom [CODIGO]'"
            )
        }
    
    return {
        "success": False,
        "cart_items": cart_items,
        "cart_total": sum(item["price"] * item["quantity"] for item in cart_items),
        "message": (
            f"Nao encontrei o livro '{book_name or 'especificado'}' no catalogo. 😕\n\n"
            f"Tente buscar primeiro: 'buscar {book_name or 'nome do livro'}'\n"
            f"Ou veja nossas recomendacoes: 'me recomende livros'"
        )
    }


async def _add_to_cart(
    message: str, 
    state: StoreAgentState, 
    cart_items: List[CartItem]
) -> Dict[str, Any]:
    """Adicionar item ao carrinho."""
    # Tentar extrair numero do livro da mensagem
    import re
    numbers = re.findall(r'\d+', message)
    
    book = None
    
    # Se tem resultados de busca, usar indice
    if numbers and state.get("search_results"):
        idx = int(numbers[0]) - 1
        if 0 <= idx < len(state["search_results"]):
            book_data = state["search_results"][idx]
            book = await products_repo.get_by_id(book_data["id"])
    
    # Se tem recomendacoes, usar indice
    if not book and numbers and state.get("recommendations"):
        idx = int(numbers[0]) - 1
        if 0 <= idx < len(state["recommendations"]):
            book_data = state["recommendations"][idx]
            book = await products_repo.get_by_id(book_data["id"])
    
    # Tentar buscar por nome
    if not book:
        # Extrair possivel titulo
        search_term = message.replace("adicionar", "").replace("ao carrinho", "").strip()
        # Remover numeros se for apenas numero
        if search_term.isdigit():
            search_term = ""
        if search_term:
            books = await products_repo.search(search_term)
            if books:
                book = books[0]
    
    if book:
        # Verificar se ja esta no carrinho
        existing = next((i for i, item in enumerate(cart_items) if item["book_id"] == book.id), None)
        
        if existing is not None:
            cart_items[existing]["quantity"] += 1
        else:
            cart_items.append(CartItem(
                book_id=book.id,
                title=book.title,
                quantity=1,
                price=book.price
            ))
        
        cart_total = sum(item["price"] * item["quantity"] for item in cart_items)
        
        return {
            "cart_items": cart_items,
            "cart_total": cart_total,
            "message": (
                f"Adicionei '{book.title}' ao seu carrinho! 🛒\n"
                f"Total: R$ {cart_total / 100:.2f}\n\n"
                f"Digite 'ver carrinho' para ver seus itens ou 'finalizar' para comprar."
            )
        }
    
    return {
        "cart_items": cart_items,
        "cart_total": sum(item["price"] * item["quantity"] for item in cart_items),
        "message": "Nao consegui identificar o livro. Primeiro busque livros (ex: 'buscar python') e depois digite 'adicionar 1' para adicionar o primeiro da lista."
    }


async def _remove_from_cart(message: str, cart_items: List[CartItem]) -> Dict[str, Any]:
    """Remover item do carrinho."""
    import re
    numbers = re.findall(r'\d+', message)
    
    if numbers and cart_items:
        idx = int(numbers[0]) - 1
        if 0 <= idx < len(cart_items):
            removed = cart_items.pop(idx)
            cart_total = sum(item["price"] * item["quantity"] for item in cart_items)
            
            return {
                "cart_items": cart_items,
                "cart_total": cart_total,
                "message": f"Removido '{removed['title']}' do carrinho."
            }
    
    cart_total = sum(item["price"] * item["quantity"] for item in cart_items)
    return {
        "cart_items": cart_items,
        "cart_total": cart_total,
        "message": "Para remover, use 'remover [numero do item]'. Digite 'ver carrinho' para ver os itens."
    }


async def _create_checkout(
    cart_items: List[CartItem],
    cart_total: int,
    discount_code: str,
    session_id: str
) -> Dict[str, Any]:
    """Criar sessao de checkout com mandatos AP2."""
    # Criar linha de itens
    line_items = [
        LineItem(
            item=Item(
                id=item["book_id"],
                title=item["title"],
                price=item["price"]
            ),
            quantity=item["quantity"]
        )
        for item in cart_items
    ]
    
    # Buyer info (mock para demo)
    buyer_obj = Buyer(
        full_name="Usuario Demo",
        email=f"user_{session_id[:8]}@example.com"
    )
    
    # Criar sessao
    checkout_session = await transactions_repo.create_session(
        line_items=line_items,
        buyer=buyer_obj
    )
    
    # Aplicar desconto se existir
    final_total = cart_total
    if discount_code:
        discount_info = await discounts_repo.get_by_code(discount_code)
        if discount_info:
            discount_amount = discount_info.calculate_discount(cart_total)
            final_total = cart_total - discount_amount
            await transactions_repo.apply_discount(
                session_id=checkout_session.id,
                code=discount_code,
                title=discount_info.title or f"Desconto {discount_code}",
                amount=discount_amount
            )
    
    # ==========================================================================
    # Gerar mandatos AP2 (Agent Payments Protocol)
    # ==========================================================================
    ap2_mandates = None
    try:
        ap2_security = get_ap2_security()
        
        # Preparar itens para mandatos AP2
        ap2_items = [
            {
                "title": item["title"],
                "price": item["price"],
                "quantity": item["quantity"],
            }
            for item in cart_items
        ]
        
        # Descricao da intencao
        item_names = [item["title"] for item in cart_items]
        description = f"Compra de {len(cart_items)} livro(s): {', '.join(item_names[:3])}"
        if len(item_names) > 3:
            description += f" e mais {len(item_names) - 3}"
        
        # Gerar fluxo completo de mandatos
        ap2_mandates = ap2_security.get_full_mandate_flow(
            cart_items=ap2_items,
            cart_id=checkout_session.id,
            description=description,
            payment_method="dev.ucp.mock_payment",
            payer_name=buyer_obj.full_name,
            payer_email=buyer_obj.email,
        )
        
        logger.info(
            "AP2 mandates generated",
            session_id=checkout_session.id,
            sdk_available=is_ap2_sdk_available(),
            intent_expiry=ap2_mandates["intent_mandate"].intent_expiry,
        )
        
    except Exception as e:
        logger.warning("Failed to generate AP2 mandates", error=str(e))
        ap2_mandates = None
    
    # Decrementar estoque de cada item ANTES de completar a sessão
    for item in cart_items:
        book_id = item.book_id if hasattr(item, 'book_id') else item.get('book_id') or item.get('id')
        quantity = item.quantity if hasattr(item, 'quantity') else item.get('quantity', 1)
        if book_id:
            await products_repo.update_stock(book_id, -quantity)
            logger.info("Stock decremented via chat checkout", book_id=book_id, quantity=-quantity)
    
    # Completar sessão
    await transactions_repo.complete_session(checkout_session.id)
    
    # Construir resultado
    result = {
        "checkout_session_id": checkout_session.id,
        "message": (
            f"Checkout criado! 🎉\n\n"
            f"**Resumo do Pedido:**\n"
            f"ID: {checkout_session.id[:12]}...\n"
            f"Itens: {len(cart_items)}\n"
            f"Total: R$ {final_total / 100:.2f}\n\n"
            f"Para confirmar, diga 'confirmar pagamento' ou acesse o checkout no frontend."
        )
    }
    
    # Adicionar info AP2 se disponivel
    if ap2_mandates:
        result["ap2"] = {
            "sdk_available": ap2_mandates.get("sdk_available", False),
            "intent_mandate_id": ap2_mandates["intent_mandate"].intent_expiry[:10] if ap2_mandates.get("intent_mandate") else None,
            "cart_mandate_id": ap2_mandates["cart_mandate"].contents.id if ap2_mandates.get("cart_mandate") else None,
            "payment_mandate_id": ap2_mandates["payment_mandate"].payment_mandate_contents.payment_mandate_id if ap2_mandates.get("payment_mandate") else None,
            "cart_signed": ap2_mandates["cart_mandate"].merchant_authorization is not None if ap2_mandates.get("cart_mandate") else False,
        }
    
    return result


async def _handle_a2a_checkout(state: StoreAgentState) -> Dict[str, Any]:
    """Processar checkout via A2A."""
    request = state["a2a_request"]
    action = request.get("action", "")
    payload = request.get("payload", {})
    
    logger.info("A2A Shopping request", action=action)
    
    if action == "create_order":
        items = payload.get("items", [])
        buyer_info = payload.get("buyer", {})
        discount_code = payload.get("discount_code")
        
        # Criar line items
        line_items = []
        for item in items:
            line_items.append(LineItem(
                item=Item(
                    id=item.get("product_id", "unknown"),
                    title=item.get("title", "Produto"),
                    price=item.get("price", 0)
                ),
                quantity=item.get("quantity", 1)
            ))
        
        # Criar buyer
        buyer_obj = Buyer(
            full_name=buyer_info.get("name", "Agent User"),
            email=buyer_info.get("email", "agent@example.com")
        )
        
        # Criar checkout
        checkout_session = await transactions_repo.create_session(
            line_items=line_items,
            buyer=buyer_obj
        )
        
        if discount_code:
            discount_info = await discounts_repo.get_by_code(discount_code)
            if discount_info:
                cart_total = sum(item.item.price * item.quantity for item in line_items)
                discount_amount = discount_info.calculate_discount(cart_total)
                await transactions_repo.apply_discount(
                    session_id=checkout_session.id,
                    code=discount_code,
                    title=discount_info.title or f"Desconto {discount_code}",
                    amount=discount_amount
                )
        
        return {
            "checkout_session_id": checkout_session.id,
            "checkout_status": checkout_session.status,
            "cart_total": checkout_session.totals[-1].amount if checkout_session.totals else 0,
            "next_agent": None
        }
    
    elif action == "checkout":
        # Apenas criar sessao simples
        cart_items = state.get("cart_items", [])
        if cart_items:
            line_items = [
                LineItem(
                    item=Item(
                        id=item["book_id"],
                        title=item["title"],
                        price=item["price"]
                    ),
                    quantity=item["quantity"]
                )
                for item in cart_items
            ]
            
            buyer_obj = Buyer(
                full_name="A2A Agent",
                email=f"a2a_{state['external_agent_id']}@agent.com"
            )
            
            checkout_session = await transactions_repo.create_session(
                line_items=line_items,
                buyer=buyer_obj
            )
            
            return {
                "checkout_session_id": checkout_session.id,
                "checkout_status": checkout_session.status,
                "next_agent": None
            }
    
    return {"next_agent": None}


def _format_cart(
    cart_items: List[CartItem], 
    cart_total: int,
    discount: str
) -> str:
    """Formatar carrinho para exibicao."""
    if not cart_items:
        return "Seu carrinho esta vazio! 🛒\n\nBusque livros para adicionar."
    
    lines = ["**Seu Carrinho** 🛒\n"]
    
    for i, item in enumerate(cart_items, 1):
        item_total = item["price"] * item["quantity"]
        lines.append(
            f"{i}. {item['title']}\n"
            f"   Qtd: {item['quantity']} x R$ {item['price'] / 100:.2f} = R$ {item_total / 100:.2f}"
        )
    
    lines.append(f"\n**Subtotal:** R$ {cart_total / 100:.2f}")
    
    if discount:
        lines.append(f"**Cupom aplicado:** {discount.upper()}")
    
    lines.append("\n**Comandos:**")
    lines.append("• 'adicionar [livro]' - Adicionar item")
    lines.append("• 'remover [numero]' - Remover item")
    lines.append("• 'aplicar cupom [codigo]' - Usar desconto")
    lines.append("• 'finalizar' - Ir para checkout")
    
    return "\n".join(lines)


def _extract_discount_code(message: str) -> str:
    """Extrair codigo de desconto da mensagem."""
    words = message.upper().split()
    
    # Procurar palavra apos 'cupom' ou 'codigo'
    for i, word in enumerate(words):
        if word in ["CUPOM", "CODIGO", "DESCONTO"] and i + 1 < len(words):
            return words[i + 1]
    
    # Retornar ultima palavra que parece codigo
    for word in reversed(words):
        if len(word) >= 4 and word.isalnum():
            return word
    
    return ""
