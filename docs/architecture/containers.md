# C4 Level 2: Diagrama de Containers

## Visao Geral

O diagrama de containers mostra as aplicacoes e servicos que compoem o sistema, incluindo o **User Agent** como um container externo que interage com a loja.

## Diagrama de Containers Completo

```mermaid
flowchart TB
    subgraph user_env [Ambiente do Usuario]
        UserAgent[User Agent<br/>Python + LangGraph]
        UserCLI[CLI Interface]
        UserLLM[LLM Client]
    end

    subgraph store_system [Livraria Virtual UCP]
        subgraph frontend_container [Frontend]
            ReactApp[React App<br/>TypeScript + Vite]
        end

        subgraph backend_containers [Backend]
            APIGateway[API Gateway<br/>FastAPI :8000]
            UCPServer[UCP Server<br/>FastAPI :8182]
            MCPServer[MCP Server<br/>FastMCP :8183]
            StoreAgents[Store Agents<br/>LangGraph]
        end

        subgraph data_layer [Data Layer]
            ProductsDB[(products.db)]
            TransactionsDB[(transactions.db)]
        end
    end

    subgraph external [Provedores LLM]
        Gemini[Google Gemini<br/>gemini-2.0-flash-lite]
        OpenAI[OpenAI<br/>gpt-4o-mini - fallback]
        Anthropic[Anthropic<br/>claude-3-haiku - fallback]
    end

    subgraph other_stores [Outras Lojas]
        OtherStores[Outras Lojas UCP]
    end

    UserCLI --> UserAgent
    UserAgent --> UserLLM
    UserLLM --> Gemini
    UserLLM -.-> OpenAI
    UserLLM -.-> Anthropic

    UserAgent -->|UCP Protocol| UCPServer
    UserAgent -->|A2A Protocol| StoreAgents
    UserAgent -->|MCP Protocol| MCPServer
    UserAgent -->|UCP Protocol| OtherStores

    ReactApp --> APIGateway
    APIGateway --> StoreAgents
    StoreAgents --> MCPServer
    MCPServer --> UCPServer
    UCPServer --> ProductsDB
    UCPServer --> TransactionsDB
    StoreAgents --> Gemini
```

## Containers Detalhados

### User Agent Container (Agente Autonomo)

O **User Agent** e um agente autonomo que o usuario executa em seu ambiente para interagir com lojas UCP. Possui CLI interativa com Typer/Rich e suporte a multiplos provedores LLM.

```mermaid
flowchart TB
    subgraph user_agent [User Agent Container]
        subgraph interface [Interface Layer]
            CLI[CLI Interface<br/>Typer + Rich]
            Commands[Commands<br/>discover, buy, chat, status]
        end

        subgraph agent_core [Agent Core - LangGraph]
            MainGraph[StateGraph<br/>shopping_graph]
            DiscoveryNode[discovery_node<br/>Lista lojas UCP]
            ShoppingNode[shopping_node<br/>Busca + Carrinho]
            CheckoutNode[checkout_node<br/>AP2 + Pagamento]
            ResponseNode[response_node<br/>LLM Response]
        end

        subgraph llm [LLM Module]
            LLMClient[LLMClient<br/>Multi-provider]
            Gemini[Google Gemini<br/>gemini-2.0-flash-lite]
            OpenAI[OpenAI Fallback<br/>gpt-4o-mini]
            Anthropic[Anthropic<br/>claude-3-haiku]
        end

        subgraph clients [Protocol Clients]
            UCPClient[UCPClient<br/>httpx + UCP SDK]
            A2AClient[A2AClient<br/>WebSocket + SDK]
            MCPClient[MCPClient<br/>MCP Protocol]
            AP2Client[AP2Security<br/>Ed25519 + JWT]
        end

        subgraph state [State Management]
            AgentState[AgentState<br/>TypedDict]
            StoresRegistry[stores: Dict]
            Cart[cart: List]
            Messages[messages: List]
        end
    end

    CLI --> Commands
    Commands --> MainGraph
    
    MainGraph --> DiscoveryNode
    MainGraph --> ShoppingNode
    MainGraph --> CheckoutNode
    MainGraph --> ResponseNode

    DiscoveryNode --> UCPClient
    DiscoveryNode --> A2AClient
    ShoppingNode --> UCPClient
    ShoppingNode --> MCPClient
    CheckoutNode --> UCPClient
    CheckoutNode --> AP2Client
    ResponseNode --> LLMClient

    LLMClient --> Gemini
    LLMClient -.-> OpenAI
    LLMClient -.-> Anthropic

    UCPClient --> AgentState
    ShoppingNode --> Cart
    MainGraph --> Messages
```

