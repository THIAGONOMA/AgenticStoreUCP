# Backend Source - Código Fonte do Backend

Este diretório contém todo o código fonte do backend da Livraria Virtual UCP. O backend implementa múltiplos protocolos (UCP, A2A, MCP, AP2) usando **SDKs oficiais** e fornece APIs REST, WebSocket e endpoints de discovery.

## Visão Geral

O backend é composto por **6 módulos principais**:

| Módulo | Descrição | Porta | SDK Oficial |
|--------|-----------|-------|-------------|
| **API Gateway** | Entry point principal (main.py) | 8000 | - |
| **UCP Server** | Servidor Universal Commerce Protocol | 8182 | ✅ `ucp-python` |
| **MCP Server** | Model Context Protocol (via HTTP) | Integrado | ✅ `mcp` (FastMCP) |
| **Agents** | Store Agents (LangGraph) + A2A | Via WebSocket | ✅ `a2a-sdk` |
| **Database** | Camada de persistência SQLite | - | - |
| **Security** | AP2 Security e assinaturas | - | ✅ `ap2` (Google) |

---

## SDKs Oficiais Integrados

| Protocolo | SDK | Repositório | Localização |
|-----------|-----|-------------|-------------|
| **UCP** | `ucp-python` | Universal-Commerce-Protocol/python-sdk | `sdk/ucp-python/` |
| **A2A** | `a2a-sdk` | a2aproject/a2a-python | PyPI |
| **AP2** | `ap2` | google-agentic-commerce/AP2 | `sdk/ap2-repo/` |
| **MCP** | `mcp` (FastMCP) | modelcontextprotocol/python-sdk | PyPI |

---

## Arquitetura do Backend

```
backend/src/
├── __init__.py          # Versão do backend
├── main.py              # API Gateway (porta 8000)
├── config.py            # Configurações
├── src.md               # Esta documentação
│
├── agents/              # Store Agents (LangGraph + A2A SDK)
│   ├── agents.md        # → Documentação completa
│   ├── a2a/
│   │   └── a2a.md      # → Protocolo A2A (SDK oficial)
│   └── nodes/
│       └── nodes.md     # → Agent Nodes
│
├── db/                  # Camada de Persistência
│   └── db.md            # → Documentação completa
│
├── mcp/                 # Model Context Protocol (SDK oficial)
│   ├── mcp.md           # → Documentação completa
│   └── tools/
│       └── tools.md      # → Ferramentas MCP
│
├── security/            # Segurança AP2 (SDK oficial Google)
│   ├── security.md      # → Documentação completa
│   ├── ap2_types.py     # → Tipos oficiais AP2
│   └── ap2_adapters.py  # → Adaptadores AP2
│
└── ucp_server/          # UCP Server (SDK oficial)
    ├── ucp.md            # → Documentação completa
    ├── capabilities/
    │   └── capabilities.md  # → Capabilities UCP
    ├── models/
    │   └── models.md        # → Modelos Pydantic
    ├── routes/
    │   └── routes.md         # → Rotas HTTP
    └── services/
        └── services.md       # → Serviços UCP
```

### Diagrama de Arquitetura Completo

