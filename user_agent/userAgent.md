# User Agent - Agente Pessoal Autônomo

Este diretório contém o código fonte do **User Agent**, um agente pessoal autônomo e genérico que atua como assistente do usuário. O User Agent pode descobrir e interagir com agentes A2A, lojas UCP, usar ferramentas MCP e realizar compras autônomas com pagamento AP2.

## Visão Geral

O User Agent é um agente inteligente que:

- **Conversa** com o usuário de forma natural usando LLM
- **Descobre e conecta** a agentes A2A e lojas UCP
- **Busca produtos** em múltiplas lojas simultaneamente
- **Gerencia carrinho** multi-loja
- **Compara preços** entre lojas diferentes
- **Realiza compras autônomas** com pagamento AP2 (3 mandatos)
- **Usa ferramentas MCP** para ações externas
- **Delega tarefas** para agentes especializados

---

## Arquitetura do User Agent

```
user_agent/
├── src/
│   ├── __init__.py          # Exports principais
│   ├── cli.py               # Interface CLI (Typer)
│   ├── config.py            # Configurações
│   │
│   ├── agent/               # Agente Principal (LangGraph)
│   │   ├── agent.md         # → Documentação completa
│   │   ├── state.py         # Estado compartilhado
│   │   ├── graph.py         # Grafo LangGraph
│   │   ├── llm.py           # Integração LLM
│   │   └── nodes/           # Nodes especializados
│   │       ├── discovery.py
│   │       ├── shopping.py
│   │       ├── compare.py
│   │       └── chat.py
│   │
│   ├── clients/             # Clientes de Protocolo
│   │   ├── client.md        # → Documentação completa
│   │   ├── ucp_client.py    # Cliente UCP
│   │   ├── a2a_client.py    # Cliente A2A
│   │   └── mcp_client.py    # Cliente MCP
│   │
│   ├── security/            # Segurança AP2
│   │   ├── ap2.md           # → Documentação AP2
│   │   ├── ap2_client.py    # Cliente AP2 (3 mandatos)
│   │   └── key_manager.py   # Gerenciamento de chaves Ed25519
│   │
│   └── wallet/              # Carteira Virtual
│       ├── wallet.md        # → Documentação Wallet
│       ├── __init__.py      # Exports
│       └── wallet.py        # VirtualWallet
│
├── .env                     # Configurações locais
├── pyproject.toml           # Dependências Python
├── requirements.txt         # Requirements
└── userAgent.md            # Esta documentação
```

### Diagrama de Arquitetura Completo

```mermaid
flowchart TB
    subgraph User["Usuário"]
        CLI["CLI Interface<br/>Typer + Rich"]
    end

    subgraph UserAgent["User Agent Source"]
        subgraph CLI["CLI :cli.py"]
            Commands["Comandos Typer<br/>chat, discover, search, buy"]
        end
        
        subgraph Agent["Agent Module"]
            Runner["UserAgentRunner"]
            Graph["user_agent_graph<br/>LangGraph"]
            Router["router_node"]
            Nodes["nodes/<br/>Discovery, Shopping, Compare, Chat"]
            LLM["llm.py<br/>Gemini/OpenAI"]
        end
        
        subgraph Clients["Clients Module"]
            UCP["UCPClient<br/>HTTP REST"]
            A2A["A2AClient<br/>WebSocket"]
            MCP["MCPClient<br/>HTTP REST"]
        end
        
        subgraph Security["Security Module"]
            AP2["AP2Client<br/>Mandatos JWT"]
            Keys["UserKeyManager<br/>Ed25519"]
        end
        
        subgraph Config["Config"]
            Settings["settings<br/>Pydantic"]
        end
    end

    subgraph External["Serviços Externos"]
        UCPStores["Lojas UCP<br/>:8182"]
        A2AAgents["Agentes A2A<br/>:8000"]
        MCPServers["Servidores MCP<br/>:8183"]
    end

    CLI --> Commands
    Commands --> Runner
    Runner --> Graph
    Graph --> Router
    Router --> LLM
    Router --> Nodes
    
    Nodes --> UCP
    Nodes --> A2A
    Nodes --> MCP
    Nodes --> AP2
    
    UCP --> UCPStores
    A2A --> A2AAgents
    MCP --> MCPServers
    
    AP2 --> Keys
    AP2 --> UCPStores
    
    Graph --> Config
    LLM --> Config
    
    style Agent fill:#e3f2fd
    style Clients fill:#fff3e0
    style Security fill:#f3e5f5
```