| Aspecto | Descricao |
|---------|-----------|
| **Tecnologia** | Python 3.11 + LangGraph 0.2 |
| **Interface** | CLI Typer + Rich (console formatado) |
| **LLM Principal** | Google Gemini (gemini-2.0-flash-lite) |
| **LLM Fallback** | OpenAI (gpt-4o-mini) ou Anthropic (claude-3-haiku) |
| **Responsabilidades** | Descobrir lojas, comparar precos, executar compras autonomas |
| **Comunicacao** | UCP, A2A, MCP, AP2 |
| **Documentacao** | [user_agent/userAgent.md](../../user_agent/userAgent.md) |

### Store Agents Container (Backend Agentico)

Os Store Agents sao agentes da loja que processam requisicoes de usuarios e de outros agentes (A2A). Incluem integracao com LLM para processamento de linguagem natural.

```mermaid
flowchart TB
    subgraph store_agents [Store Agents Container]
        subgraph orchestration [Orchestration - LangGraph]
            MainOrchestrator[Main Orchestrator<br/>StateGraph]
            A2AHandler[A2AAdapter<br/>google.adk]
            IntentRouter[Intent Router]
        end

        subgraph llm_module [LLM Module]
            LLMClient[LLMClient<br/>google.genai]
            IntentDetector[Intent Detector]
            ResponseGen[Response Generator]
        end

        subgraph internal_agents [Internal Agents - Nodes]
            DiscoveryAgent[discovery_agent<br/>Lista produtos]
            ShoppingAgent[shopping_agent<br/>Carrinho + Compra]
            RecommendAgent[recommend_agent<br/>Sugestoes LLM]
        end

        subgraph external_interface [External Interface]
            A2AEndpoint[A2A Endpoint<br/>WebSocket + HTTP]
            AgentAuth[AP2 Authentication<br/>Ed25519 + JWT]
        end
    end

    A2AEndpoint --> A2AHandler
    A2AHandler --> AgentAuth
    AgentAuth --> MainOrchestrator
    MainOrchestrator --> IntentRouter
    IntentRouter --> LLMClient
    LLMClient --> IntentDetector
    IntentRouter --> DiscoveryAgent
    IntentRouter --> ShoppingAgent
    IntentRouter --> RecommendAgent
    RecommendAgent --> ResponseGen
```

| Aspecto | Descricao |
|---------|-----------|
| **Tecnologia** | Python 3.11 + LangGraph 0.2 |
| **LLM** | Google Gemini (via google-genai) |
| **A2A** | Google ADK (google-adk) |
| **Responsabilidades** | Processar requests humanos e A2A, gerar recomendacoes |
| **Documentacao** | [backend/agents.md](../../docs/backend/agents.md) |

### Frontend Container (SPA React)

O Frontend e uma Single Page Application moderna construida com React, TypeScript e Vite.