```mermaid
flowchart TB
    subgraph Clients["Clientes"]
        Browser["Browser<br/>(Frontend)"]
        AIAgent["AI Agent<br/>(UCP/A2A)"]
        MCPClient["MCP Client"]
    end

    subgraph SDKs["SDKs Oficiais"]
        UCPSDK["ucp-python<br/>sdk/ucp-python/"]
        A2ASDK["a2a-sdk<br/>PyPI"]
        AP2SDK["ap2<br/>sdk/ap2-repo/"]
        MCPSDK["mcp (FastMCP)<br/>PyPI"]
    end

    subgraph Backend["Backend Source"]
        subgraph Gateway["API Gateway :8000"]
            Main["main.py<br/>FastAPI App"]
            A2ADiscovery["/.well-known/agent.json<br/>Discovery A2A"]
            ChatWS["/ws/chat<br/>WebSocket"]
            A2AWS["/ws/a2a<br/>WebSocket"]
            REST["/api/*<br/>REST API"]
        end
        
        subgraph UCP["UCP Server :8182"]
            UCPServer["ucp_server/server.py"]
            Discovery["/.well-known/ucp"]
            UCPRoutes["routes/"]
        end
        
        subgraph Agents["Store Agents"]
            Runner["store_agent_runner"]
            Graph["LangGraph"]
            Nodes["nodes/"]
            A2A["a2a/ (SDK)"]
        end
        
        subgraph MCP["MCP Module"]
            MCPServer["mcp/server.py"]
            Tools["tools/"]
        end
        
        subgraph Data["Data Layer"]
            DB["db/<br/>Repositories"]
            Models["ucp_server/models/"]
        end
        
        subgraph Security["Security (SDK Google)"]
            AP2["security/<br/>AP2 Security"]
            AP2Types["ap2_types.py"]
            AP2Adapt["ap2_adapters.py"]
        end
    end

    Browser --> Main
    AIAgent --> Discovery
    AIAgent --> A2ADiscovery
    AIAgent --> A2AWS
    MCPClient --> MCPServer
    
    Main --> ChatWS
    Main --> A2AWS
    Main --> REST
    
    ChatWS --> Runner
    A2AWS --> A2A
    REST --> UCPRoutes
    
    Runner --> Graph
    Graph --> Nodes
    A2A --> Runner
    A2A --> A2ASDK
    
    UCPRoutes --> Models
    UCPRoutes --> DB
    UCPRoutes --> AP2
    Models --> UCPSDK
    
    MCPServer --> Tools
    MCPServer --> MCPSDK
    Tools --> DB
    
    Nodes --> DB
    AP2 --> AP2Types
    AP2 --> AP2Adapt
    AP2Types --> AP2SDK
    
    style Gateway fill:#e3f2fd
    style UCP fill:#fff3e0
    style Agents fill:#e8f5e9
    style MCP fill:#fce4ec
    style SDKs fill:#f3e5f5
```

---

## Componentes Principais

### 1. API Gateway (`main.py`)

Entry point principal que orquestra todas as funcionalidades.

#### Estrutura do App

```mermaid
flowchart TD
    subgraph App["FastAPI App (main.py)"]
        subgraph Endpoints["Endpoints REST"]
            Health["GET /health"]
            BooksAPI["GET /api/books"]
            ChatAPI["POST /api/chat"]
            A2AAPI["POST /api/a2a"]
            UCPProxy["POST /api/ucp/checkout-sessions"]
        end
        
        subgraph WebSockets["WebSockets"]
            ChatWS["/ws/chat"]
            A2AWS["/ws/a2a"]
        end
        
        subgraph Manager["ConnectionManager"]
            ChatConn["chat_connections"]
            A2AConn["a2a_connections"]
        end
    end
    
    ChatWS --> Manager
    A2AWS --> Manager
    
    ChatWS --> Runner["store_agent_runner"]
    A2AWS --> Handler["a2a_handler"]
    
    UCPProxy --> UCPServer["UCP Server :8182"]
```

#### Endpoints Principais

| Endpoint | Método | Tipo | Descrição |
|----------|--------|------|-----------|
| `/health` | GET | REST | Health check |
| `/.well-known/agent.json` | GET | REST | Discovery endpoint A2A |
| `/api/books` | GET | REST | Listar livros |
| `/api/books/search` | GET | REST | Buscar livros |
| `/api/chat` | POST | REST | Chat com Store Agents |
| `/api/a2a` | POST | REST | Requisição A2A |
| `/api/a2a/agents` | GET | REST | Listar agentes conectados |
| `/api/ucp/checkout-sessions` | POST | REST | Proxy para UCP Server |
| `/ws/chat` | WebSocket | WS | Chat em tempo real |
| `/ws/a2a` | WebSocket | WS | Comunicação A2A |

#### Fluxo de Chat WebSocket

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Runner as store_agent_runner
    participant Graph as LangGraph

    Client->>Gateway: WebSocket /ws/chat
    Gateway->>Gateway: manager.connect_chat()
    Gateway-->>Client: {type: "connected", session_id}

    Client->>Gateway: {message: "Buscar Python"}
    Gateway->>Runner: process_message(session_id, message)
    Runner->>Graph: store_graph.ainvoke(state)
    Graph-->>Runner: result
    Runner-->>Gateway: {response, cart_items, ...}
    Gateway-->>Client: JSON response