---

## Componentes Principais

### 1. CLI (`cli.py`)

Interface de linha de comando usando Typer e Rich para uma experiência interativa.

#### Comandos Disponíveis

| Comando | Descrição | Uso |
|---------|-----------|-----|
| `chat` | Iniciar chat interativo | `user-agent chat [--store URL] [--agent URL]` |
| `discover` | Descobrir loja UCP | `user-agent discover <url>` |
| `search` | Buscar produtos | `user-agent search <query> [--store URL]` |
| `buy` | Comprar produto diretamente | `user-agent buy <product_id> [--store URL]` |
| `info` | Mostrar informações do agente | `user-agent info` |

#### Estrutura do CLI

```mermaid
flowchart TD
    subgraph CLI["CLI (cli.py)"]
        Main["main()"]
        Chat["chat()"]
        Discover["discover()"]
        Search["search()"]
        Buy["buy()"]
        Info["info()"]
    end
    
    subgraph Helpers["Helpers"]
        Welcome["print_welcome()"]
        Response["print_response()"]
        Cart["print_cart_summary()"]
        Stores["print_stores()"]
        Agents["print_agents()"]
        Tools["print_tools()"]
        Status["print_status_bar()"]
    end
    
    subgraph Agent["Agent Module"]
        Runner["UserAgentRunner"]
    end
    
    Main --> Chat
    Main --> Discover
    Main --> Search
    Main --> Buy
    Main --> Info
    
    Chat --> Welcome
    Chat --> Runner
    Chat --> Response
    Chat --> Cart
    Chat --> Status
    
    Discover --> UCP["UCPClient"]
    Search --> UCP
    Buy --> UCP
    Buy --> AP2["AP2Client"]
```

#### Fluxo de Chat Interativo

```mermaid
sequenceDiagram
    participant U as Usuário
    participant CLI as CLI
    participant Runner as UserAgentRunner
    participant Graph as LangGraph

    CLI->>CLI: print_welcome()
    CLI->>Runner: initialize()
    
    loop Chat Loop
        CLI->>CLI: print_status_bar()
        CLI->>U: Prompt input
        U->>CLI: Mensagem
        
        alt Comando Especial
            CLI->>CLI: Executar comando (carrinho, lojas, etc)
        else Mensagem Normal
            CLI->>Runner: process_message(message)
            Runner->>Graph: ainvoke(state)
            Graph-->>Runner: result
            Runner-->>CLI: response
            CLI->>CLI: print_response(response)
            CLI->>CLI: print_cart_summary() (se relevante)
        end
    end
```

---

### 2. Agent Module (`agent/`)

Sistema de agentes inteligentes usando LangGraph.

📄 **Documentação completa:** [`src/agent/agent.md`](src/agent/agent.md)

#### Visão Geral

O módulo Agent implementa o agente pessoal usando LangGraph com:

- **State** - Estado compartilhado (`UserAgentState`)
- **Graph** - Grafo LangGraph orquestrador
- **Router** - Detecção de intenção inteligente (LLM/keywords)
- **Nodes** - Nodes especializados (Discovery, Shopping, Compare, Chat)

```mermaid
flowchart LR
    subgraph Agent["agent/"]
        State["state.py<br/>UserAgentState"]
        Graph["graph.py<br/>LangGraph"]
        LLM["llm.py<br/>Gemini/OpenAI"]
        Nodes["nodes/<br/>4 nodes"]
    end
    
    Graph --> State
    Graph --> LLM
    Graph --> Nodes
    Nodes --> State
```

