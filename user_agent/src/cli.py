"""CLI do User Agent - Agente Pessoal Generico."""
import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.layout import Layout
from rich.text import Text
from typing import Optional

from .agent import UserAgentRunner
from .agent.llm import is_llm_enabled
from .config import settings

app = typer.Typer(
    name="user-agent",
    help="User Agent - Seu Agente Pessoal Autonomo"
)
console = Console()


def print_welcome():
    """Imprimir mensagem de boas-vindas."""
    llm_status = "[green]Ativo (Gemini)[/green]" if is_llm_enabled() else "[yellow]Desativado[/yellow]"
    
    welcome = f"""
# User Agent - Seu Assistente Pessoal

Sou seu agente autonomo! Posso conversar, descobrir outros agentes, fazer compras e usar ferramentas.

**LLM:** {llm_status}
**Protocolos:** UCP, A2A, MCP, AP2

## O que posso fazer

### 💬 Conversar
Faca perguntas sobre qualquer assunto

### 🤖 Descobrir Agentes (A2A)
- **descobrir agente [url]** - Conectar a um agente
- **listar agentes** - Ver agentes conectados

### 🛒 Fazer Compras (UCP)
- **descobrir [url]** - Conectar a loja
- **buscar [termo]** - Buscar produtos
- **adicionar [n]** - Adicionar ao carrinho
- **comprar** - Finalizar (eu autorizo o pagamento!)

### 🔧 Ferramentas (MCP)
- **listar ferramentas** - Ver ferramentas disponiveis

### Outros
- **ajuda** - Ver ajuda completa
- **status** - Ver status atual
- **sair** - Encerrar

Digite uma mensagem!
"""
    console.print(Panel(Markdown(welcome), title="Bem-vindo!", border_style="blue"))


def print_response(response: str, is_llm: bool = False):
    """Imprimir resposta do agente."""
    title = "Agente (LLM)" if is_llm else "Agente"
    style = "cyan" if is_llm else "green"
    
    console.print(Panel(
        Markdown(response),
        title=title,
        border_style=style
    ))


def print_cart_summary(runner: UserAgentRunner):
    """Imprimir resumo do carrinho."""
    cart = runner.get_cart_summary()
    
    if not cart["items"]:
        return
    
    table = Table(title="Carrinho")
    table.add_column("Item", style="cyan")
    table.add_column("Qtd", justify="center")
    table.add_column("Preco", justify="right", style="green")
    
    for item in cart["items"]:
        table.add_row(
            item["title"][:30],
            str(item["quantity"]),
            f"R$ {item['price'] * item['quantity'] / 100:.2f}"
        )
    
    if cart.get("discount") and cart["discount"] > 0:
        table.add_section()
        table.add_row("Subtotal", "", f"R$ {(cart['total'] + cart['discount']) / 100:.2f}")
        table.add_row(f"Desconto ({cart.get('applied_discount', '')})", "", f"-R$ {cart['discount'] / 100:.2f}", style="red")
    
    table.add_section()
    table.add_row("", "TOTAL", f"R$ {cart['total'] / 100:.2f}", style="bold")
    
    console.print(table)


def print_stores(runner: UserAgentRunner):
    """Imprimir lojas descobertas."""
    stores = runner.get_discovered_stores()
    
    if not stores:
        console.print("[yellow]Nenhuma loja conectada.[/yellow]")
        console.print("Use: [cyan]descobrir http://localhost:8182[/cyan]")
        return
    
    table = Table(title="Lojas Conectadas")
    table.add_column("Nome", style="cyan")
    table.add_column("URL")
    table.add_column("UCP", justify="center")
    table.add_column("A2A", justify="center")
    
    for url, info in stores.items():
        ucp_status = "[green]OK[/green]" if info.get("connected") else "[red]X[/red]"
        a2a_status = "[green]OK[/green]" if info.get("a2a_connected") else "[dim]-[/dim]"
        table.add_row(info.get("name", "?"), url, ucp_status, a2a_status)
    
    console.print(table)