```

#### Fluxo de A2A WebSocket

```mermaid
sequenceDiagram
    participant Agent as External Agent
    participant Gateway as API Gateway
    participant Handler as a2a_handler
    participant Runner as store_agent_runner

    Agent->>Gateway: WebSocket /ws/a2a
    Gateway->>Gateway: manager.connect_a2a()
    
    Agent->>Gateway: {type: "a2a.request", action: "search", payload: {...}}
    Gateway->>Handler: handle_message(message, session_id)
    Handler->>Runner: process_a2a_request(...)
    Runner-->>Handler: result
    Handler-->>Gateway: A2AMessage response
    Gateway-->>Agent: JSON response
```

---

### 2. Configurações (`config.py`)

Configurações centralizadas usando Pydantic Settings.

#### Configurações Disponíveis

| Categoria | Configuração | Padrão | Descrição |
|-----------|--------------|--------|-----------|
| **Server** | `api_port` | 8000 | Porta do API Gateway |
| **Server** | `ucp_port` | 8182 | Porta do UCP Server |
| **Database** | `products_db_path` | `./data/products.db` | Path do banco de produtos |
| **Database** | `transactions_db_path` | `./data/transactions.db` | Path do banco de transações |
| **Security** | `ap2_key_id` | `livraria-key-001` | ID da chave AP2 |
| **Security** | `jwt_expiry_seconds` | 3600 | Expiração de JWT (1 hora) |
| **LLM** | `google_api_key` | - | Chave da API Gemini |
| **Debug** | `debug` | `True` | Modo debug |
| **Debug** | `log_level` | `INFO` | Nível de log |

#### Carregamento de Configurações

```mermaid
flowchart TD
    Start([Settings]) --> EnvFile[Carregar .env]
    EnvFile --> EnvVars[Variáveis de ambiente]
    EnvVars --> Merge[Mesclar com defaults]
    Merge --> Settings["settings: Settings"]
```

---

## Módulos Documentados

### Agents

📄 **Documentação:** [`agents/agents.md`](agents/agents.md)

Sistema de agentes inteligentes usando LangGraph e **A2A SDK oficial**:

- **State** - Estado compartilhado entre agentes
- **Graph** - Grafo LangGraph orquestrador
- **Nodes** - Agentes especializados (Discovery, Shopping, Recommend)
- **A2A** - Comunicação Agent-to-Agent (SDK oficial)

📄 **Submódulos:**
- [`agents/a2a/a2a.md`](agents/a2a/a2a.md) - Protocolo Agent-to-Agent (SDK oficial)
- [`agents/nodes/nodes.md`](agents/nodes/nodes.md) - Agent Nodes detalhados

```mermaid
flowchart LR
    subgraph Agents["agents/"]
        Runner["store_agent_runner"]
        Graph["LangGraph"]
        Nodes["nodes/"]
        A2A["a2a/ (SDK)"]
    end
    
    subgraph SDK["SDK Oficial"]
        A2ASDK["a2a-sdk"]
    end
    
    Runner --> Graph
    Graph --> Nodes
    A2A --> Runner
    A2A --> A2ASDK
```

---

### Database

📄 **Documentação:** [`db/db.md`](db/db.md)

Camada de persistência SQLite:

- **Database** - Gerenciador de conexões
- **ProductsRepository** - Operações com livros (inclui controle de estoque)
- **DiscountsRepository** - Operações com cupons
- **TransactionsRepository** - Operações com checkout

```mermaid
flowchart LR
    subgraph DB["db/"]
        ProductsRepo["products_repo"]
        DiscountsRepo["discounts_repo"]
        TransactionsRepo["transactions_repo"]
    end
    
    ProductsRepo --> ProductsDB[(products.db)]
    DiscountsRepo --> ProductsDB
    TransactionsRepo --> TransactionsDB[(transactions.db)]
```

---

### MCP

📄 **Documentação:** [`mcp/mcp.md`](mcp/mcp.md)

Model Context Protocol usando **SDK oficial** (FastMCP):

- **MCP Server** - Servidor MCP principal (FastMCP)
- **HTTP Server** - API REST para MCP
- **Tool Registry** - Registro de ferramentas
- **Progressive Disclosure** - Revelação gradual

📄 **Submódulo:**
- [`mcp/tools/tools.md`](mcp/tools/tools.md) - 7 ferramentas MCP

```mermaid
flowchart LR
    subgraph MCP["mcp/"]
        Server["mcp_server"]
        HTTP["http_server"]
        Tools["tools/"]
    end
    
    subgraph SDK["SDK Oficial"]
        FastMCP["mcp (FastMCP)"]
    end
    
    Server --> Tools
    HTTP --> Server
    Server --> FastMCP
