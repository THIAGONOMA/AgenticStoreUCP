# Módulo MCP - Model Context Protocol

Este módulo implementa o servidor **MCP (Model Context Protocol)** da Livraria Virtual UCP. O MCP permite que agentes de IA interajam com o catálogo da livraria de forma estruturada, com suporte a **progressive disclosure** para revelar ferramentas gradualmente.

## Visão Geral

O módulo MCP fornece:
- **Servidor MCP** - Expõe ferramentas para agentes de IA
- **HTTP Server** - API REST alternativa ao SSE/stdio
- **Tool Registry** - Registro centralizado de ferramentas
- **Progressive Disclosure** - Revelação gradual de ferramentas
- **7 Ferramentas** - Busca, catálogo, carrinho e recomendações

---

## Arquitetura do Módulo

```
backend/src/mcp/
├── __init__.py              # Exports públicos
├── server.py                # Servidor MCP principal
├── http_server.py           # API HTTP para MCP
├── registry.py              # Registry de ferramentas
├── progressive_disclosure.py # Controle de disclosure
├── mcp.md                   # Esta documentação
└── tools/                   # Ferramentas MCP
    ├── search.py
    ├── catalog.py
    ├── cart.py
    ├── recommendations.py
    └── tools.md             # → Documentação detalhada
```

### Diagrama de Arquitetura

```mermaid
flowchart TB
    subgraph Clients["Clientes"]
        AI["AI Agent<br/>(Claude, GPT, etc)"]
        HTTP["HTTP Client"]
    end

    subgraph MCP["Módulo MCP"]
        subgraph Core["Core"]
            Server["server.py<br/>mcp_server"]
            HTTPServer["http_server.py<br/>FastAPI Router"]
        end
        
        subgraph Management["Gerenciamento"]
            Registry["registry.py<br/>ToolRegistry"]
            Disclosure["progressive_disclosure.py<br/>ProgressiveDisclosure"]
        end
        
        subgraph ToolsModule["tools/"]
            Search["search.py"]
            Catalog["catalog.py"]
            Cart["cart.py"]
            Recs["recommendations.py"]
        end
    end

    subgraph Data["Dados"]
        DB[(products_repo<br/>discounts_repo)]
    end

    AI -->|"MCP Protocol"| Server
    HTTP -->|"REST API"| HTTPServer
    
    Server --> ToolsModule
    HTTPServer --> Disclosure
    HTTPServer --> Server
    
    Registry --> ToolsModule
    Disclosure --> Registry
    
    ToolsModule --> DB
    
    style Core fill:#e3f2fd
    style Management fill:#fff3e0
    style ToolsModule fill:#e8f5e9
```

---

## Componentes Principais

### 1. MCP Server (`server.py`)

Servidor MCP principal usando a biblioteca `mcp`.

#### Diagrama do Server

```mermaid
flowchart TB
    subgraph MCPServer["mcp_server (Server)"]
        ListTools["@list_tools()<br/>Listar ferramentas"]
        CallTool["@call_tool()<br/>Executar ferramenta"]
    end

    subgraph Tools["tools/"]
        GetAll["get_all_tools()"]
        CallHandler["call_tool_handler()"]
    end

    ListTools --> GetAll
    CallTool --> CallHandler
    
    GetAll --> Return1["List[Tool]"]
    CallHandler --> Return2["List[TextContent]"]
```

#### Handlers Registrados

| Handler | Decorator | Descrição |
|---------|-----------|-----------|
| `list_tools` | `@mcp_server.list_tools()` | Lista todas as ferramentas disponíveis |
| `call_tool` | `@mcp_server.call_tool()` | Executa uma ferramenta pelo nome |

#### Código Principal

```python
# Criar instância do servidor MCP
mcp_server = Server("livraria-mcp")

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    """Retorna todas as ferramentas MCP."""
    return get_all_tools()

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Executa uma ferramenta e retorna resultado como JSON."""
    result = await call_tool_handler(name, arguments)
    return [TextContent(type="text", text=json.dumps(result))]
```

---

### 2. HTTP Server (`http_server.py`)

API REST que expõe as funcionalidades MCP via HTTP.

#### Diagrama de Rotas

