#!/usr/bin/env python3
"""
Demo do User Agent - Agente Pessoal Generico

Este script demonstra todas as capacidades do User Agent:
1. Perguntas gerais (LLM)
2. Descoberta de agentes (A2A)
3. Descoberta de lojas (UCP)
4. Busca de produtos
5. Carteira Virtual (saldo, token, transacoes)
6. Compra com pagamento autonomo (AP2 + PSP)

Uso:
    python demo.py
    
Requisitos:
    - Backend rodando em http://localhost:8000
    - UCP Server rodando em http://localhost:8182
    - User Agent API rodando em http://localhost:8001
    - GOOGLE_API_KEY configurado no .env
    
Para subir todos os servicos:
    make up
"""
import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import print as rprint

# Adicionar src ao path
sys.path.insert(0, '.')

console = Console()


def print_section(title: str, emoji: str = "📌"):
    """Imprimir separador de seção."""
    console.print()
    console.print(f"[bold blue]{'='*60}[/bold blue]")
    console.print(f"[bold blue]{emoji} {title}[/bold blue]")
    console.print(f"[bold blue]{'='*60}[/bold blue]")
    console.print()


def print_demo_step(step: int, description: str):
    """Imprimir passo da demo."""
    console.print(f"\n[yellow]>>> Passo {step}:[/yellow] [bold]{description}[/bold]\n")


async def demo_question(runner):
    """Demo: Perguntas gerais."""
    print_section("PERGUNTAS GERAIS (LLM)", "💬")
    
    questions = [
        "O que é o protocolo UCP?",
        "Explique o que é A2A em uma frase.",
    ]
    
    for i, q in enumerate(questions, 1):
        print_demo_step(i, f'Perguntando: "{q}"')
        console.print(f"[dim]Voce:[/dim] {q}")
        
        response = await runner.process_message(q)
        console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))
        
        await asyncio.sleep(1)


async def demo_agents(runner):
    """Demo: Descoberta de agentes A2A."""
    print_section("DESCOBERTA DE AGENTES (A2A)", "🤖")
    
    # Listar agentes (vazio inicialmente)
    print_demo_step(1, "Listando agentes conectados")
    console.print("[dim]Voce:[/dim] listar agentes")
    response = await runner.process_message("listar agentes")
    console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))
    
    # Descobrir agente da loja
    print_demo_step(2, "Descobrindo agente da loja via A2A")
    console.print("[dim]Voce:[/dim] descobrir agente http://localhost:8000")
    response = await runner.process_message("descobrir agente http://localhost:8000")
    console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))
    
    # Listar agentes novamente
    print_demo_step(3, "Listando agentes apos descoberta")
    console.print("[dim]Voce:[/dim] listar agentes")
    response = await runner.process_message("listar agentes")
    console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))


async def demo_stores(runner):
    """Demo: Descoberta de lojas UCP."""
    print_section("DESCOBERTA DE LOJAS (UCP)", "🏪")
    
    # Descobrir loja
    print_demo_step(1, "Descobrindo loja UCP")
    console.print("[dim]Voce:[/dim] descobrir http://localhost:8182")
    response = await runner.process_message("descobrir http://localhost:8182")
    console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))
    
    # Verificar lojas
    stores = runner.get_discovered_stores()
    if stores:
        table = Table(title="Lojas Descobertas")
        table.add_column("URL")
        table.add_column("Nome")
        table.add_column("Status")
        
        for url, info in stores.items():
            status = "✅ Conectada" if info.get("connected") else "❌"
            table.add_row(url, info.get("name", "?"), status)
        
        console.print(table)