#### Nodes Disponíveis

| Node | Responsabilidade | Intenções |
|------|------------------|-----------|
| **router** | Detectar intenção e rotear | Todas |
| **question** | Responder perguntas gerais | question |
| **agents** | Gerenciar agentes A2A | discover_agent, list_agents |
| **discovery** | Descobrir lojas e buscar produtos | discover, search, recommend |
| **shopping** | Carrinho e checkout | add_to_cart, checkout, apply_discount |
| **compare** | Comparar preços | compare |
| **chat** | Conversa via A2A | talk_to_agent, chat |
| **mcp** | Ferramentas MCP | use_tool, list_tools |
| **help** | Ajuda | help |

---

### 3. Clients Module (`clients/`)

Clientes para comunicação com protocolos externos.

📄 **Documentação completa:** [`src/clients/client.md`](src/clients/client.md)

#### Visão Geral

O módulo Clients fornece três clientes principais:

- **UCPClient** - Cliente para Universal Commerce Protocol
- **A2AClient** - Cliente para Agent-to-Agent Protocol
- **MCPClient** - Cliente para Model Context Protocol

```mermaid
flowchart LR
    subgraph Clients["clients/"]
        UCP["UCPClient<br/>HTTP REST"]
        A2A["A2AClient<br/>WebSocket"]
        MCP["MCPClient<br/>HTTP REST"]
    end
    
    subgraph External["Externo"]
        UCPProto["UCP Server"]
        A2AProto["A2A Server"]
        MCPProto["MCP Server"]
    end
    
    UCP -->|HTTP| UCPProto
    A2A -->|WebSocket| A2AProto
    MCP -->|HTTP| MCPProto
```

#### Funcionalidades por Cliente

**UCPClient:**
- Descoberta de lojas (`discover()`)
- Busca de produtos (`search_products()`)
- Criação de checkout (`create_checkout()`)
- Aplicação de descontos (`apply_discount()`)
- Completar checkout (`complete_checkout()`)

**A2AClient:**
- Conexão WebSocket persistente (`connect()`)
- Requisições A2A (`request()`)
- Reconexão automática
- Keep-alive (ping)
- Pool de conexões (`A2AClientPool`)

**MCPClient:**
- Descoberta de ferramentas (`discover_tools()`)
- Chamada de ferramentas (`call_tool()`)
- Helpers específicos (search_books, get_book_details, etc.)

---

### 4. Security Module (`security/`)

Segurança AP2 e gerenciamento de chaves para pagamentos autônomos.

📄 **Documentação:** [`src/security/ap2.md`](src/security/ap2.md)

#### Componentes

- **AP2Client** - Geração de mandatos JWT para pagamentos autônomos
- **UserKeyManager** - Gerenciamento de chaves Ed25519 do usuário

#### Fluxo de 3 Mandatos AP2

```mermaid
sequenceDiagram
    participant User as User Agent
    participant AP2 as AP2Client
    participant Store as Loja UCP

    Note over User,Store: 1. Intent Mandate
    User->>AP2: create_intent_mandate(description, merchants)
    AP2->>AP2: Gerar JWT com chave Ed25519
    AP2-->>User: intent_mandate_jwt
    
    Note over User,Store: 2. Cart Mandate (do Merchant)
    User->>Store: create_checkout(items)
    Store->>Store: Criar Cart Mandate
    Store-->>User: cart_mandate_jwt
    
    Note over User,Store: 3. Payment Mandate
    User->>AP2: create_payment_mandate(cart_mandate_jwt, total)
    AP2->>AP2: Validar cart mandate
    AP2->>AP2: Gerar payment mandate JWT
    AP2-->>User: payment_mandate_jwt
    
    User->>Store: complete_checkout(session_id, payment_mandate_jwt)
    Store->>Store: Validar payment mandate
    Store-->>User: Checkout completed
```