```

---

### Security

📄 **Documentação:** [`security/security.md`](security/security.md)

Segurança AP2 usando **SDK oficial do Google**:

- **AP2Security** - Orquestrador de mandatos (IntentMandate, CartMandate, PaymentMandate)
- **ap2_types** - Tipos oficiais re-exportados do SDK
- **ap2_adapters** - Funções de conversão e assinatura
- **KeyManager** - Gerenciamento de chaves Ed25519
- **RequestSigner** - Assinaturas de requisições UCP

```mermaid
flowchart LR
    subgraph Security["security/"]
        AP2["AP2Security"]
        Types["ap2_types.py"]
        Adapters["ap2_adapters.py"]
        Keys["KeyManager"]
        Signer["RequestSigner"]
    end
    
    subgraph SDK["SDK Oficial"]
        GoogleAP2["ap2 (Google)"]
    end
    
    AP2 --> Types
    AP2 --> Adapters
    Types --> GoogleAP2
    Adapters --> Keys
    Signer --> Keys
```

#### Fluxo de Mandatos AP2

```mermaid
flowchart LR
    Intent["1. IntentMandate<br/>(Intenção do usuário)"]
    Cart["2. CartMandate<br/>(Merchant assina)"]
    Payment["3. PaymentMandate<br/>(Usuário autoriza)"]
    Settlement["4. Settlement<br/>(Pagamento)"]
    
    Intent --> Cart --> Payment --> Settlement
```

---

### UCP Server

📄 **Documentação:** [`ucp_server/ucp.md`](ucp_server/ucp.md)

Servidor Universal Commerce Protocol usando **SDK oficial**:

- **Server** - FastAPI app do UCP Server
- **Discovery** - Endpoint `/.well-known/ucp`
- **Routes** - Endpoints HTTP REST
- **Models** - Modelos Pydantic (SDK oficial)
- **Capabilities** - Capabilities UCP
- **Services** - Serviços UCP

📄 **Submódulos:**
- [`ucp_server/capabilities/capabilities.md`](ucp_server/capabilities/capabilities.md) - Capabilities (checkout, discount, fulfillment)
- [`ucp_server/models/models.md`](ucp_server/models/models.md) - Modelos Pydantic
- [`ucp_server/routes/routes.md`](ucp_server/routes/routes.md) - Rotas HTTP
- [`ucp_server/services/services.md`](ucp_server/services/services.md) - Serviços e payment handlers

```mermaid
flowchart TB
    subgraph UCP["ucp_server/"]
        Server["server.py"]
        Discovery["discovery.py"]
        Routes["routes/"]
        Models["models/"]
        Capabilities["capabilities/"]
        Services["services/"]
    end
    
    subgraph SDK["SDK Oficial"]
        UCPSDK["ucp-python"]
    end
    
    Server --> Discovery
    Server --> Routes
    Routes --> Models
    Models --> UCPSDK
    Discovery --> Capabilities
    Discovery --> Services
```

---

## Fluxo de Requisição Completo

### Fluxo de Discovery A2A

```mermaid
sequenceDiagram
    participant Agent as External Agent
    participant Gateway as API Gateway
    participant Adapters as adapters.py (SDK)

    Agent->>Gateway: GET /.well-known/agent.json
    Gateway->>Adapters: get_store_agent_card()
    Adapters-->>Gateway: AgentCard JSON (SDK A2A)
    Gateway-->>Agent: {name, skills, capabilities, url}
    
    Note over Agent,Gateway: Agente descobre capacidades<br/>sem precisar conectar WebSocket