async def demo_shopping(runner):
    """Demo: Busca e compra de produtos."""
    print_section("BUSCA E COMPRA DE PRODUTOS", "🛒")
    
    # Buscar produtos
    print_demo_step(1, "Buscando livros de Python")
    console.print("[dim]Voce:[/dim] buscar livros de python")
    response = await runner.process_message("buscar livros de python")
    console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))
    
    # Adicionar ao carrinho
    print_demo_step(2, "Adicionando item 3 ao carrinho")
    console.print("[dim]Voce:[/dim] adicionar 3")
    response = await runner.process_message("adicionar 3")
    console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))
    
    # Ver carrinho
    print_demo_step(3, "Verificando carrinho")
    console.print("[dim]Voce:[/dim] carrinho")
    response = await runner.process_message("carrinho")
    console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))
    
    # Mostrar resumo do carrinho
    cart = runner.get_cart_summary()
    if cart["items"]:
        table = Table(title="Resumo do Carrinho")
        table.add_column("Item")
        table.add_column("Qtd", justify="center")
        table.add_column("Preco", justify="right")
        
        for item in cart["items"]:
            table.add_row(
                item["title"],
                str(item["quantity"]),
                f"R$ {item['price'] * item['quantity'] / 100:.2f}"
            )
        
        table.add_section()
        table.add_row("", "TOTAL", f"R$ {cart['total'] / 100:.2f}", style="bold green")
        console.print(table)


async def demo_checkout(runner):
    """Demo: Finalizar compra com AP2."""
    print_section("CHECKOUT COM AP2", "💳")
    
    console.print("[bold yellow]IMPORTANTE:[/bold yellow] O pagamento é autorizado pelo SEU agente!")
    console.print("[dim]O User Agent gera o mandato AP2 (PaymentMandate) com SUA chave Ed25519.[/dim]")
    console.print()
    
    # Verificar se tem itens no carrinho
    cart = runner.get_cart_summary()
    if not cart["items"]:
        console.print("[yellow]Carrinho vazio - pulando checkout[/yellow]")
        return
    
    # Iniciar checkout
    print_demo_step(1, "Iniciando checkout")
    console.print("[dim]Voce:[/dim] comprar")
    response = await runner.process_message("comprar")
    console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))
    
    # Se pediu confirmação, confirmar
    if runner.state and runner.state.get("waiting_for_confirmation"):
        print_demo_step(2, "Confirmando compra")
        console.print("[dim]Voce:[/dim] sim")
        response = await runner.process_message("sim")
        console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))
    
    # Mostrar mandato AP2 se gerado
    if runner.state and runner.state.get("ap2_mandate"):
        mandate = runner.state["ap2_mandate"]
        console.print()
        console.print("[bold green]✅ Mandato AP2 gerado com sucesso![/bold green]")
        console.print(f"   Payment Mandate ID: {mandate.get('payment_mandate_id', 'N/A')}")
        console.print(f"   Total Autorizado: R$ {mandate.get('total_authorized', 0) / 100:.2f}")
        console.print(f"   Moeda: {mandate.get('currency', 'BRL')}")