---

## Fluxos Principais

### Fluxo de Descoberta e Compra

```mermaid
sequenceDiagram
    participant U as Usuário
    participant CLI as CLI
    participant Agent as UserAgentRunner
    participant Discovery as discovery_node
    participant Shopping as shopping_node
    participant UCP as UCPClient
    participant AP2 as AP2Client
    participant Store as Loja UCP

    Note over U,Store: 1. Descoberta
    U->>CLI: "descobrir http://localhost:8182"
    CLI->>Agent: process_message()
    Agent->>Discovery: discovery_node
    Discovery->>UCP: discover()
    UCP->>Store: GET /.well-known/ucp
    Store-->>UCP: UCPProfile
    UCP-->>Discovery: Profile
    Discovery-->>Agent: {discovered_stores: {...}}
    Agent-->>CLI: "✅ Loja descoberta!"
    CLI-->>U: Resposta formatada

    Note over U,Store: 2. Busca
    U->>CLI: "buscar python"
    CLI->>Agent: process_message()
    Agent->>Discovery: discovery_node (intent=search)
    Discovery->>UCP: search_products("python")
    UCP->>Store: GET /books/search?q=python
    Store-->>UCP: Products[]
    UCP-->>Discovery: Results
    Discovery-->>Agent: {search_results: [...]}
    Agent-->>CLI: Lista formatada
    CLI-->>U: Produtos encontrados

    Note over U,Store: 3. Adicionar ao Carrinho
    U->>CLI: "adicionar 1"
    CLI->>Agent: process_message()
    Agent->>Shopping: shopping_node (intent=add_to_cart)
    Shopping->>Shopping: Adicionar item ao carrinho
    Shopping-->>Agent: {cart_items: [...], cart_total: 3990}
    Agent-->>CLI: "Adicionado! Total: R$ 39,90"
    CLI-->>U: Confirmação

    Note over U,Store: 4. Checkout com AP2
    U->>CLI: "comprar"
    CLI->>Agent: process_message()
    Agent->>Shopping: shopping_node (intent=checkout)
    Shopping->>Shopping: Preparar resumo
    Shopping-->>Agent: Pedir confirmação
    Agent-->>CLI: "Confirmar compra? Total: R$ 39,90"
    CLI-->>U: Confirmação

    U->>CLI: "sim"
    CLI->>Agent: process_message()
    Agent->>Shopping: shopping_node (intent=execute_checkout)
    Shopping->>AP2: create_intent_mandate()
    AP2-->>Shopping: intent_mandate_jwt
    Shopping->>UCP: create_checkout(cart_items)
    UCP->>Store: POST /checkout-sessions
    Store->>Store: Criar Cart Mandate
    Store-->>UCP: cart_mandate_jwt
    UCP-->>Shopping: session_id, cart_mandate_jwt
    Shopping->>AP2: create_payment_mandate(cart_mandate_jwt)
    AP2-->>Shopping: payment_mandate_jwt
    Shopping->>UCP: complete_checkout(session_id, payment_mandate_jwt)
    UCP->>Store: POST /checkout-sessions/{id}/complete
    Store-->>UCP: Success
    UCP-->>Shopping: Checkout completed
    Shopping-->>Agent: Compra concluída
    Agent-->>CLI: "✅ Compra realizada!"
    CLI-->>U: Sucesso
```

### Fluxo de Conversa A2A