```mermaid
flowchart LR
    subgraph Routes["/mcp"]
        GET1["GET /tools"]
        POST1["POST /tools/{name}/call"]
        POST2["POST /sessions/{id}/upgrade"]
        GET2["GET /sessions/{id}/context"]
        DELETE["DELETE /sessions/{id}"]
    end

    subgraph Handlers["Handlers"]
        H1["get_tools()"]
        H2["call_mcp_tool()"]
        H3["upgrade_disclosure_level()"]
        H4["get_session_context()"]
        H5["clear_session()"]
    end

    GET1 --> H1
    POST1 --> H2
    POST2 --> H3
    GET2 --> H4
    DELETE --> H5
```

#### Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/mcp/tools` | Lista ferramentas (com progressive disclosure opcional) |
| POST | `/mcp/tools/{tool_name}/call` | Executa uma ferramenta |
| POST | `/mcp/sessions/{session_id}/upgrade` | Faz upgrade do nível de disclosure |
| GET | `/mcp/sessions/{session_id}/context` | Obtém contexto de disclosure |
| DELETE | `/mcp/sessions/{session_id}` | Limpa sessão |

#### Fluxo com Progressive Disclosure

```mermaid
sequenceDiagram
    participant C as Client
    participant H as HTTP Server
    participant D as ProgressiveDisclosure
    participant S as MCP Server

    C->>H: GET /mcp/tools?session_id=abc
    H->>D: get_available_tools(session_id)
    D-->>H: Tools do nível atual
    H-->>C: {tools: [...], count: N}

    C->>H: POST /mcp/tools/calculate_cart/call?session_id=abc
    H->>D: context.can_access("calculate_cart")
    alt Não tem acesso
        H-->>C: 403 Forbidden
    else Tem acesso
        H->>D: record_interaction()
        H->>S: call_tool("calculate_cart", args)
        S-->>H: Result
        H-->>C: {success: true, data: {...}}
    end
```

---

### 3. Tool Registry (`registry.py`)

Registro centralizado para gerenciamento de ferramentas.

#### Diagrama de Classes

```mermaid
classDiagram
    class ToolDefinition {
        +str name
        +str description
        +Dict input_schema
        +Callable handler
        +str category
        +bool requires_auth
        +int rate_limit
    }
    
    class ToolRegistry {
        +Dict~str,ToolDefinition~ tools
        +register(name, description, schema, handler, ...)
        +unregister(name)
        +get(name) ToolDefinition
        +list_all() List~ToolDefinition~
        +list_by_category(category) List~ToolDefinition~
        +get_categories() List~str~
        +execute(name, arguments) Any
        +to_mcp_format() List~Dict~
    }
    
    class tool {
        <<decorator>>
        +name: str
        +description: str
        +input_schema: Dict
        +category: str
        +requires_auth: bool
    }
    
    ToolRegistry --> ToolDefinition
    tool --> ToolRegistry : registra em
```

#### Uso do Decorator

```python
from backend.src.mcp import tool

@tool(
    name="my_tool",
    description="Descrição da ferramenta",
    input_schema={"type": "object", "properties": {...}},
    category="custom"
)
async def my_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"result": "..."}
```

#### Métodos do Registry

| Método | Descrição |
|--------|-----------|
| `register(...)` | Registra uma nova ferramenta |
| `unregister(name)` | Remove uma ferramenta |
| `get(name)` | Obtém definição de uma ferramenta |
| `list_all()` | Lista todas as ferramentas |
| `list_by_category(cat)` | Lista ferramentas de uma categoria |
| `get_categories()` | Lista categorias disponíveis |
| `execute(name, args)` | Executa uma ferramenta |
| `to_mcp_format()` | Converte para formato MCP |

---

### 4. Progressive Disclosure (`progressive_disclosure.py`)

Implementa a revelação gradual de ferramentas conforme o contexto do usuário.

#### Diagrama de Níveis