async def demo_wallet():
    """Demo: Carteira Virtual Pessoal."""
    import httpx
    
    print_section("CARTEIRA VIRTUAL PESSOAL", "💰")
    
    console.print("[bold yellow]A carteira pessoal é gerenciada pelo User Agent API (porta 8001)[/bold yellow]")
    console.print("[dim]Tokens wtk_* são reconhecidos pelo PSP e debitados desta carteira.[/dim]")
    console.print()
    
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=10.0) as client:
            # 1. Ver saldo atual
            print_demo_step(1, "Consultando saldo da carteira")
            res = await client.get("/wallet")
            wallet = res.json()
            
            table = Table(title="Carteira Pessoal")
            table.add_column("Campo", style="cyan")
            table.add_column("Valor", justify="right")
            table.add_row("Wallet ID", wallet["wallet_id"])
            table.add_row("Saldo", f"[green]{wallet['balance_formatted']}[/green]")
            table.add_row("Moeda", wallet["currency"])
            table.add_row("Transacoes", str(wallet["transaction_count"]))
            console.print(table)
            
            # 2. Gerar token de pagamento
            print_demo_step(2, "Gerando token de pagamento")
            res = await client.post("/wallet/token")
            token_data = res.json()
            console.print(f"[green]Token gerado:[/green] {token_data['token']}")
            console.print(f"[dim]Este token pode ser usado para pagamentos via PSP[/dim]")
            
            # 3. Verificar se pode pagar um valor
            print_demo_step(3, "Verificando limite para R$ 100.00")
            res = await client.get("/wallet/can-pay/10000")
            can_pay = res.json()
            status = "[green]✅ Pode pagar[/green]" if can_pay["can_pay"] else "[red]❌ Saldo insuficiente[/red]"
            console.print(f"Status: {status}")
            console.print(f"Saldo atual: R$ {can_pay['balance'] / 100:.2f}")
            console.print(f"Valor solicitado: R$ {can_pay['amount'] / 100:.2f}")
            
            # 4. Listar transacoes recentes
            print_demo_step(4, "Listando transacoes recentes")
            res = await client.get("/wallet/transactions?limit=5")
            txns = res.json()
            
            if txns["transactions"]:
                table = Table(title=f"Ultimas {len(txns['transactions'])} Transacoes")
                table.add_column("ID")
                table.add_column("Tipo")
                table.add_column("Valor", justify="right")
                table.add_column("Descricao")
                
                for t in txns["transactions"]:
                    tipo_cor = "[red]-[/red]" if t["type"] == "debit" else "[green]+[/green]"
                    table.add_row(
                        t["id"][:12] + "...",
                        f"{tipo_cor} {t['type']}",
                        f"R$ {t['amount'] / 100:.2f}",
                        t["description"][:30]
                    )
                console.print(table)
            else:
                console.print("[dim]Nenhuma transacao registrada ainda[/dim]")
            
            # 5. Adicionar fundos (demo)
            print_demo_step(5, "Adicionando R$ 50.00 (simulado)")
            res = await client.post("/wallet/add-funds", json={"amount": 5000})
            result = res.json()
            console.print(f"[green]✅ Fundos adicionados![/green]")
            console.print(f"Novo saldo: {result['new_balance_formatted']}")
            
    except httpx.ConnectError:
        console.print("[red]❌ User Agent API nao esta rodando![/red]")
        console.print("[yellow]Execute: make up-ua-api[/yellow]")
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


