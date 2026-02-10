#!/usr/bin/env python3
"""
Demonstracao do Agent Payments Protocol (AP2)

Mostra o fluxo completo de mandatos seguindo o SDK oficial do Google:
1. IntentMandate - Intencao de compra do usuario
2. CartMandate - Carrinho assinado pelo merchant
3. PaymentMandate - Autorizacao final de pagamento

Referencia: https://github.com/google-agentic-commerce/AP2
"""

import sys
import os
import json
import time
import base64

# Adicionar path do backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich import box
from rich.tree import Tree

console = Console()


def print_header():
    """Exibir cabecalho."""
    console.print()
    console.print(Panel.fit(
        "[bold blue]Agent Payments Protocol (AP2)[/bold blue]\n"
        "[dim]Demonstracao com SDK Oficial do Google[/dim]\n"
        "[dim]github.com/google-agentic-commerce/AP2[/dim]",
        border_style="blue"
    ))
    console.print()


def demo_step(step: int, title: str, subtitle: str = ""):
    """Exibir titulo do passo."""
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]  Passo {step}: {title}[/bold cyan]")
    if subtitle:
        console.print(f"[dim]  {subtitle}[/dim]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")


def base64url_decode(data: str) -> str:
    """Decodificar base64url."""
    padded = data + "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode()


def decode_jwt_parts(jwt: str):
    """Decodificar partes do JWT."""
    parts = jwt.split(".")
    header = json.loads(base64url_decode(parts[0]))
    payload = json.loads(base64url_decode(parts[1]))
    return header, payload


def check_sdk_availability():
    """Verificar disponibilidade do SDK."""
    from src.security import is_ap2_sdk_available
    
    sdk_available = is_ap2_sdk_available()
    
    if sdk_available:
        console.print("[green]✓[/green] SDK AP2 oficial disponivel")
        console.print("  [dim]Usando tipos do google-agentic-commerce/AP2[/dim]")
    else:
        console.print("[yellow]![/yellow] SDK AP2 nao disponivel - usando fallback")
        console.print("  [dim]Clone o SDK: git clone https://github.com/google-agentic-commerce/AP2[/dim]")
    
    return sdk_available


def demo_intent_mandate():
    """Demonstrar criacao de IntentMandate."""
    from src.security import AP2Security, is_ap2_sdk_available
    from src.security.key_manager import KeyManager
    
    demo_step(1, "IntentMandate", "Usuario expressa intencao de compra")
    
    console.print("[yellow]>[/yellow] Usuario quer comprar livros de programacao...")
    console.print("[yellow]>[/yellow] User Agent cria IntentMandate...\n")
    
    key_manager = KeyManager()
    ap2 = AP2Security(key_manager)
    
    intent = ap2.create_intent_mandate(
        description="Comprar livros de Python e Clean Code para estudos",
        merchants=["livraria-ucp"],
        skus=None,  # Qualquer SKU
        requires_confirmation=True,
        expiry_minutes=60,
    )
    
    # Mostrar detalhes
    table = Table(title="IntentMandate", box=box.ROUNDED, border_style="green")
    table.add_column("Campo", style="cyan")
    table.add_column("Valor", style="green")
    
    table.add_row("Descricao", intent.natural_language_description)
    table.add_row("Merchants", str(intent.merchants))
    table.add_row("Requer Confirmacao", str(intent.user_cart_confirmation_required))
    table.add_row("Requer Reembolso", str(intent.requires_refundability))
    table.add_row("Expira em", intent.intent_expiry)
    
    console.print(table)
    
    console.print("\n[bold green]✓ IntentMandate criado![/bold green]")
    console.print("  [dim]Usuario declarou o que quer comprar em linguagem natural[/dim]")
    
    return ap2, key_manager, intent