```mermaid
flowchart TB
    subgraph Levels["Níveis de Disclosure"]
        Basic["basic<br/>3 ferramentas"]
        Shopping["shopping<br/>6 ferramentas"]
        Advanced["advanced<br/>9 ferramentas"]
    end
    
    subgraph BasicTools["Basic"]
        B1["search_books"]
        B2["list_categories"]
        B3["get_book_details"]
    end
    
    subgraph ShoppingTools["+ Shopping"]
        S1["get_books_by_category"]
        S2["check_discount_code"]
        S3["calculate_cart"]
    end
    
    subgraph AdvancedTools["+ Advanced"]
        A1["get_recommendations"]
        A2["create_checkout"]
        A3["complete_checkout"]
    end
    
    Basic --> BasicTools
    Shopping --> BasicTools
    Shopping --> ShoppingTools
    Advanced --> BasicTools
    Advanced --> ShoppingTools
    Advanced --> AdvancedTools
    
    style Basic fill:#c8e6c9
    style Shopping fill:#fff9c4
    style Advanced fill:#ffcdd2
```

#### Diagrama de Classes

```mermaid
classDiagram
    class DisclosureLevel {
        +str name
        +Set~str~ tools
        +str description
    }
    
    class DisclosureContext {
        +str session_id
        +str current_level
        +Set~str~ unlocked_tools
        +int interaction_count
        +unlock(tool_name)
        +can_access(tool_name) bool
    }
    
    class ProgressiveDisclosure {
        +Dict~str,DisclosureLevel~ levels
        +Dict~str,DisclosureContext~ contexts
        -_setup_default_levels()
        +get_context(session_id) DisclosureContext
        +upgrade_level(session_id, level) List~str~
        +get_available_tools(session_id) List~Dict~
        +record_interaction(session_id, tool_name)
        +clear_context(session_id)
    }
    
    ProgressiveDisclosure --> DisclosureLevel
    ProgressiveDisclosure --> DisclosureContext
```

#### Fluxo de Auto-Upgrade

```mermaid
flowchart TD
    Start([record_interaction]) --> Increment[interaction_count++]
    
    Increment --> Check1{count >= 3<br/>AND level == basic?}
    Check1 -->|Sim| Upgrade1[upgrade_level → shopping]
    Check1 -->|Não| Check2{count >= 7<br/>AND level == shopping?}
    
    Check2 -->|Sim| Upgrade2[upgrade_level → advanced]
    Check2 -->|Não| End([Fim])
    
    Upgrade1 --> End
    Upgrade2 --> End
```

#### Níveis Configurados

| Nível | Ferramentas | Descrição |
|-------|-------------|-----------|
| `basic` | search_books, list_categories, get_book_details | Ferramentas básicas de navegação |
| `shopping` | + get_books_by_category, check_discount_code, calculate_cart | Ferramentas de compra |
| `advanced` | + get_recommendations, create_checkout, complete_checkout | Ferramentas completas |

---

## Submódulo Tools

O submódulo `tools/` contém as implementações das 7 ferramentas MCP.

📄 **Documentação completa:** [`tools/tools.md`](tools/tools.md)

```mermaid
flowchart LR
    subgraph Tools["tools/"]
        Search["search.py<br/>search_books<br/>get_book_details"]
        Catalog["catalog.py<br/>list_categories<br/>get_books_by_category"]
        Cart["cart.py<br/>check_discount_code<br/>calculate_cart"]
        Recs["recommendations.py<br/>get_recommendations"]
    end
```

| Arquivo | Ferramentas |
|---------|-------------|
| `search.py` | `search_books`, `get_book_details` |
| `catalog.py` | `list_categories`, `get_books_by_category` |
| `cart.py` | `check_discount_code`, `calculate_cart` |
| `recommendations.py` | `get_recommendations` |

---

## Exports do Módulo

```python
from backend.src.mcp import (
    # Servidor MCP
    mcp_server,
    
    # Registry
    ToolRegistry,
    ToolDefinition,
    get_tool_registry,
    tool,  # decorator
    
    # Progressive Disclosure
    ProgressiveDisclosure,
    DisclosureContext,
    DisclosureLevel,
    get_progressive_disclosure,
)
```

---

## Fluxos de Uso

### Fluxo MCP Padrão (Stdio/SSE)

```mermaid
sequenceDiagram
    participant AI as AI Agent
    participant S as mcp_server
    participant T as tools/

    AI->>S: list_tools
    S->>T: get_all_tools()
    T-->>S: List[Tool]
    S-->>AI: 7 ferramentas disponíveis

    AI->>S: call_tool("search_books", {query: "python"})
    S->>T: call_tool_handler("search_books", {...})
    T-->>S: {count: 3, books: [...]}
    S-->>AI: TextContent(JSON)
```