async def demo_tools(runner):
    """Demo: Ferramentas MCP."""
    import httpx
    from src.clients import MCPClient
    
    print_section("FERRAMENTAS MCP", "🔧")
    
    console.print("[bold yellow]Ferramentas MCP permitem ao agente acessar recursos da loja[/bold yellow]")
    console.print("[dim]A loja expõe ferramentas via /api/mcp/tools[/dim]")
    console.print()
    
    # 1. Registrar servidor MCP da loja
    print_demo_step(1, "Registrando servidor MCP da loja")
    
    try:
        mcp_url = "http://localhost:8000/api"
        client = MCPClient(mcp_url)
        tools = await client.discover_tools()
        
        if tools:
            # Registrar no estado do runner
            for tool in tools:
                runner.state["mcp_tools"][tool.name] = {
                    "name": tool.name,
                    "description": tool.description,
                    "server_url": mcp_url,
                    "input_schema": tool.input_schema
                }
            
            if mcp_url not in runner.state["mcp_servers"]:
                runner.state["mcp_servers"].append(mcp_url)
            
            console.print(f"[green]✅ {len(tools)} ferramentas MCP descobertas![/green]")
            
            # Mostrar ferramentas
            table = Table(title="Ferramentas MCP Disponíveis")
            table.add_column("Nome", style="cyan")
            table.add_column("Descrição")
            
            for tool in tools:
                table.add_row(tool.name, tool.description[:60] + "..." if len(tool.description) > 60 else tool.description)
            
            console.print(table)
        else:
            console.print("[yellow]Nenhuma ferramenta encontrada[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Erro ao descobrir ferramentas: {e}[/red]")
    
    # 2. Usar ferramenta search_books
    print_demo_step(2, "Usando ferramenta search_books via MCP")
    
    try:
        result = await client.search_books("python", max_results=3)
        
        if result.success:
            console.print("[green]✅ Busca executada via MCP![/green]")
            books = result.data.get("books", []) if isinstance(result.data, dict) else []
            
            if books:
                table = Table(title="Livros encontrados (via MCP)")
                table.add_column("Título")
                table.add_column("Preço", justify="right")
                
                for book in books[:3]:
                    table.add_row(
                        book.get("title", "?")[:40],
                        f"R$ {book.get('price', 0) / 100:.2f}"
                    )
                console.print(table)
        else:
            console.print(f"[red]Erro: {result.error}[/red]")
            
    except Exception as e:
        console.print(f"[red]Erro ao usar ferramenta: {e}[/red]")
    
    # 3. Usar ferramenta list_categories
    print_demo_step(3, "Usando ferramenta list_categories via MCP")
    
    try:
        result = await client.list_categories()
        
        if result.success:
            console.print("[green]✅ Categorias obtidas via MCP![/green]")
            categories = result.data.get("categories", []) if isinstance(result.data, dict) else []
            
            if categories:
                console.print(f"[cyan]Categorias:[/cyan] {', '.join(categories)}")
        else:
            console.print(f"[red]Erro: {result.error}[/red]")
            
    except Exception as e:
        console.print(f"[red]Erro ao listar categorias: {e}[/red]")
    
    # 4. Listar transacoes via MCP
    print_demo_step(4, "Listando transacoes via MCP (ferramenta list_transactions)")
    
    try:
        result = await client.list_transactions(limit=5)
        
        if result.success:
            console.print("[green]✅ Transações obtidas via MCP![/green]")
            transactions = result.data.get("transactions", []) if isinstance(result.data, dict) else []
            
            if transactions:
                table = Table(title="Transações (via MCP)")
                table.add_column("ID")
                table.add_column("Valor", justify="right")
                table.add_column("Status")
                table.add_column("Origem")
                
                for t in transactions[:5]:
                    status_color = "[green]" if t.get("status") == "success" else "[red]"
                    table.add_row(
                        t.get("id", "?")[:16] + "...",
                        t.get("amount_formatted", "?"),
                        f"{status_color}{t.get('status', '?')}[/]",
                        t.get("wallet_source", "?")
                    )
                console.print(table)
            else:
                console.print("[dim]Nenhuma transação encontrada[/dim]")
        else:
            console.print(f"[red]Erro: {result.error}[/red]")
            
    except Exception as e:
        console.print(f"[red]Erro ao listar transações: {e}[/red]")
    
    # Fechar cliente
    await client.close()
    
    # 5. Listar via comando do agente
    print_demo_step(5, "Listando ferramentas via comando do agente")
    console.print("[dim]Voce:[/dim] listar ferramentas")
    response = await runner.process_message("listar ferramentas")
    console.print(Panel(response, title="[cyan]Agente[/cyan]", border_style="cyan"))