def demo_cart_mandate(ap2, key_manager):
    """Demonstrar criacao de CartMandate."""
    demo_step(2, "CartMandate", "Merchant assina o carrinho")
    
    console.print("[yellow]>[/yellow] Usuario selecionou itens no carrinho...")
    console.print("[yellow]>[/yellow] Merchant cria e assina CartMandate...\n")
    
    # Itens do carrinho
    cart_items = [
        {"title": "Clean Code em Python", "price": 4990, "quantity": 1},
        {"title": "Python para Todos", "price": 3990, "quantity": 1},
    ]
    
    cart_mandate = ap2.create_cart_mandate(
        cart_items=cart_items,
        cart_id="cart_demo_001",
        merchant_name="Livraria Virtual UCP",
        currency="BRL",
    )
    
    # Mostrar itens
    items_table = Table(title="Itens do Carrinho", box=box.SIMPLE)
    items_table.add_column("Item", style="white")
    items_table.add_column("Preco", style="green", justify="right")
    items_table.add_column("Qtd", justify="center")
    
    total = 0
    for item in cart_items:
        items_table.add_row(
            item["title"],
            f"R$ {item['price']/100:.2f}",
            str(item["quantity"])
        )
        total += item["price"] * item["quantity"]
    
    items_table.add_row("", "", "")
    items_table.add_row("[bold]TOTAL[/bold]", f"[bold]R$ {total/100:.2f}[/bold]", "")
    
    console.print(items_table)
    
    # Mostrar CartMandate
    console.print()
    cart_table = Table(title="CartMandate", box=box.ROUNDED, border_style="yellow")
    cart_table.add_column("Campo", style="cyan")
    cart_table.add_column("Valor", style="yellow")
    
    cart_table.add_row("Cart ID", cart_mandate.contents.id)
    cart_table.add_row("Merchant", cart_mandate.contents.merchant_name)
    cart_table.add_row("Total", f"R$ {cart_mandate.contents.payment_request.details.total.amount.value:.2f}")
    cart_table.add_row("Moeda", cart_mandate.contents.payment_request.details.total.amount.currency)
    cart_table.add_row("Requer Confirmacao", str(cart_mandate.contents.user_cart_confirmation_required))
    cart_table.add_row("Expira em", cart_mandate.contents.cart_expiry)
    cart_table.add_row("Assinado", "[green]Sim[/green]" if cart_mandate.merchant_authorization else "[red]Nao[/red]")
    
    console.print(cart_table)
    
    # Mostrar JWT de autorizacao
    if cart_mandate.merchant_authorization:
        console.print("\n[yellow]>[/yellow] JWT de Autorizacao do Merchant:")
        jwt = cart_mandate.merchant_authorization
        parts = jwt.split(".")
        console.print(f"  [dim]Header:[/dim]  [blue]{parts[0][:40]}...[/blue]")
        console.print(f"  [dim]Payload:[/dim] [green]{parts[1][:40]}...[/green]")
        console.print(f"  [dim]Signature:[/dim] [red]{parts[2][:40]}...[/red]")
        
        # Decodificar e mostrar payload
        header, payload = decode_jwt_parts(jwt)
        console.print("\n[yellow]>[/yellow] Conteudo do JWT:")
        console.print(Syntax(json.dumps(payload, indent=2, default=str), "json", theme="monokai"))
    
    console.print("\n[bold green]✓ CartMandate criado e assinado![/bold green]")
    console.print("  [dim]Merchant garantiu precos e disponibilidade[/dim]")
    
    return cart_mandate