### Fluxo HTTP com Progressive Disclosure

```mermaid
sequenceDiagram
    participant C as Client
    participant H as HTTP Server
    participant D as ProgressiveDisclosure
    participant S as mcp_server

    Note over C,S: Sessão nova - nível basic
    
    C->>H: GET /mcp/tools?session_id=sess_123
    H->>D: get_available_tools("sess_123")
    D-->>H: [search_books, list_categories, get_book_details]
    H-->>C: {tools: [...], count: 3}

    C->>H: POST /mcp/tools/search_books/call
    H->>D: record_interaction()
    H->>S: call_tool("search_books", {...})
    S-->>H: Result
    H-->>C: {success: true, data: {...}}

    Note over C,S: Após 3 interações → auto-upgrade para shopping

    C->>H: GET /mcp/tools?session_id=sess_123
    H->>D: get_available_tools("sess_123")
    D-->>H: [6 ferramentas]
    H-->>C: {tools: [...], count: 6}
```

### Fluxo de Upgrade Manual

```mermaid
sequenceDiagram
    participant C as Client
    participant H as HTTP Server
    participant D as ProgressiveDisclosure

    C->>H: POST /mcp/sessions/sess_123/upgrade
    Note right of C: {level: "advanced"}
    
    H->>D: upgrade_level("sess_123", "advanced")
    D->>D: Calcular novas ferramentas
    D-->>H: ["get_recommendations", "create_checkout", ...]
    
    H-->>C: {session_id, new_level: "advanced", new_tools: [...]}
```

---

## Integração com UCP Server

O módulo MCP é integrado ao UCP Server via FastAPI router.

```mermaid
flowchart TB
    subgraph UCP["UCP Server (:8182)"]
        Main["main.py"]
        Router["FastAPI Router"]
    end
    
    subgraph MCP["MCP Module"]
        HTTPRouter["http_server.router"]
        Server["mcp_server"]
    end
    
    Main --> Router
    Router -->|"include_router"| HTTPRouter
    HTTPRouter --> Server
```

### Montagem no UCP Server

```python
from fastapi import FastAPI
from backend.src.mcp.http_server import router as mcp_router

app = FastAPI()
app.include_router(mcp_router)  # Monta em /mcp
```

---

## Instâncias Globais

O módulo exporta três instâncias globais:

```mermaid
flowchart LR
    subgraph Globals["Instâncias Globais"]
        mcp_server["mcp_server<br/>Server('livraria-mcp')"]
        registry["_tool_registry<br/>ToolRegistry"]
        disclosure["_progressive_disclosure<br/>ProgressiveDisclosure"]
    end
    
    subgraph Getters["Funções de Acesso"]
        get_registry["get_tool_registry()"]
        get_disclosure["get_progressive_disclosure()"]
    end
    
    get_registry --> registry
    get_disclosure --> disclosure
```

---

## Dependências

```mermaid
flowchart TB
    subgraph External["Externas"]
        mcp_lib["mcp<br/>Server, Tool, TextContent"]
        fastapi["fastapi<br/>APIRouter, HTTPException"]
        structlog["structlog"]
    end
    
    subgraph Internal["Internas"]
        tools["./tools<br/>get_all_tools, call_tool_handler"]
        db["../db<br/>products_repo, discounts_repo"]
    end
    
    subgraph MCP["Módulo MCP"]
        server["server.py"]
        http["http_server.py"]
        registry["registry.py"]
        disclosure["progressive_disclosure.py"]
    end
    
    server --> mcp_lib
    server --> tools
    server --> structlog
    
    http --> fastapi
    http --> server
    http --> disclosure
    http --> structlog
    
    registry --> structlog
    
    disclosure --> registry
    disclosure --> structlog
    
    tools --> db
```

---

## Referências

- **Ferramentas MCP:** [`tools/tools.md`](tools/tools.md)
- **MCP Protocol Spec:** https://modelcontextprotocol.io/
- **Database Layer:** [`../db/db.md`](../db/db.md)