```

### Fluxo de Compra via UCP com AP2

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant Gateway as API Gateway
    participant UCP as UCP Server
    participant DB as Database
    participant AP2 as AP2 Security (SDK)

    Agent->>UCP: GET /.well-known/ucp
    UCP-->>Agent: {capabilities, services, payment, ap2}

    Agent->>Gateway: POST /api/ucp/checkout-sessions
    Gateway->>UCP: POST /checkout-sessions
    UCP->>DB: Criar sessão
    DB-->>UCP: CheckoutSession
    UCP-->>Gateway: CheckoutSession
    Gateway-->>Agent: CheckoutSession

    Note over Agent,AP2: Fluxo AP2 com 3 Mandatos

    Agent->>AP2: create_intent_mandate()
    AP2-->>Agent: IntentMandate
    
    Agent->>AP2: create_cart_mandate()
    AP2->>AP2: Assinar com Ed25519
    AP2-->>Agent: CartMandate (JWT)
    
    Agent->>AP2: create_payment_mandate()
    AP2-->>Agent: PaymentMandate

    Agent->>Gateway: POST /api/ucp/checkout-sessions/{id}/complete
    Gateway->>UCP: POST /checkout-sessions/{id}/complete
    UCP->>AP2: validate_cart_mandate(jwt)
    AP2-->>UCP: {valid: true}
    UCP->>DB: complete_session() + decrement_stock()
    UCP-->>Gateway: CheckoutSession (completed)
    Gateway-->>Agent: CheckoutSession (completed)
```

### Fluxo de Chat com Store Agents

```mermaid
sequenceDiagram
    participant User as Usuário
    participant Gateway as API Gateway
    participant Runner as store_agent_runner
    participant Graph as LangGraph
    participant DB as Database

    User->>Gateway: WebSocket /ws/chat
    Gateway-->>User: Connected

    User->>Gateway: {message: "Buscar Python"}
    Gateway->>Runner: process_message(session_id, message)
    Runner->>Graph: store_graph.ainvoke(state)
    Graph->>Graph: orchestrator_node
    Graph->>Graph: discovery_node
    Graph->>DB: products_repo.search("python")
    DB-->>Graph: books[]
    Graph-->>Runner: result
    Runner-->>Gateway: {response, search_results}
    Gateway-->>User: JSON response
```

---

## Integração entre Módulos

```mermaid
flowchart TB
    subgraph Backend["Backend Source"]
        Gateway["main.py<br/>API Gateway"]
        UCP["ucp_server/<br/>UCP Server"]
        Agents["agents/<br/>Store Agents"]
        MCP["mcp/<br/>MCP Server"]
        DB["db/<br/>Database"]
        Security["security/<br/>AP2 Security"]
    end

    subgraph SDKs["SDKs Oficiais"]
        UCPSDK["ucp-python"]
        A2ASDK["a2a-sdk"]
        AP2SDK["ap2 (Google)"]
        MCPSDK["mcp (FastMCP)"]
    end

    Gateway --> Agents
    Gateway --> UCP
    Gateway --> MCP
    
    UCP --> DB
    UCP --> Security
    UCP --> UCPSDK
    
    Agents --> DB
    Agents --> UCP
    Agents --> A2ASDK
    
    MCP --> DB
    MCP --> MCPSDK
    
    Security --> AP2SDK
    
    style Gateway fill:#e3f2fd
    style UCP fill:#fff3e0
    style Agents fill:#e8f5e9
    style MCP fill:#fce4ec
    style SDKs fill:#f3e5f5
```

### Tabela de Dependências

| Módulo | Usa | Via | SDK |
|--------|-----|-----|-----|
| **main.py** | agents | `store_agent_runner`, `a2a_handler` | a2a-sdk |
| **main.py** | ucp_server | HTTP proxy (`httpx`) | - |
| **ucp_server** | db | `products_repo`, `transactions_repo`, `discounts_repo` | - |
| **ucp_server** | security | `get_ap2_security()` | ap2 |
| **ucp_server** | models | Modelos Pydantic | ucp-python |
| **agents** | db | `products_repo`, `transactions_repo`, `discounts_repo` | - |
| **agents** | a2a | `adapters.py` | a2a-sdk |
| **mcp** | db | `products_repo`, `discounts_repo` | - |
| **mcp** | server | FastMCP | mcp |

---

## Inicialização do Backend

### Startup Sequence

```mermaid
sequenceDiagram
    participant Main as main.py
    participant UCP as ucp_server
    participant DB as Database

    Main->>DB: init_databases()
    Main->>DB: products_db.connect()
    Main->>DB: transactions_db.connect()
    Main->>Main: API Gateway ready (port 8000)

    UCP->>DB: init_databases()
    UCP->>DB: products_db.connect()
    UCP->>DB: transactions_db.connect()
    UCP->>UCP: UCP Server ready (port 8182)
```