```mermaid
flowchart TB
    subgraph frontend [Frontend Container - Porta 5173]
        subgraph build [Build Tools]
            Vite[Vite 5.4<br/>Dev Server + Build]
            TypeScript[TypeScript 5.6<br/>Type Checking]
            Tailwind[Tailwind CSS 3.4<br/>Styling]
        end

        subgraph app [React Application]
            App[App.tsx<br/>Root Component]
            Router[React Router<br/>SPA Navigation]
        end

        subgraph pages [Pages]
            Home[HomePage<br/>Catalogo]
            Chat[ChatPage<br/>Agente Interativo]
            Cart[CartPage<br/>Carrinho]
            Checkout[CheckoutPage<br/>Finalizar]
        end

        subgraph components [UI Components]
            BookCard[BookCard<br/>Exibicao produto]
            ChatBox[ChatBox<br/>Mensagens]
            FlowVis[FlowVisualizer<br/>Grafo interativo]
        end

        subgraph state [State Management]
            Zustand[Zustand Store]
            CartState[cart: CartItem[]]
            ChatState[messages: Message[]]
            AgentState[agentState: AgentNode]
        end

        subgraph services [Services]
            APIService[api.ts<br/>REST Client]
            WSService[websocket.ts<br/>Real-time]
        end
    end

    Vite --> App
    App --> Router
    Router --> Home
    Router --> Chat
    Router --> Cart
    Router --> Checkout

    Home --> BookCard
    Chat --> ChatBox
    Chat --> FlowVis

    BookCard --> Zustand
    ChatBox --> Zustand
    FlowVis --> Zustand

    Zustand --> CartState
    Zustand --> ChatState
    Zustand --> AgentState

    APIService --> Zustand
    WSService --> ChatState
```

| Aspecto | Descricao |
|---------|-----------|
| **Framework** | React 18 + TypeScript 5.6 |
| **Build Tool** | Vite 5.4 |
| **Styling** | Tailwind CSS 3.4 |
| **State** | Zustand 5.0 |
| **Real-time** | WebSocket (native) |
| **Porta** | 5173 (desenvolvimento) |
| **Documentacao** | [frontend/front.md](../../docs/frontend/front.md) |

### UCP Server Container

```mermaid
flowchart TB
    subgraph ucp_server [UCP Server Container - Porta 8182]
        subgraph routes [Routes Layer]
            DiscoveryRoute[GET /.well-known/ucp]
            CheckoutRoutes[/checkout-sessions/*]
            BooksRoutes[/books/*]
        end

        subgraph capabilities [Capabilities]
            CheckoutCap[Checkout Capability]
            DiscountExt[Discount Extension]
            FulfillmentExt[Fulfillment Extension]
        end

        subgraph services [Services]
            SessionService[Session Service]
            PricingService[Pricing Service]
            PaymentService[Payment Service]
        end

        subgraph security [Security]
            AP2Handler[AP2 Handler]
            SignatureValidator[Signature Validator]
        end
    end

    DiscoveryRoute --> CheckoutCap
    CheckoutRoutes --> CheckoutCap
    CheckoutRoutes --> DiscountExt
    CheckoutCap --> SessionService
    SessionService --> AP2Handler
```

### MCP Server Container

```mermaid
flowchart TB
    subgraph mcp_server [MCP Server Container - Porta 8183]
        subgraph protocol [Protocol]
            MCPHandler[MCP Protocol Handler]
            ToolDispatcher[Tool Dispatcher]
        end

        subgraph tools [Tools]
            SearchTool[tool_search]
            DiscoveryTool[refresh_ucp_discovery]
            CheckoutTools[checkout tools]
            CodeTool[execute_code]
        end

        subgraph proxy [Proxy]
            UCPProxy[UCP Proxy]
            Sandbox[Execution Sandbox]
        end
    end

    MCPHandler --> ToolDispatcher
    ToolDispatcher --> SearchTool
    ToolDispatcher --> DiscoveryTool
    ToolDispatcher --> CheckoutTools
    ToolDispatcher --> CodeTool
    CheckoutTools --> UCPProxy
    CodeTool --> Sandbox
```

## Comunicacao entre User Agent e Loja

### Via UCP (Direto)

```mermaid
sequenceDiagram
    participant UA as User Agent
    participant UCP as UCP Server

    UA->>UCP: GET /.well-known/ucp
    UCP-->>UA: Discovery Profile
    
    UA->>UCP: POST /checkout-sessions
    UCP-->>UA: Session Created
    
    UA->>UCP: PUT /checkout-sessions/{id}
    UCP-->>UA: Session Updated
    
    UA->>UCP: POST /checkout-sessions/{id}/complete
    UCP-->>UA: Order Completed
```