def print_status_bar(runner: UserAgentRunner):
    """Imprimir barra de status do Agente Pessoal."""
    status_info = runner.get_status()
    cart = runner.get_cart_summary()
    
    agents_count = status_info.get("agents_count", 0)
    stores_count = status_info.get("stores_count", 0)
    tools_count = status_info.get("tools_count", 0)
    cart_count = len(cart["items"])
    cart_total = cart["total"] / 100 if cart["total"] else 0
    llm = "[green]LLM[/green]" if runner.is_llm_enabled() else "[dim]LLM[/dim]"
    
    status = Text()
    
    # Agentes
    if agents_count > 0:
        status.append(f" 🤖 {agents_count} ", style="cyan")
        status.append("|")
    
    # Lojas
    status.append(f" 🏪 {stores_count} ", style="bold" if stores_count else "dim")
    status.append("|")
    
    # Carrinho
    status.append(f" 🛒 {cart_count} ", style="cyan" if cart_count else "dim")
    if cart_count:
        status.append(f"(R$ {cart_total:.2f})", style="green")
    status.append(" |")
    
    # Ferramentas
    if tools_count > 0:
        status.append(f" 🔧 {tools_count} ", style="yellow")
        status.append("|")
    
    # LLM
    status.append(f" {llm} ")
    
    console.print(Panel(status, height=3, border_style="dim"))


def print_agents(runner: UserAgentRunner):
    """Imprimir agentes conectados."""
    agents = runner.get_connected_agents()
    
    if not agents:
        console.print("[yellow]Nenhum agente conectado.[/yellow]")
        console.print("Use: [cyan]descobrir agente http://localhost:8000[/cyan]")
        return
    
    table = Table(title="Agentes Conectados (A2A)")
    table.add_column("Nome", style="cyan")
    table.add_column("URL")
    table.add_column("Skills")
    table.add_column("Status", justify="center")
    
    for url, info in agents.items():
        status = "[green]✓[/green]" if info.get("connected") else "[red]✗[/red]"
        skills = ", ".join(info.get("skills", [])[:3])
        if len(info.get("skills", [])) > 3:
            skills += "..."
        table.add_row(info.get("name", "?"), url, skills, status)
    
    console.print(table)


def print_tools(runner: UserAgentRunner):
    """Imprimir ferramentas MCP disponiveis."""
    tools = runner.get_mcp_tools()
    
    if not tools:
        console.print("[yellow]Nenhuma ferramenta MCP disponivel.[/yellow]")
        console.print("[dim]Ferramentas MCP permitem acesso a funcionalidades externas.[/dim]")
        return
    
    table = Table(title="Ferramentas MCP")
    table.add_column("Nome", style="cyan")
    table.add_column("Descricao")
    table.add_column("Servidor")
    
    for name, info in tools.items():
        table.add_row(name, info.get("description", "-")[:50], info.get("server_url", "-"))
    
    console.print(table)