```mermaid
sequenceDiagram
    participant U as Usuário
    participant Agent as UserAgentRunner
    participant Chat as chat_node
    participant A2A as A2AClient
    participant WS as WebSocket
    participant Store as Store Agent

    U->>Agent: "perguntar ao agente: tem livros de python?"
    Agent->>Chat: chat_node
    
    alt Sessão A2A não existe
        Chat->>A2A: connect(store_url)
        A2A->>WS: WebSocket connect
        WS-->>A2A: Connected
        A2A->>WS: CONNECT {agent_profile}
        WS->>Store: Processar conexão
        Store-->>WS: RESPONSE {connected}
        WS-->>A2A: Connected
        A2A-->>Chat: Sessão criada
    end
    
    Chat->>A2A: chat("tem livros de python?")
    A2A->>WS: REQUEST {action: "search", query: "python"}
    WS->>Store: Processar com Store Agents
    Store->>Store: discovery_node
    Store-->>WS: RESPONSE {products: [...]}
    WS-->>A2A: Response
    A2A-->>Chat: A2AResponse
    Chat->>Chat: Formatar resposta
    Chat-->>Agent: Mensagem formatada
    Agent-->>U: "Sim! Encontrei 5 livros sobre Python..."
```

### Fluxo Multi-Loja

```mermaid
sequenceDiagram
    participant U as Usuário
    participant Agent as UserAgentRunner
    participant Discovery as discovery_node
    participant UCP1 as UCPClient (Loja 1)
    participant UCP2 as UCPClient (Loja 2)
    participant Store1 as Loja 1
    participant Store2 as Loja 2

    Note over U,Store2: Descoberta Multi-Loja
    U->>Agent: "descobrir http://loja1:8182"
    Agent->>Discovery: discovery_node
    Discovery->>UCP1: discover()
    UCP1->>Store1: GET /.well-known/ucp
    Store1-->>UCP1: Profile
    UCP1-->>Discovery: StoreInfo
    Discovery-->>Agent: Loja 1 descoberta
    
    U->>Agent: "descobrir http://loja2:8182"
    Agent->>Discovery: discovery_node
    Discovery->>UCP2: discover()
    UCP2->>Store2: GET /.well-known/ucp
    Store2-->>UCP2: Profile
    UCP2-->>Discovery: StoreInfo
    Discovery-->>Agent: Loja 2 descoberta

    Note over U,Store2: Busca Multi-Loja
    U->>Agent: "buscar python"
    Agent->>Discovery: discovery_node
    par Busca Paralela
        Discovery->>UCP1: search_products("python")
        UCP1->>Store1: GET /books/search?q=python
        Store1-->>UCP1: Products[]
        UCP1-->>Discovery: Results Loja 1
    and
        Discovery->>UCP2: search_products("python")
        UCP2->>Store2: GET /books/search?q=python
        Store2-->>UCP2: Products[]
        UCP2-->>Discovery: Results Loja 2
    end
    Discovery->>Discovery: Agrupar resultados
    Discovery-->>Agent: {search_results: [loja1_items, loja2_items]}
    Agent-->>U: Resultados de ambas as lojas
```

---

## Configuração e Variáveis de Ambiente

### Arquivo `.env`

```bash
# LLM - Gemini (prioritário)
GOOGLE_API_KEY=sua-chave-aqui
GEMINI_MODEL=gemini-2.0-flash-lite

# LLM - Fallback
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=gpt-4-turbo-preview

# HTTP
HTTP_TIMEOUT=30.0

# A2A
A2A_RECONNECT_INTERVAL=5.0
A2A_PING_INTERVAL=30.0

# Default Stores
DEFAULT_STORES=http://localhost:8182
API_GATEWAY_URL=http://localhost:8000
UCP_SERVER_URL=http://localhost:8182

# Security
JWT_EXPIRY_SECONDS=3600
USER_KEY_ID=user-agent-key-001

# Debug
DEBUG=True
LOG_LEVEL=INFO
```

### Configurações Principais

| Categoria | Configuração | Padrão | Descrição |
|-----------|--------------|--------|-----------|
| **LLM** | `GOOGLE_API_KEY` | - | Chave da API do Google (Gemini) |
| **LLM** | `GEMINI_MODEL` | `gemini-2.0-flash-lite` | Modelo Gemini |
| **A2A** | `A2A_RECONNECT_INTERVAL` | `5.0` | Intervalo de reconexão (segundos) |
| **A2A** | `A2A_PING_INTERVAL` | `30.0` | Intervalo de ping (segundos) |
| **Security** | `USER_KEY_ID` | `user-agent-key-001` | ID da chave Ed25519 |
| **Debug** | `DEBUG` | `True` | Modo debug |