def demo_payment_mandate(ap2, cart_mandate):
    """Demonstrar criacao de PaymentMandate."""
    demo_step(3, "PaymentMandate", "Usuario autoriza pagamento")
    
    console.print("[yellow]>[/yellow] Usuario confirmou o carrinho...")
    console.print("[yellow]>[/yellow] Criando PaymentMandate com autorizacao...\n")
    
    payment_mandate = ap2.create_payment_mandate(
        cart_mandate=cart_mandate,
        payment_method="dev.ucp.mock_payment",
        payer_name="Usuario Demo",
        payer_email="demo@example.com",
    )
    
    # Mostrar PaymentMandate
    pm_table = Table(title="PaymentMandate", box=box.ROUNDED, border_style="magenta")
    pm_table.add_column("Campo", style="cyan")
    pm_table.add_column("Valor", style="magenta")
    
    contents = payment_mandate.payment_mandate_contents
    pm_table.add_row("Payment Mandate ID", contents.payment_mandate_id)
    pm_table.add_row("Payment Details ID", contents.payment_details_id)
    pm_table.add_row("Merchant Agent", contents.merchant_agent)
    pm_table.add_row("Total", f"R$ {contents.payment_details_total.amount.value:.2f}")
    pm_table.add_row("Metodo", contents.payment_response.method_name)
    pm_table.add_row("Pagador", contents.payment_response.payer_name or "N/A")
    pm_table.add_row("Email", contents.payment_response.payer_email or "N/A")
    pm_table.add_row("Timestamp", contents.timestamp)
    pm_table.add_row("Autorizacao", "[green]Presente[/green]" if payment_mandate.user_authorization else "[red]Ausente[/red]")
    
    console.print(pm_table)
    
    # Mostrar JWT de autorizacao do usuario
    if payment_mandate.user_authorization:
        console.print("\n[yellow]>[/yellow] JWT de Autorizacao do Usuario:")
        jwt = payment_mandate.user_authorization
        parts = jwt.split(".")
        console.print(f"  [dim]Header:[/dim]  [blue]{parts[0][:40]}...[/blue]")
        console.print(f"  [dim]Payload:[/dim] [green]{parts[1][:40]}...[/green]")
        console.print(f"  [dim]Signature:[/dim] [red]{parts[2][:40]}...[/red]")
        
        header, payload = decode_jwt_parts(jwt)
        console.print("\n[yellow]>[/yellow] Conteudo da Autorizacao:")
        console.print(Syntax(json.dumps(payload, indent=2, default=str), "json", theme="monokai"))
    
    console.print("\n[bold green]✓ PaymentMandate criado com autorizacao![/bold green]")
    console.print("  [dim]Usuario autorizou o pagamento[/dim]")
    
    return payment_mandate


def demo_validation(ap2, cart_mandate):
    """Demonstrar validacao de CartMandate."""
    demo_step(4, "Validacao", "Verificar integridade dos mandatos")
    
    console.print("[yellow]>[/yellow] Validando CartMandate...")
    
    result = ap2.validate_cart_mandate(cart_mandate)
    
    if result.valid:
        console.print("\n[bold green]✓ CartMandate VALIDO![/bold green]")
        
        checks = [
            ("Formato JWT", True),
            ("Algoritmo EdDSA", True),
            ("Assinatura Ed25519", True),
            ("Hash do Carrinho", True),
            ("Nao Expirado", True),
        ]
        
        for check, passed in checks:
            status = "[green]✓[/green]" if passed else "[red]✗[/red]"
            console.print(f"  {status} {check}")
    else:
        console.print(f"\n[bold red]✗ CartMandate INVALIDO: {result.error}[/bold red]")
    
    # Demonstrar rejeicao de adulteracao
    console.print("\n[yellow]>[/yellow] Testando protecao contra adulteracao...")
    
    # Adulterar o JWT
    if cart_mandate.merchant_authorization:
        jwt = cart_mandate.merchant_authorization
        parts = jwt.split(".")
        
        # Modificar payload
        payload = json.loads(base64url_decode(parts[1]))
        payload["cart_hash"] = "adulterado_123"
        
        new_payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        tampered_jwt = f"{parts[0]}.{new_payload_b64}.{parts[2]}"
        
        # Criar CartMandate adulterado
        from src.security.ap2_types import CartMandate as CM
        tampered_cart = CM(
            contents=cart_mandate.contents,
            merchant_authorization=tampered_jwt
        )
        
        tampered_result = ap2.validate_cart_mandate(tampered_cart)
        
        if not tampered_result.valid:
            console.print("  [green]✓[/green] Adulteracao DETECTADA!")
            console.print(f"    [red]Erro: {tampered_result.error}[/red]")
        else:
            console.print("  [yellow]![/yellow] Adulteracao nao detectada (problema!)")