### Shutdown Sequence

```mermaid
sequenceDiagram
    participant Main as main.py
    participant UCP as ucp_server
    participant DB as Database

    Main->>DB: products_db.disconnect()
    Main->>DB: transactions_db.disconnect()
    Main->>Main: API Gateway stopped

    UCP->>DB: products_db.disconnect()
    UCP->>DB: transactions_db.disconnect()
    UCP->>UCP: UCP Server stopped
```

---

## Endpoints Principais

### API Gateway (porta 8000)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/health` | GET | Health check |
| `/.well-known/agent.json` | GET | Discovery endpoint A2A (AgentCard) |
| `/api/books` | GET | Listar livros |
| `/api/books/search` | GET | Buscar livros |
| `/api/books/{book_id}` | GET | Obter livro |
| `/api/chat` | POST | Chat REST |
| `/api/a2a` | POST | A2A REST |
| `/api/a2a/agents` | GET | Listar agentes |
| `/api/ucp/checkout-sessions` | POST | Proxy UCP |
| `/ws/chat` | WebSocket | Chat em tempo real |
| `/ws/a2a` | WebSocket | A2A em tempo real |

### UCP Server (porta 8182)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/.well-known/ucp` | GET | Discovery endpoint (inclui AP2 info) |
| `/health` | GET | Health check |
| `/books/*` | GET | Rotas de catálogo |
| `/checkout-sessions/*` | POST, GET, PUT, DELETE | Rotas de checkout |
| `/mcp/*` | GET, POST | Rotas MCP |

---

## Configuração e Variáveis de Ambiente

### Arquivo `.env`

```bash
# Servers
API_PORT=8000
UCP_PORT=8182

# Database
PRODUCTS_DB_PATH=./data/products.db
TRANSACTIONS_DB_PATH=./data/transactions.db

# Security
AP2_KEY_ID=livraria-key-001
JWT_EXPIRY_SECONDS=3600

# LLM (Gemini)
GOOGLE_API_KEY=AIza...

# Debug
DEBUG=True
LOG_LEVEL=INFO
```

---

## Logging

O backend usa `structlog` para logging estruturado em todos os módulos:

```python
logger.info("Event", field1=value1, field2=value2)
logger.warning("Warning", error=error_message)
logger.error("Error", error=str(e))
```

### Eventos Logados

| Módulo | Eventos |
|--------|---------|
| **main.py** | Chat messages, A2A messages, UCP proxy requests |
| **ucp_server** | Discovery requests, checkout operations, AP2 validation |
| **agents** | Intent detection (LLM), node processing, A2A requests |
| **mcp** | Tool calls, progressive disclosure upgrades |
| **security** | Mandate creation, JWT signing, validation |

---

## Referências para Documentação Detalhada

### Módulos Principais

- **Agents:** [`agents/agents.md`](agents/agents.md)
  - Sistema de agentes LangGraph
  - Submódulos: [`a2a/a2a.md`](agents/a2a/a2a.md), [`nodes/nodes.md`](agents/nodes/nodes.md)

- **Database:** [`db/db.md`](db/db.md)
  - Camada de persistência SQLite
  - Repositories e gerenciamento de conexões

- **MCP:** [`mcp/mcp.md`](mcp/mcp.md)
  - Model Context Protocol (SDK oficial)
  - Submódulo: [`tools/tools.md`](mcp/tools/tools.md)

- **Security:** [`security/security.md`](security/security.md)
  - AP2 Security (SDK oficial Google)
  - Fluxo de 3 mandatos: Intent → Cart → Payment

- **UCP Server:** [`ucp_server/ucp.md`](ucp_server/ucp.md)
  - Servidor Universal Commerce Protocol (SDK oficial)
  - Submódulos:
    - [`capabilities/capabilities.md`](ucp_server/capabilities/capabilities.md)
    - [`models/models.md`](ucp_server/models/models.md)
    - [`routes/routes.md`](ucp_server/routes/routes.md)
    - [`services/services.md`](ucp_server/services/services.md)

---

## Execução

### Iniciar Backend Completo

```bash
# Terminal 1: API Gateway
uvicorn backend.src.main:app --host 0.0.0.0 --port 8000

# Terminal 2: UCP Server
uvicorn backend.src.ucp_server.server:app --host 0.0.0.0 --port 8182
```