---

## Execução

### Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Ou via pip
pip install -e .
```

### Uso via CLI

```bash
# Chat interativo
user-agent chat

# Chat com loja pré-conectada
user-agent chat --store http://localhost:8182

# Chat com agente pré-conectado
user-agent chat --agent http://localhost:8000

# Descobrir loja
user-agent discover http://localhost:8182

# Buscar produtos
user-agent search python --store http://localhost:8182

# Comprar produto diretamente
user-agent buy book_001 --store http://localhost:8182 --qty 2

# Informações do agente
user-agent info
```

### Uso Programático

```python
from user_agent.src.agent import UserAgentRunner

# Criar runner
runner = UserAgentRunner()
runner.initialize(session_id="sess_123", user_name="João")

# Processar mensagem
response = await runner.process_message("buscar livros de python")
print(response)

# Verificar status
status = runner.get_status()
print(f"Lojas: {status['stores_count']}, Carrinho: {status['cart_count']}")

# Conectar a loja
await runner.connect_store_a2a("http://localhost:8182")

# Obter carrinho
cart = runner.get_cart_summary()
print(f"Total: R$ {cart['total'] / 100:.2f}")
```

---

## Integração entre Módulos

```mermaid
flowchart TB
    subgraph UserAgent["User Agent"]
        CLI["cli.py"]
        Agent["agent/"]
        Clients["clients/"]
        Security["security/"]
        Config["config.py"]
    end

    subgraph External["Externo"]
        UCPStores["Lojas UCP"]
        A2AAgents["Agentes A2A"]
        MCPServers["Servidores MCP"]
    end

    CLI --> Agent
    Agent --> Clients
    Agent --> Security
    
    Clients --> UCPStores
    Clients --> A2AAgents
    Clients --> MCPServers
    
    Security --> UCPStores
    
    Agent --> Config
    Clients --> Config
    Security --> Config
    
    style Agent fill:#e3f2fd
    style Clients fill:#fff3e0
    style Security fill:#f3e5f5
```

### Tabela de Dependências

| Módulo | Usa | Via |
|--------|-----|-----|
| **cli.py** | agent | `UserAgentRunner` |
| **agent/** | clients | `UCPClient`, `A2AClient`, `MCPClient` |
| **agent/** | security | `AP2Client`, `UserKeyManager` |
| **agent/** | config | `settings` |
| **clients/** | config | `settings` (timeouts, URLs) |
| **security/** | config | `settings` (key_id, jwt_expiry) |

---

## Logging

O User Agent usa `structlog` para logging estruturado:

```python
logger.info("Event", field1=value1, field2=value2)
logger.warning("Warning", error=error_message)
logger.error("Error", error=str(e))
```

### Eventos Logados

| Módulo | Eventos |
|--------|---------|
| **cli.py** | Comandos executados, respostas do usuário |
| **agent/** | Detecção de intenção, processamento de nodes |
| **clients/** | Requisições HTTP/WebSocket, respostas, erros |
| **security/** | Criação de mandatos, assinaturas, validações |

---

## Referências para Documentação Detalhada

### Módulos Principais

- **Agent:** [`src/agent/agent.md`](src/agent/agent.md)
  - Sistema de agentes LangGraph
  - Estado compartilhado (`UserAgentState`)
  - Nodes especializados
  - Integração com LLM

- **Clients:** [`src/clients/client.md`](src/clients/client.md)
  - UCPClient (comércio)
  - A2AClient (comunicação)
  - MCPClient (ferramentas)
  - Pool de conexões

- **Security:** [`src/security/ap2.md`](src/security/ap2.md)
  - AP2Client (mandatos JWT)
  - UserKeyManager (chaves Ed25519)
  - Fluxo de 3 mandatos

---

## Protocolos Suportados

| Protocolo | Cliente | Descrição |
|-----------|---------|-----------|
| **UCP** | `UCPClient` | Universal Commerce Protocol (comércio) |
| **A2A** | `A2AClient` | Agent-to-Agent Protocol (comunicação) |
| **MCP** | `MCPClient` | Model Context Protocol (ferramentas) |
| **AP2** | `AP2Client` | Agent Payments Protocol v2 (pagamento autônomo) |

---

## Arquitetura de Camadas

```mermaid
flowchart TB
    subgraph Layer1["Camada de Apresentação"]
        CLI["cli.py<br/>Interface CLI"]
    end
    
    subgraph Layer2["Camada de Negócio"]
        Agent["agent/<br/>UserAgentRunner + LangGraph"]
        Router["router_node<br/>Detecção de Intenção"]
        Nodes["nodes/<br/>Nodes Especializados"]
    end
    
    subgraph Layer3["Camada de Integração"]
        Clients["clients/<br/>UCP, A2A, MCP"]
    end
    
    subgraph Layer4["Camada de Infraestrutura"]
        Security["security/<br/>AP2, Keys"]
        Config["config.py<br/>Settings"]
        LLM["llm.py<br/>Gemini/OpenAI"]
    end
    
    CLI --> Agent
    Agent --> Router
    Router --> Nodes
    Nodes --> Clients
    Nodes --> Security
    Agent --> LLM
    Clients --> Config
    Security --> Config
    LLM --> Config