### Via A2A (Atraves dos Agentes)

```mermaid
sequenceDiagram
    participant UA as User Agent
    participant A2A as A2A Endpoint
    participant SA as Store Agents
    participant RA as Recommend Agent

    UA->>A2A: A2A Message (recommend.request)
    A2A->>SA: Route to agent
    SA->>RA: Handle recommendation
    RA-->>SA: Book recommendations
    SA-->>A2A: A2A Message (recommend.response)
    A2A-->>UA: Recommendations
```

### Via MCP (Ferramentas)

```mermaid
sequenceDiagram
    participant UA as User Agent
    participant MCP as MCP Server
    participant Tools as Tool Registry
    participant UCP as UCP Server

    UA->>MCP: tool_search("checkout")
    MCP->>Tools: Search available tools
    Tools-->>MCP: [create_checkout, apply_discount, ...]
    MCP-->>UA: Available tools
    
    UA->>MCP: create_checkout(params)
    MCP->>UCP: POST /checkout-sessions
    UCP-->>MCP: Session
    MCP-->>UA: Session created
```

## Portas e Endpoints

| Container | Porta | Endpoints Principais |
|-----------|-------|---------------------|
| Frontend | 5173 | `/` (SPA) |
| API Gateway | 8000 | `/api/*`, `/ws/*` |
| UCP Server | 8182 | `/.well-known/ucp`, `/checkout-sessions/*` |
| MCP Server | 8183 | MCP Protocol (stdio/HTTP) |
| User Agent | - | Local execution |

## Fluxo de Compra com User Agent

```mermaid
sequenceDiagram
    participant User as Usuario
    participant UA as User Agent
    participant UCP as UCP Server
    participant AP2 as AP2 Security
    participant DB as Database

    User->>UA: "Compre o livro Python para Todos"
    
    UA->>UCP: GET /.well-known/ucp
    UCP-->>UA: Capabilities (checkout, discount)
    
    UA->>UCP: GET /books?search=Python
    UCP->>DB: SELECT * FROM books
    DB-->>UCP: [book_003: Python para Todos]
    UCP-->>UA: Book found
    
    UA->>UCP: POST /checkout-sessions
    Note over UA,UCP: line_items: [book_003], buyer: user_info
    UCP->>DB: INSERT checkout_session
    UCP-->>UA: session_id, status=ready
    
    UA->>AP2: create_mandate(3990, BRL)
    AP2-->>UA: JWT mandate
    
    UA->>UCP: POST /checkout-sessions/{id}/complete
    Note over UA,UCP: payment: {mandate: JWT}
    UCP->>UCP: Validate AP2 mandate
    UCP->>DB: UPDATE status=completed
    UCP-->>UA: Order confirmed
    
    UA-->>User: "Compra realizada! Pedido #123"
```

## Arquitetura Multi-Loja

O User Agent pode interagir com multiplas lojas simultaneamente:

```mermaid
flowchart TB
    subgraph user [Usuario]
        UA[User Agent]
    end

    subgraph stores [Lojas UCP]
        Store1[Livraria UCP<br/>:8182]
        Store2[Eletronica UCP<br/>:8282]
        Store3[Roupas UCP<br/>:8382]
    end

    UA -->|Discovery| Store1
    UA -->|Discovery| Store2
    UA -->|Discovery| Store3

    UA -->|Checkout| Store1
    UA -->|Checkout| Store2
```

## Decisoes de Design

1. **User Agent Independente**: Executa no ambiente do usuario, nao na loja
2. **Multiplos Protocolos**: User Agent suporta UCP, A2A, MCP e AP2
3. **A2A Bidirecional**: Store Agents podem receber requests de User Agents
4. **Stateless UCP**: Cada request UCP e independente (idempotency keys)
5. **AP2 para Autonomia**: User Agent gera mandatos sem intervencao do usuario