async def main():
    """Executar demo completa."""
    from src.agent import UserAgentRunner
    from src.agent.llm import is_llm_enabled
    
    # Banner
    console.print()
    console.print(Panel.fit(
        "[bold blue]USER AGENT - DEMO DO AGENTE PESSOAL[/bold blue]\n\n"
        "Demonstração das capacidades do seu agente autônomo:\n"
        "• Conversação com LLM (Gemini)\n"
        "• Descoberta de Agentes (A2A)\n"
        "• Descoberta de Lojas (UCP)\n"
        "• Carteira Virtual Pessoal (Wallet)\n"
        "• Compras com Pagamento Autônomo (AP2 + PSP)\n"
        "• Ferramentas Externas (MCP)",
        title="🤖 Demo",
        border_style="blue"
    ))
    
    # Verificar LLM
    llm_status = "[green]✅ Ativo (Gemini)[/green]" if is_llm_enabled() else "[red]❌ Desativado[/red]"
    console.print(f"\nStatus do LLM: {llm_status}")
    
    if not is_llm_enabled():
        console.print("[yellow]⚠️  Configure GOOGLE_API_KEY no .env para habilitar o LLM[/yellow]")
    
    # Inicializar runner
    runner = UserAgentRunner()
    runner.initialize("demo-session", "Usuario Demo", "demo@example.com")
    
    console.print(f"\n[dim]Sessão iniciada: {runner.state['session_id']}[/dim]")
    
    # Executar demos
    try:
        # 1. Perguntas gerais
        if is_llm_enabled():
            await demo_question(runner)
        else:
            console.print("\n[yellow]Pulando demo de perguntas (LLM desativado)[/yellow]")
        
        await asyncio.sleep(3)
        
        # 2. Descoberta de agentes A2A
        await demo_agents(runner)
        
        await asyncio.sleep(3)
        
        # 3. Descoberta de lojas UCP
        await demo_stores(runner)
        
        await asyncio.sleep(3)
        
        # 4. Busca e compra
        await demo_shopping(runner)
        
        await asyncio.sleep(3)
        
        # 5. Carteira Virtual Pessoal
        await demo_wallet()
        
        await asyncio.sleep(3)
        
        # 6. Checkout com AP2
        await demo_checkout(runner)
        
        await asyncio.sleep(3)
        
        # 7. Ferramentas MCP
        await demo_tools(runner)
        
    except Exception as e:
        console.print(f"[red]Erro durante demo: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    # Resumo final
    print_section("RESUMO FINAL", "📊")
    
    status = runner.get_status()
    
    table = Table(title="Status do Agente Pessoal")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", justify="right")
    
    table.add_row("LLM", "Ativo" if status.get("llm_enabled") else "Inativo")
    table.add_row("Agentes Conectados", str(status.get("agents_count", 0)))
    table.add_row("Lojas Descobertas", str(status.get("stores_count", 0)))
    table.add_row("Itens no Carrinho", str(status.get("cart_count", 0)))
    table.add_row("Carteira Pessoal", "Ativa (porta 8001)")
    table.add_row("Ferramentas MCP", str(status.get("tools_count", 0)))
    
    console.print(table)
    
    # Arquitetura
    console.print()
    console.print(Panel(
        "[bold]Arquitetura do User Agent:[/bold]\n\n"
        "┌──────────────────────────────────────────────────────────┐\n"
        "│                      USER AGENT                          │\n"
        "│                   (Agente Pessoal)                       │\n"
        "│                                                          │\n"
        "│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │\n"
        "│  │  LLM   │ │  A2A   │ │  UCP   │ │ Wallet │ │  MCP   │ │\n"
        "│  │ Gemini │ │Agentes │ │ Lojas  │ │ wtk_*  │ │ Tools  │ │\n"
        "│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ │\n"
        "│      │          │          │          │          │      │\n"
        "│      └──────────┼──────────┼──────────┼──────────┘      │\n"
        "│                 │          │          │                 │\n"
        "│           ┌─────┴────┐ ┌───┴───┐ ┌────┴────┐            │\n"
        "│           │  Store   │ │  AP2  │ │   PSP   │            │\n"
        "│           │  Agent   │ │Mandate│ │ Payment │            │\n"
        "│           └──────────┘ └───────┘ └─────────┘            │\n"
        "│                            ↑          ↑                 │\n"
        "│            [VOCÊ AUTORIZA] │ [DEBITA CARTEIRA PESSOAL]  │\n"
        "└──────────────────────────────────────────────────────────┘",
        title="Arquitetura",
        border_style="green"
    ))
    
    console.print()
    console.print("[bold green]✅ Demo concluída![/bold green]")
    console.print()
    console.print("Para usar interativamente:")
    console.print("  [cyan]python -m src.cli chat[/cyan]")
    console.print()


if __name__ == "__main__":
    asyncio.run(main())