```

---

## Exemplos de Uso

### Exemplo 1: Descoberta e Busca

```bash
# Iniciar chat
user-agent chat

# Descobrir loja
> descobrir http://localhost:8182
✅ Loja descoberta: Livraria Virtual UCP

# Buscar produtos
> buscar python
📚 Encontrei 5 livros sobre Python:
1. Python para Todos - R$ 39,90
2. Clean Code em Python - R$ 49,90
...

# Adicionar ao carrinho
> adicionar 1
✅ Adicionado! Total: R$ 39,90
```

### Exemplo 2: Compra Autônoma com AP2

```bash
# Ver carrinho
> carrinho
🛒 Carrinho:
  Python para Todos x1 - R$ 39,90
  TOTAL: R$ 39,90

# Finalizar compra
> comprar
📋 Resumo da Compra:
  Total: R$ 39,90
  Confirmar? (sim/não)

> sim
🔐 Gerando mandato AP2...
💳 Processando pagamento...
✅ Compra realizada! Pedido #12345
```

### Exemplo 3: Conversa A2A

```bash
# Descobrir agente
> descobrir agente http://localhost:8000
✅ Agente descoberto: Livraria Virtual UCP
Skills: search, recommend, checkout

# Conversar com agente
> perguntar ao agente: tem livros de machine learning?
🤖 Store Agent: Sim! Encontrei 3 livros sobre Machine Learning...
```

---

## Referências

- **Documentação dos Módulos:**
  - [`src/agent/agent.md`](src/agent/agent.md) - Agente Principal (LangGraph)
  - [`src/clients/client.md`](src/clients/client.md) - Clientes de Protocolo (UCP, A2A, MCP)
  - [`src/security/ap2.md`](src/security/ap2.md) - Segurança AP2 (3 Mandatos)
  - [`src/wallet/wallet.md`](src/wallet/wallet.md) - Carteira Virtual

- **Documentação Externa:**
  - [`../backend/src/src.md`](../backend/src/src.md) - Backend (lojas UCP)
  - [`../docs/architecture/`](../docs/architecture/) - Arquitetura geral

- **Especificações:**
  - Universal Commerce Protocol (UCP)
  - Agent-to-Agent Protocol (A2A)
  - Model Context Protocol (MCP)
  - Agent Payments Protocol v2 (AP2)