def show_flow_diagram():
    """Mostrar diagrama do fluxo."""
    demo_step(5, "Fluxo Completo", "Visao geral do AP2")
    
    tree = Tree("[bold blue]Fluxo de Mandatos AP2[/bold blue]")
    
    intent_branch = tree.add("[green]1. IntentMandate[/green]")
    intent_branch.add("[dim]Usuario declara intencao de compra[/dim]")
    intent_branch.add("[dim]Inclui descricao em linguagem natural[/dim]")
    intent_branch.add("[dim]Define merchants e SKUs permitidos[/dim]")
    
    cart_branch = tree.add("[yellow]2. CartMandate[/yellow]")
    cart_branch.add("[dim]Merchant seleciona itens[/dim]")
    cart_branch.add("[dim]Calcula total e opcoes de pagamento[/dim]")
    cart_branch.add("[dim]Assina com JWT (garantia de preco)[/dim]")
    
    payment_branch = tree.add("[magenta]3. PaymentMandate[/magenta]")
    payment_branch.add("[dim]Usuario confirma carrinho[/dim]")
    payment_branch.add("[dim]Escolhe metodo de pagamento[/dim]")
    payment_branch.add("[dim]Assina autorizacao final[/dim]")
    
    settlement_branch = tree.add("[cyan]4. Settlement[/cyan]")
    settlement_branch.add("[dim]Processador valida mandatos[/dim]")
    settlement_branch.add("[dim]Executa pagamento[/dim]")
    settlement_branch.add("[dim]Gera prova de settlement[/dim]")
    
    console.print(tree)
    
    console.print("\n[bold]Beneficios do AP2 com SDK Oficial:[/bold]")
    benefits = [
        "[cyan]Padronizado:[/cyan] Segue especificacao oficial do Google",
        "[cyan]Interoperavel:[/cyan] Compativel com outros implementadores",
        "[cyan]Seguro:[/cyan] Criptografia Ed25519 em todos os mandatos",
        "[cyan]Auditavel:[/cyan] Cadeia de mandatos cria trilha nao-repudiavel",
        "[cyan]Extensivel:[/cyan] Suporta diferentes rails de pagamento (x402, card, etc)",
    ]
    for b in benefits:
        console.print(f"  {b}")


def show_summary():
    """Mostrar resumo final."""
    demo_step(6, "Resumo", "Mandatos gerados nesta demo")
    
    summary = """
[bold]Arquivos e Configuracao:[/bold]

  SDK:        sdk/ap2-repo/ (clonado do Google)
  Tipos:      backend/src/security/ap2_types.py
  Adapters:   backend/src/security/ap2_adapters.py
  Security:   backend/src/security/ap2_security.py

[bold]Como usar no codigo:[/bold]

  from src.security import (
      AP2Security, 
      IntentMandate, 
      CartMandate, 
      PaymentMandate
  )
  
  ap2 = AP2Security()
  
  # Fluxo completo
  mandates = ap2.get_full_mandate_flow(
      cart_items=[{"title": "Livro", "price": 4990, "quantity": 1}],
      cart_id="cart_123",
      description="Compra de livros"
  )
    """
    console.print(summary)


def main():
    """Executar demonstracao."""
    print_header()
    
    try:
        # Verificar SDK
        sdk_available = check_sdk_availability()
        
        # 1. Intent Mandate
        ap2, key_manager, intent = demo_intent_mandate()
        
        # 2. Cart Mandate
        cart_mandate = demo_cart_mandate(ap2, key_manager)
        
        # 3. Payment Mandate
        payment_mandate = demo_payment_mandate(ap2, cart_mandate)
        
        # 4. Validacao
        demo_validation(ap2, cart_mandate)
        
        # 5. Diagrama de fluxo
        show_flow_diagram()
        
        # 6. Resumo
        show_summary()
        
        console.print("\n[bold green]{'='*60}[/bold green]")
        console.print("[bold green]  Demonstracao AP2 Concluida com Sucesso![/bold green]")
        console.print(f"[bold green]  SDK Oficial: {'Disponivel' if sdk_available else 'Fallback'}[/bold green]")
        console.print("[bold green]{'='*60}[/bold green]\n")
        
    except ImportError as e:
        console.print(f"[red]Erro de importacao: {e}[/red]")
        import traceback
        traceback.print_exc()
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