@app.command()
def chat(
    store_url: str = typer.Option(
        None,
        "--store", "-s",
        help="URL da loja UCP para conectar automaticamente"
    ),
    agent_url: str = typer.Option(
        None,
        "--agent", "-a",
        help="URL do agente A2A para conectar automaticamente"
    ),
    user_name: str = typer.Option(
        None,
        "--name", "-n",
        help="Seu nome"
    ),
    user_email: str = typer.Option(
        None,
        "--email", "-e",
        help="Seu email"
    ),
    no_auto_connect: bool = typer.Option(
        False,
        "--no-connect",
        help="Nao conectar automaticamente"
    )
):
    """Iniciar chat interativo com o User Agent (Agente Pessoal)."""
    print_welcome()
    
    runner = UserAgentRunner()
    runner.initialize("cli-session", user_name, user_email)
    
    # Conectar a agente A2A se fornecido
    if agent_url and not no_auto_connect:
        console.print(f"\n[dim]Conectando ao agente {agent_url}...[/dim]")
        with console.status("[bold cyan]Descobrindo agente..."):
            response = asyncio.run(runner.process_message(f"descobrir agente {agent_url}"))
        print_response(response, runner.is_llm_enabled())
    
    # Conectar a loja inicial se fornecida
    if store_url and not no_auto_connect:
        console.print(f"\n[dim]Conectando a loja {store_url}...[/dim]")
        with console.status("[bold green]Descobrindo loja..."):
            response = asyncio.run(runner.process_message(f"descobrir {store_url}"))
        print_response(response, runner.is_llm_enabled())
    
    # Loop principal
    while True:
        try:
            # Mostrar status
            print_status_bar(runner)
            
            # Input do usuario
            user_input = Prompt.ask("\n[bold blue]Voce[/bold blue]")
            
            if not user_input.strip():
                continue
            
            # Comandos especiais do CLI
            cmd = user_input.lower().strip()
            
            if cmd in ["sair", "exit", "quit", "q"]:
                console.print("[yellow]Ate logo![/yellow]")
                break
            
            if cmd in ["carrinho", "cart"]:
                print_cart_summary(runner)
                continue
            
            if cmd in ["lojas", "stores"]:
                print_stores(runner)
                continue
            
            if cmd in ["agentes", "agents"]:
                print_agents(runner)
                continue
            
            if cmd in ["ferramentas", "tools"]:
                print_tools(runner)
                continue
            
            if cmd in ["status"]:
                # Status completo
                status = runner.get_status()
                console.print(f"\n[bold]Status do Agente Pessoal[/bold]")
                console.print(f"  LLM: {'[green]Ativo[/green]' if status.get('llm_enabled') else '[dim]Inativo[/dim]'}")
                console.print(f"  Agentes: {status.get('agents_count', 0)}")
                console.print(f"  Lojas: {status.get('stores_count', 0)}")
                console.print(f"  Carrinho: {status.get('cart_count', 0)} itens")
                console.print(f"  Ferramentas: {status.get('tools_count', 0)}")
                continue
            
            if cmd in ["limpar", "clear", "cls"]:
                console.clear()
                print_welcome()
                continue
            
            # Processar com agente
            with console.status("[bold green]Pensando..."):
                response = asyncio.run(runner.process_message(user_input))
            
            print_response(response, runner.is_llm_enabled())
            
            # Mostrar carrinho se relevante
            if any(word in cmd for word in ["adicionar", "remover", "carrinho", "add", "remove"]):
                print_cart_summary(runner)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Ate logo![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Erro: {e}[/red]")
            if settings.debug:
                console.print_exception()


@app.command()
def discover(
    url: str = typer.Argument(..., help="URL da loja UCP")
):
    """Descobrir uma loja UCP."""
    from .clients import UCPClient
    
    async def _discover():
        console.print(f"[dim]Descobrindo {url}...[/dim]")
        
        try:
            async with UCPClient(url) as client:
                profile = await client.discover()
                
                if profile:
                    table = Table(title=f"Loja: {profile.name}")
                    table.add_column("Propriedade", style="cyan")
                    table.add_column("Valor")
                    
                    table.add_row("URL", url)
                    table.add_row("Versao UCP", profile.version)
                    
                    # Payment handlers
                    handlers = profile.payment_handlers
                    if handlers:
                        if isinstance(handlers[0], dict):
                            handler_names = [h.get("name", h.get("id", str(h))) for h in handlers]
                        else:
                            handler_names = [str(h) for h in handlers]
                        table.add_row("Payment Handlers", ", ".join(handler_names))
                    
                    # Capabilities
                    if profile.capabilities:
                        caps = list(profile.capabilities.keys())[:5]
                        table.add_row("Capabilities", ", ".join(caps))
                    
                    console.print(table)
                else:
                    console.print("[red]Loja nao encontrada ou nao suporta UCP[/red]")
        except Exception as e:
            console.print(f"[red]Erro: {e}[/red]")
    
    asyncio.run(_discover())


@app.command()
def search(
    query: str = typer.Argument(..., help="Termo de busca"),
    store_url: str = typer.Option(
        "http://localhost:8182",
        "--store", "-s",
        help="URL da loja"
    )
):
    """Buscar produtos em uma loja."""
    from .clients import UCPClient
    
    async def _search():
        try:
            async with UCPClient(store_url) as client:
                await client.discover()
                products = await client.search_products(query)
                
                if products:
                    table = Table(title=f"Resultados para '{query}'")
                    table.add_column("#", style="dim")
                    table.add_column("Titulo", style="cyan")
                    table.add_column("Autor")
                    table.add_column("Preco", justify="right", style="green")
                    table.add_column("Estoque", justify="center")
                    
                    for i, p in enumerate(products[:10], 1):
                        stock = p.get("stock", "?")
                        stock_style = "green" if stock and stock > 0 else "red"
                        table.add_row(
                            str(i),
                            p.get("title", "")[:40],
                            p.get("author", "")[:20],
                            f"R$ {p.get('price', 0) / 100:.2f}",
                            Text(str(stock), style=stock_style)
                        )
                    
                    console.print(table)
                else:
                    console.print(f"[yellow]Nenhum resultado para '{query}'[/yellow]")
        except Exception as e:
            console.print(f"[red]Erro: {e}[/red]")
    
    asyncio.run(_search())


@app.command()
def buy(
    product_id: str = typer.Argument(..., help="ID do produto"),
    store_url: str = typer.Option(
        "http://localhost:8182",
        "--store", "-s",
        help="URL da loja"
    ),
    quantity: int = typer.Option(1, "--qty", "-q", help="Quantidade")
):
    """Comprar um produto diretamente via UCP."""
    from .clients import UCPClient
    from .security import get_ap2_client
    
    async def _buy():
        console.print(f"[dim]Iniciando compra de {product_id}...[/dim]")
        
        try:
            async with UCPClient(store_url) as client:
                await client.discover()
                
                # Buscar detalhes do produto
                product = await client.get_product(product_id)
                if not product:
                    console.print(f"[red]Produto {product_id} nao encontrado[/red]")
                    return
                
                # Mostrar produto
                console.print(f"\n[cyan]{product.get('title')}[/cyan]")
                console.print(f"Preco: R$ {product.get('price', 0) / 100:.2f}")
                console.print(f"Quantidade: {quantity}\n")
                
                # Criar checkout no formato UCP
                line_items = [{
                    "item": {
                        "id": product_id,
                        "title": product.get("title", product_id)
                    },
                    "quantity": quantity
                }]
                buyer_info = {"full_name": "CLI User", "email": "cli@user-agent.local"}
                
                with console.status("Criando checkout..."):
                    session = await client.create_checkout(line_items, buyer_info)
                
                if not session:
                    console.print("[red]Falha ao criar checkout[/red]")
                    return
                
                console.print(f"[green]Checkout criado: {session.id[:8]}...[/green]")
                console.print(f"Total: R$ {session.total / 100:.2f}\n")
                
                # Confirmar
                confirm = Prompt.ask("Confirmar compra?", choices=["s", "n"], default="s")
                
                if confirm == "s":
                    # Gerar mandato AP2
                    ap2 = get_ap2_client()
                    mandate = ap2.create_mandate_for_checkout(
                        session.total, "BRL", store_url
                    )
                    console.print(f"[dim]Mandato AP2: {mandate.key_id}[/dim]")
                    
                    with console.status("Processando pagamento..."):
                        result = await client.complete_checkout(
                            session.id,
                            "success_token",
                            mandate.jwt
                        )
                    
                    if result.get("status") == "completed":
                        console.print(Panel(
                            f"[green]Compra realizada![/green]\n\n"
                            f"Pedido: #{result.get('order_id', result.get('id', session.id))}",
                            title="Sucesso",
                            border_style="green"
                        ))
                    else:
                        error = result.get("error", result.get("detail", "Erro desconhecido"))
                        console.print(f"[red]Falha: {error}[/red]")
                else:
                    console.print("[yellow]Compra cancelada[/yellow]")
        except Exception as e:
            console.print(f"[red]Erro: {e}[/red]")
            if settings.debug:
                console.print_exception()
    
    asyncio.run(_buy())


@app.command()
def info():
    """Mostrar informacoes do User Agent."""
    from .agent.llm import is_llm_enabled
    from .security.ap2_client import AP2Client
    
    table = Table(title="User Agent - Informacoes")
    table.add_column("Componente", style="cyan")
    table.add_column("Status")
    table.add_column("Detalhes")
    
    # LLM
    if is_llm_enabled():
        table.add_row("LLM", "[green]Ativo[/green]", f"Gemini {settings.gemini_model}")
    else:
        table.add_row("LLM", "[yellow]Inativo[/yellow]", "Configure GOOGLE_API_KEY")
    
    # AP2
    ap2_sdk = "[green]SDK[/green]" if AP2Client.is_sdk_available() else "[yellow]Local[/yellow]"
    table.add_row("AP2", ap2_sdk, "Ed25519 JWT")
    
    # URLs
    table.add_row("API Gateway", "[dim]-[/dim]", settings.api_gateway_url)
    table.add_row("UCP Server", "[dim]-[/dim]", settings.ucp_server_url)
    
    console.print(table)


def main():
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