### Usando Scripts

```bash
# Executar tudo
./scripts/start_backend.sh

# Ou via Makefile
make run-backend

# Demo AP2 (fluxo de 3 mandatos)
make demo-ap2
```

---

## Estrutura de Dados

### Bancos de Dados

| Banco | Path | Tabelas |
|-------|------|---------|
| **products.db** | `./data/products.db` | books (com stock), discount_codes |
| **transactions.db** | `./data/transactions.db` | buyers, checkout_sessions, line_items, applied_discounts, payments |

📄 **Documentação:** [`../data/data.md`](../data/data.md)

---

## Protocolos Implementados

| Protocolo | Endpoint | SDK Oficial | Descrição |
|-----------|----------|-------------|-----------|
| **UCP** | `/.well-known/ucp` | ✅ ucp-python | Universal Commerce Protocol |
| **A2A** | `/.well-known/agent.json` | ✅ a2a-sdk | Discovery endpoint A2A (AgentCard) |
| **A2A** | `/ws/a2a` | ✅ a2a-sdk | Agent-to-Agent Communication (WebSocket) |
| **MCP** | `/mcp/*` | ✅ mcp (FastMCP) | Model Context Protocol |
| **AP2** | Via checkout | ✅ ap2 (Google) | Agent Payments Protocol v2 |
| **REST** | `/api/*` | - | API REST padrão |
| **WebSocket** | `/ws/*` | - | Comunicação em tempo real |

---

## Arquitetura de Camadas

```mermaid
flowchart TB
    subgraph Layer1["Camada de Apresentação"]
        Gateway["main.py<br/>API Gateway"]
        UCPRoutes["ucp_server/routes/"]
    end
    
    subgraph Layer2["Camada de Negócio"]
        Agents["agents/<br/>Store Agents"]
        UCPServices["ucp_server/services/"]
        Discovery["ucp_server/discovery.py"]
    end
    
    subgraph Layer3["Camada de Dados"]
        Models["ucp_server/models/"]
        DB["db/<br/>Repositories"]
    end
    
    subgraph Layer4["Camada de Infraestrutura"]
        Security["security/<br/>AP2 (SDK Google)"]
        Capabilities["ucp_server/capabilities/"]
        MCP["mcp/<br/>MCP (SDK FastMCP)"]
    end
    
    subgraph Layer5["SDKs Oficiais"]
        SDKs["ucp-python | a2a-sdk | ap2 | mcp"]
    end
    
    Gateway --> Agents
    Gateway --> UCPRoutes
    UCPRoutes --> UCPServices
    UCPServices --> Models
    Agents --> Models
    Models --> DB
    UCPServices --> Security
    Discovery --> Capabilities
    Gateway --> MCP
    
    Security --> SDKs
    Models --> SDKs
    MCP --> SDKs
```

---

## Referências

- **Documentação dos Módulos:**
  - [`agents/agents.md`](agents/agents.md)
  - [`agents/a2a/a2a.md`](agents/a2a/a2a.md)
  - [`agents/nodes/nodes.md`](agents/nodes/nodes.md)
  - [`db/db.md`](db/db.md)
  - [`mcp/mcp.md`](mcp/mcp.md)
  - [`mcp/tools/tools.md`](mcp/tools/tools.md)
  - [`security/security.md`](security/security.md)
  - [`ucp_server/ucp.md`](ucp_server/ucp.md)
  - [`ucp_server/capabilities/capabilities.md`](ucp_server/capabilities/capabilities.md)
  - [`ucp_server/models/models.md`](ucp_server/models/models.md)
  - [`ucp_server/routes/routes.md`](ucp_server/routes/routes.md)
  - [`ucp_server/services/services.md`](ucp_server/services/services.md)

- **Documentação Externa:**
  - [`../data/data.md`](../data/data.md) - Dados e bancos de dados
  - [`../docs/techSpec.md`](../docs/techSpec.md) - Especificação técnica completa

- **SDKs Oficiais:**
  - UCP: https://github.com/Universal-Commerce-Protocol/python-sdk
  - A2A: https://github.com/a2aproject/a2a-python
  - AP2: https://github.com/google-agentic-commerce/AP2
  - MCP: https://github.com/modelcontextprotocol/python-sdk
