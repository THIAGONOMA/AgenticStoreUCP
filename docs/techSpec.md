# Especificacao Tecnica - Livraria Virtual UCP

Este documento detalha todas as especificacoes tecnicas do projeto, incluindo stack tecnologico, dependencias, APIs, protocolos e configuracoes.

---

## Stack Tecnologico

### Backend (Loja)

| Tecnologia | Versao | Proposito |
|------------|--------|-----------|
| Python | 3.11+ | Linguagem principal |
| FastAPI | 0.109+ | Framework web/API |
| Uvicorn | 0.27+ | ASGI server |
| LangGraph | 0.2+ | Orquestracao de agentes |
| LangChain | 0.3+ | Integracao com LLMs |
| Pydantic | 2.5+ | Validacao de dados |
| httpx | 0.27+ | Cliente HTTP async |
| SQLite | 3.45+ | Banco de dados |
| cryptography | 42.0+ | Criptografia Ed25519 |
| FastMCP | 0.1+ | Servidor MCP |

### User Agent (Agente do Usuario)

| Tecnologia | Versao | Proposito |
|------------|--------|-----------|
| Python | 3.11+ | Linguagem principal |
| LangGraph | 0.2+ | Orquestracao do agente |
| LangChain | 0.3+ | Integracao com LLMs |
| httpx | 0.27+ | Cliente UCP (HTTP async) |
| websockets | 12.0+ | Cliente A2A (WebSocket) |
| cryptography | 42.0+ | AP2 mandates (Ed25519) |
| Rich | 13.7+ | CLI output formatado |
| Typer | 0.9+ | CLI framework |

### Frontend

| Tecnologia | Versao | Proposito |
|------------|--------|-----------|
| React | 18.2+ | Framework UI |
| TypeScript | 5.3+ | Tipagem estatica |
| Vite | 5.0+ | Build tool |
| Tailwind CSS | 3.4+ | Styling |
| Zustand | 4.5+ | State management |
| React Query | 5.0+ | Data fetching |
| Socket.io Client | 4.7+ | WebSocket |
| Axios | 1.6+ | HTTP client |

### Ferramentas de Desenvolvimento

| Ferramenta | Proposito |
|------------|-----------|
| uv | Gerenciador de pacotes Python |
| npm/pnpm | Gerenciador de pacotes Node |
| Ruff | Linter/Formatter Python |
| ESLint | Linter JavaScript/TypeScript |
| Prettier | Formatter |
| pytest | Testes Python |
| Vitest | Testes JavaScript |

---

## Estrutura de Pastas

```
FuturesUCP/
├── docs/                           # Documentacao
│   ├── basicPlan.md               # Plano de execucao
│   ├── techSpec.md                # Especificacao tecnica
│   └── architecture/              # Diagramas de arquitetura
│       ├── README.md
│       ├── overview.md            # C4 Context
│       ├── containers.md          # C4 Containers
│       ├── components.md          # C4 Components
│       ├── flows.md               # Diagramas de sequencia
│       └── data-model.md          # Modelo ER
│
├── backend/                        # Codigo backend Python
│   ├── pyproject.toml             # Configuracao do projeto
│   ├── requirements.txt           # Dependencias
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                # Entry point FastAPI
│   │   ├── config.py              # Configuracoes
│   │   │
│   │   ├── ucp_server/            # Servidor UCP
│   │   │   ├── __init__.py
│   │   │   ├── server.py          # App FastAPI UCP
│   │   │   ├── discovery.py       # /.well-known/ucp
│   │   │   ├── routes/
│   │   │   │   ├── checkout.py    # Routes de checkout
│   │   │   │   └── books.py       # Routes de livros
│   │   │   ├── capabilities/
│   │   │   │   ├── checkout.py    # Checkout capability
│   │   │   │   ├── discount.py    # Discount extension
│   │   │   │   └── fulfillment.py # Fulfillment extension
│   │   │   ├── services/
│   │   │   │   ├── session.py     # Session service
│   │   │   │   ├── pricing.py     # Pricing service
│   │   │   │   └── payment.py     # Payment service
│   │   │   └── models/
│   │   │       ├── book.py
│   │   │       ├── checkout.py
│   │   │       └── payment.py
│   │   │
│   │   ├── agents/                # Agentes LangGraph
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py    # Grafo principal
│   │   │   ├── state.py           # Estado compartilhado
│   │   │   ├── router.py          # Intent router
│   │   │   ├── discovery_agent.py
│   │   │   ├── shopping_agent.py
│   │   │   ├── recommend_agent.py
│   │   │   └── a2a/
│   │   │       ├── message_bus.py
│   │   │       └── protocol.py
│   │   │
│   │   ├── mcp/                   # Servidor MCP
│   │   │   ├── __init__.py
│   │   │   ├── server.py          # FastMCP server
│   │   │   ├── tool_registry.py   # Registry com deferred loading
│   │   │   ├── ucp_proxy.py       # Proxy para UCP
│   │   │   ├── sandbox.py         # Sandbox de execucao
│   │   │   └── tools/
│   │   │       ├── search.py
│   │   │       ├── checkout.py
│   │   │       └── discovery.py
│   │   │
│   │   ├── security/              # Seguranca AP2
│   │   │   ├── __init__.py
│   │   │   ├── key_manager.py     # Ed25519 keys
│   │   │   ├── ap2_security.py    # AP2 mandates
│   │   │   ├── signatures.py      # Request signatures
│   │   │   └── conformance.py     # UCP conformance headers
│   │   │
│   │   └── db/                    # Banco de dados
│   │       ├── __init__.py
│   │       ├── database.py        # Connection manager
│   │       ├── products.py        # Products repository
│   │       ├── transactions.py    # Transactions repository
│   │       └── migrations/
│   │           ├── 001_initial.sql
│   │           └── 002_fulfillment.sql
│   │
│   ├── data/
│   │   └── books_catalog.csv      # Dados iniciais
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_discovery.py
│       ├── test_checkout.py
│       ├── test_agents.py
│       └── test_security.py
│
├── user_agent/                     # User Agent (Agente do Usuario) - NOVO!
│   ├── pyproject.toml             # Configuracao do projeto
│   ├── README.md                  # Instrucoes de uso
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                # Entry point
│   │   ├── cli.py                 # CLI com Rich/Typer
│   │   ├── config.py              # Configuracoes
│   │   │
│   │   ├── agent/                 # Core do agente
│   │   │   ├── __init__.py
│   │   │   ├── graph.py           # Main LangGraph
│   │   │   ├── state.py           # Agent state TypedDict
│   │   │   └── nodes/
│   │   │       ├── discovery.py   # Discovery node
│   │   │       ├── shopping.py    # Shopping node
│   │   │       ├── compare.py     # Compare prices node
│   │   │       └── recommend.py   # Get recommendations node
│   │   │
│   │   ├── clients/               # Protocol clients
│   │   │   ├── __init__.py
│   │   │   ├── ucp_client.py      # Cliente UCP HTTP
│   │   │   ├── a2a_client.py      # Cliente A2A WebSocket
│   │   │   └── mcp_client.py      # Cliente MCP (opcional)
│   │   │
│   │   ├── security/              # AP2 para o User Agent
│   │   │   ├── __init__.py
│   │   │   ├── key_manager.py     # Chaves Ed25519 do usuario
│   │   │   └── ap2_client.py      # Geracao de mandatos
│   │   │
│   │   ├── registry/              # Registro de lojas
│   │   │   ├── __init__.py
│   │   │   ├── stores.py          # Store registry
│   │   │   └── capabilities.py    # Capabilities cache
│   │   │
│   │   └── utils/
│   │       ├── formatters.py      # Formatacao Rich
│   │       └── validators.py      # Validacoes
│   │
│   └── tests/
│       ├── test_ucp_client.py
│       ├── test_discovery.py
│       └── test_shopping.py
│
├── frontend/                       # Codigo frontend React
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx               # Entry point
│       ├── App.tsx                # App principal
│       ├── components/
│       │   ├── BookCatalog.tsx
│       │   ├── BookCard.tsx
│       │   ├── Cart.tsx
│       │   ├── Checkout.tsx
│       │   ├── AgentChat.tsx
│       │   └── TransactionStatus.tsx
│       ├── hooks/
│       │   ├── useCart.ts
│       │   ├── useAgent.ts
│       │   ├── useCheckout.ts
│       │   └── useBooks.ts
│       ├── services/
│       │   ├── api.ts
│       │   └── websocket.ts
│       ├── stores/
│       │   ├── cart.ts
│       │   └── agent.ts
│       └── types/
│           └── index.ts
│
├── scripts/
│   ├── import_books.py            # Importar catalogo
│   ├── run_demo.sh                # Script de demo
│   └── setup.sh                   # Setup inicial
│
└── README.md                       # README principal
```

---

## Dependencias Python (requirements.txt)

```txt
# Web Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
websockets>=12.0

# LangGraph e LangChain
langgraph>=0.2.0
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-anthropic>=0.2.0

# Validacao e Serialização
pydantic>=2.5.0
pydantic-settings>=2.1.0

# HTTP Client
httpx>=0.27.0
aiohttp>=3.9.0

# Database
aiosqlite>=0.20.0

# Seguranca e Criptografia
cryptography>=42.0.0
PyJWT>=2.8.0

# MCP
mcp>=0.1.0

# Utilitarios
python-dotenv>=1.0.0
structlog>=24.1.0

# Desenvolvimento
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
ruff>=0.2.0
```

---

## Dependencias Node (package.json)

```json
{
  "name": "livraria-ucp-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "@tanstack/react-query": "^5.20.0",
    "zustand": "^4.5.0",
    "axios": "^1.6.0",
    "socket.io-client": "^4.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.330.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.56.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "vitest": "^1.2.0"
  }
}
```

---

## Especificacao das APIs

### API Gateway (Porta 8000)

#### Endpoints REST

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/api/books` | Listar livros |
| GET | `/api/books/{id}` | Obter livro |
| GET | `/api/books/search?q=` | Buscar livros |
| POST | `/api/chat` | Enviar mensagem ao agente |
| GET | `/api/cart` | Obter carrinho |
| POST | `/api/cart/items` | Adicionar item |
| DELETE | `/api/cart/items/{id}` | Remover item |
| POST | `/api/checkout` | Iniciar checkout |

#### WebSocket

| Evento | Direcao | Payload |
|--------|---------|---------|
| `connect` | Client -> Server | `{ user_id }` |
| `chat` | Client -> Server | `{ message }` |
| `response` | Server -> Client | `{ message, type }` |
| `typing` | Server -> Client | `{ agent }` |
| `cart_update` | Server -> Client | `{ cart }` |
| `checkout_status` | Server -> Client | `{ status, session_id }` |

### A2A Endpoint (Porta 8000) - Para User Agents Externos

O A2A Endpoint permite que **User Agents externos** se comuniquem com os Store Agents da loja.

#### WebSocket A2A

```
WS /ws/a2a
```

| Evento | Direcao | Payload |
|--------|---------|---------|
| `a2a.connect` | Agent -> Server | `{ agent_id, agent_profile }` |
| `a2a.request` | Agent -> Server | `{ message_id, action, payload }` |
| `a2a.response` | Server -> Agent | `{ message_id, status, payload }` |
| `a2a.event` | Server -> Agent | `{ event_type, payload }` |

#### Acoes A2A Suportadas

| Action | Descricao | Payload Request | Payload Response |
|--------|-----------|-----------------|------------------|
| `discover` | Descobrir capabilities | `{}` | `{ capabilities[] }` |
| `recommend` | Pedir recomendacoes | `{ topic, limit }` | `{ books[] }` |
| `search` | Buscar produtos | `{ query }` | `{ results[] }` |
| `add_to_cart` | Adicionar ao carrinho | `{ book_id, quantity }` | `{ cart }` |
| `get_cart` | Obter carrinho | `{}` | `{ cart }` |
| `checkout` | Iniciar checkout | `{ buyer_info }` | `{ session }` |

#### Exemplo de Mensagem A2A

```json
// Request
{
  "message_id": "msg_123",
  "from_agent": "user_agent_456",
  "to_agent": "store_orchestrator",
  "type": "request",
  "action": "recommend",
  "payload": {
    "topic": "inteligencia artificial",
    "limit": 5
  },
  "timestamp": "2026-01-29T10:30:00Z"
}

// Response
{
  "message_id": "msg_123",
  "from_agent": "store_orchestrator",
  "to_agent": "user_agent_456",
  "type": "response",
  "action": "recommend",
  "payload": {
    "books": [
      { "id": "book_004", "title": "ML Pratico", "price": 7990 },
      { "id": "book_007", "title": "Arquitetura SW", "price": 6990 }
    ]
  },
  "timestamp": "2026-01-29T10:30:01Z"
}
```

### UCP Server (Porta 8182)

#### Discovery

```http
GET /.well-known/ucp
```

**Response:**
```json
{
  "ucp": {
    "version": "2026-01-11",
    "services": {
      "dev.ucp.shopping": {
        "version": "2026-01-11",
        "spec": "https://ucp.dev/specs/shopping",
        "rest": {
          "schema": "https://ucp.dev/services/shopping/openapi.json",
          "endpoint": "http://localhost:8182/"
        }
      }
    },
    "capabilities": [
      {
        "name": "dev.ucp.shopping.checkout",
        "version": "2026-01-11",
        "spec": "https://ucp.dev/specs/shopping/checkout",
        "schema": "https://ucp.dev/schemas/shopping/checkout.json"
      },
      {
        "name": "dev.ucp.shopping.discount",
        "version": "2026-01-11",
        "extends": "dev.ucp.shopping.checkout"
      },
      {
        "name": "dev.ucp.shopping.fulfillment",
        "version": "2026-01-11",
        "extends": "dev.ucp.shopping.checkout"
      }
    ]
  },
  "payment": {
    "handlers": [
      {
        "id": "mock_payment",
        "name": "dev.ucp.mock_payment",
        "version": "2026-01-11",
        "spec": "https://ucp.dev/specs/mock",
        "config_schema": "https://ucp.dev/schemas/mock.json",
        "instrument_schemas": [
          "https://ucp.dev/schemas/shopping/types/card_payment_instrument.json"
        ],
        "config": {
          "supported_tokens": ["success_token", "fail_token"]
        }
      }
    ]
  }
}
```

#### Checkout Sessions

```http
POST /checkout-sessions
Content-Type: application/json
UCP-Agent: profile="https://agent.example/profile"
request-signature: <signature>
idempotency-key: <uuid>
request-id: <uuid>
```

**Request Body:**
```json
{
  "line_items": [
    {
      "item": {
        "id": "book_001",
        "title": "O Codigo do Futuro"
      },
      "quantity": 1
    }
  ],
  "buyer": {
    "full_name": "Joao Silva",
    "email": "joao@email.com"
  },
  "currency": "BRL",
  "payment": {
    "instruments": [],
    "handlers": []
  }
}
```

**Response:**
```json
{
  "ucp": {
    "version": "2026-01-11",
    "capabilities": [
      { "name": "dev.ucp.shopping.checkout", "version": "2026-01-11" }
    ]
  },
  "id": "sess_abc123",
  "line_items": [
    {
      "id": "li_xyz789",
      "item": {
        "id": "book_001",
        "title": "O Codigo do Futuro",
        "price": 4990
      },
      "quantity": 1,
      "totals": [
        { "type": "subtotal", "amount": 4990 },
        { "type": "total", "amount": 4990 }
      ]
    }
  ],
  "buyer": {
    "full_name": "Joao Silva",
    "email": "joao@email.com"
  },
  "status": "ready_for_complete",
  "currency": "BRL",
  "totals": [
    { "type": "subtotal", "amount": 4990 },
    { "type": "total", "amount": 4990 }
  ],
  "links": [],
  "payment": { "handlers": [], "instruments": [] },
  "discounts": {}
}
```

#### Atualizar Checkout (Aplicar Desconto)

```http
PUT /checkout-sessions/{id}
```

**Request Body:**
```json
{
  "id": "sess_abc123",
  "discounts": {
    "codes": ["PRIMEIRA10"]
  }
}
```

#### Completar Checkout

```http
POST /checkout-sessions/{id}/complete
```

**Request Body:**
```json
{
  "payment": {
    "token": "pay_token123",
    "mandate": "<jwt_mandate>",
    "handler_id": "mock_payment"
  }
}
```

---

## Protocolos

### UCP (Universal Commerce Protocol)

**Versao:** 2026-01-11

**Capabilities implementadas:**
- `dev.ucp.shopping.checkout` - Core checkout
- `dev.ucp.shopping.discount` - Extensao de descontos
- `dev.ucp.shopping.fulfillment` - Extensao de entrega

**Headers obrigatorios:**
- `UCP-Agent`: Perfil do agente
- `request-signature`: Assinatura da requisicao
- `idempotency-key`: Chave de idempotencia
- `request-id`: ID unico da requisicao
- `ucp-timestamp`: Timestamp da requisicao
- `ucp-nonce`: Nonce unico

### A2A (Agent-to-Agent)

**Estrutura de mensagem:**
```python
class A2AMessage:
    message_id: str      # UUID
    from_agent: str      # ID do agente origem
    to_agent: str        # ID do agente destino
    type: str            # 'request' | 'response' | 'event'
    action: str          # Acao solicitada
    payload: dict        # Dados da mensagem
    timestamp: datetime  # ISO 8601
    correlation_id: str  # Para rastrear conversas
```

**Tipos de mensagem:**
- `discovery.request` - Solicitar descoberta UCP
- `discovery.response` - Resposta com capacidades
- `recommend.request` - Solicitar recomendacao
- `recommend.response` - Livros recomendados
- `checkout.request` - Iniciar checkout
- `checkout.response` - Status do checkout

### AP2 (Agent Payments Protocol)

**Algoritmo de assinatura:** EdDSA (Ed25519)

**Estrutura do mandato JWT:**
```json
{
  "header": {
    "alg": "EdDSA",
    "typ": "JWT",
    "kid": "key-id-123"
  },
  "payload": {
    "iss": "livraria-agent",
    "sub": "agent-autonomous-action",
    "aud": "merchant-livraria",
    "exp": 1706540400,
    "scope": "ucp:payment",
    "mandate": {
      "max_amount": 10000,
      "currency": "BRL"
    }
  }
}
```

**Formato de assinatura de requisicao:**
```
signing_input = f"{timestamp}.{nonce}.{canonical_payload}"
signature = base64url(Ed25519.sign(signing_input, private_key))
```

### MCP (Model Context Protocol)

**Ferramentas expostas:**

| Ferramenta | Descricao | Parametros |
|------------|-----------|------------|
| `tool_search` | Busca ferramentas por regex | `regex: string` |
| `refresh_ucp_discovery` | Descobre capacidades UCP | `url: string` |
| `create_checkout` | Cria sessao de checkout | `line_items, buyer, currency` |
| `update_checkout` | Atualiza sessao | `session_id, updates` |
| `apply_discount` | Aplica cupom | `session_id, code` |
| `complete_checkout` | Finaliza compra | `session_id, payment` |
| `execute_code` | Executa codigo no sandbox | `code: string` |

---

## Configuracoes de Ambiente

### Variaveis de Ambiente (.env)

```bash
# Servidor
API_HOST=0.0.0.0
API_PORT=8000
UCP_HOST=0.0.0.0
UCP_PORT=8182
MCP_PORT=8183

# Banco de dados
PRODUCTS_DB_PATH=./data/products.db
TRANSACTIONS_DB_PATH=./data/transactions.db

# LLM
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
LLM_MODEL=gpt-4-turbo-preview

# Seguranca
JWT_EXPIRY_SECONDS=3600
AP2_KEY_ID=livraria-key-001

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Debug
DEBUG=true
LOG_LEVEL=INFO
```

### Configuracao Python (config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    ucp_host: str = "0.0.0.0"
    ucp_port: int = 8182
    mcp_port: int = 8183
    
    # Database
    products_db_path: str = "./data/products.db"
    transactions_db_path: str = "./data/transactions.db"
    
    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4-turbo-preview"
    
    # Security
    jwt_expiry_seconds: int = 3600
    ap2_key_id: str = "livraria-key-001"
    
    # HTTP
    http_timeout: float = 30.0
    
    # Sandbox
    sandbox_globals: list[str] = ["json", "asyncio", "re", "datetime"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Modelos Pydantic Principais

### Book

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Book(BaseModel):
    id: str
    title: str
    author: str
    description: Optional[str] = None
    price: int  # centavos
    category: Optional[str] = None
    isbn: Optional[str] = None
    stock: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BookCreate(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    price: int
    category: Optional[str] = None
    isbn: Optional[str] = None
    stock: int = 0
```

### Store Agent State (Agentes da Loja - LangGraph)

```python
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph.message import add_messages

class StoreAgentState(TypedDict):
    # Mensagens do chat
    messages: Annotated[List, add_messages]
    
    # Perfil UCP descoberto
    ucp_profile: Optional[dict]
    
    # Carrinho atual
    cart: List[dict]
    
    # Sessao de checkout ativa
    checkout_session: Optional[dict]
    
    # Agente atual
    current_agent: str
    
    # Intencao detectada
    intent: Optional[str]
    
    # Contexto de recomendacao
    recommendations: List[dict]
    
    # Erro, se houver
    error: Optional[str]
```

### User Agent State (Agente do Usuario - LangGraph)

```python
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel

class StoreInfo(BaseModel):
    """Informacoes de uma loja descoberta"""
    url: str
    name: str
    capabilities: List[str]
    payment_handlers: List[str]
    last_discovered: datetime

class CartItem(BaseModel):
    """Item no carrinho do User Agent"""
    store_url: str
    book_id: str
    title: str
    price: int
    quantity: int

class UserAgentState(TypedDict):
    # Mensagens do chat com usuario
    messages: Annotated[List, add_messages]
    
    # Registro de lojas descobertas
    discovered_stores: Dict[str, StoreInfo]
    
    # Loja atualmente selecionada
    current_store: Optional[str]
    
    # Carrinho multi-loja
    cart: List[CartItem]
    
    # Sessao de checkout ativa
    checkout_session: Optional[dict]
    
    # Resultados da ultima busca
    search_results: List[dict]
    
    # Comparacao de precos
    price_comparison: List[dict]
    
    # Intencao detectada
    intent: Optional[str]
    
    # Recomendacoes recebidas via A2A
    recommendations: List[dict]
    
    # Erro, se houver
    error: Optional[str]
```

### A2A Message

```python
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
import uuid

class A2AMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str
    to_agent: str
    type: str  # 'request', 'response', 'event'
    action: str
    payload: dict = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
```

---

## Scripts de Execucao

### Setup Inicial (scripts/setup.sh)

```bash
#!/bin/bash
set -e

echo "=== Setup Livraria UCP ==="

# Backend
echo "Configurando backend..."
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Criar bancos
echo "Criando bancos de dados..."
mkdir -p data
python scripts/import_books.py

# Frontend
echo "Configurando frontend..."
cd ../frontend
npm install

echo "Setup completo!"
```

### Demo Backend + Frontend (scripts/run_demo.sh)

```bash
#!/bin/bash

echo "=== Iniciando Livraria UCP Demo ==="

# Iniciar UCP Server
echo "Iniciando UCP Server na porta 8182..."
cd backend
source .venv/bin/activate
uvicorn src.ucp_server.server:app --host 0.0.0.0 --port 8182 &
UCP_PID=$!

# Iniciar API Gateway
echo "Iniciando API Gateway na porta 8000..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Iniciar Frontend
echo "Iniciando Frontend na porta 5173..."
cd ../frontend
npm run dev &
FE_PID=$!

echo ""
echo "=== Servidores iniciados ==="
echo "UCP Server: http://localhost:8182"
echo "API Gateway: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Pressione Ctrl+C para parar todos os servidores"

# Trap para limpar processos
trap "kill $UCP_PID $API_PID $FE_PID 2>/dev/null" EXIT

# Aguardar
wait
```

### Demo User Agent (scripts/run_user_agent.sh)

```bash
#!/bin/bash

echo "=== Iniciando User Agent Demo ==="

cd user_agent
source .venv/bin/activate

# Modo interativo (CLI)
python -m src.main

# Ou modo especifico:
# python -m src.main discover http://localhost:8182
# python -m src.main search "Python" --store http://localhost:8182
# python -m src.main buy book_003 --store http://localhost:8182 --coupon TECH15
```

### User Agent CLI (user_agent/src/cli.py)

```python
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="User Agent - Agente autonomo para comercio UCP")
console = Console()

@app.command()
def discover(url: str = "http://localhost:8182"):
    """Descobrir capacidades de uma loja UCP"""
    from .agent.graph import create_agent
    from .clients.ucp_client import UCPClient
    
    client = UCPClient()
    profile = client.discover(url)
    
    table = Table(title=f"Capacidades de {url}")
    table.add_column("Capability", style="cyan")
    table.add_column("Version", style="green")
    
    for cap in profile.ucp.capabilities:
        table.add_row(cap.name, cap.version)
    
    console.print(table)

@app.command()
def search(query: str, store: str = "http://localhost:8182"):
    """Buscar produtos em uma loja"""
    from .clients.ucp_client import UCPClient
    
    client = UCPClient()
    results = client.search_books(store, query)
    
    table = Table(title=f"Resultados para '{query}'")
    table.add_column("ID", style="dim")
    table.add_column("Titulo", style="cyan")
    table.add_column("Autor")
    table.add_column("Preco", style="green")
    
    for book in results:
        price = f"R$ {book['price']/100:.2f}"
        table.add_row(book['id'], book['title'], book['author'], price)
    
    console.print(table)

@app.command()
def buy(
    book_id: str,
    store: str = "http://localhost:8182",
    coupon: str = None
):
    """Comprar um livro autonomamente"""
    from .agent.graph import create_agent
    
    agent = create_agent()
    result = agent.invoke({
        "messages": [f"Compre o livro {book_id} na loja {store}" + 
                    (f" com cupom {coupon}" if coupon else "")]
    })
    
    console.print(Panel(result["messages"][-1].content, title="Resultado"))

@app.command()
def chat():
    """Modo interativo de chat com o agente"""
    from .agent.graph import create_agent
    
    console.print(Panel("User Agent - Modo Chat", subtitle="Digite 'sair' para encerrar"))
    
    agent = create_agent()
    state = {"messages": []}
    
    while True:
        user_input = console.input("[bold blue]Voce:[/] ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break
        
        state["messages"].append({"role": "user", "content": user_input})
        result = agent.invoke(state)
        state = result
        
        response = result["messages"][-1].content
        console.print(f"[bold green]Agente:[/] {response}")

if __name__ == "__main__":
    app()
```

---

## Testes

### Estrutura de Testes

```
tests/
├── conftest.py           # Fixtures compartilhadas
├── test_discovery.py     # Testes de discovery UCP
├── test_checkout.py      # Testes de checkout
├── test_agents.py        # Testes de agentes
├── test_security.py      # Testes de AP2
└── integration/
    └── test_e2e.py       # Testes end-to-end
```

### Exemplo de Teste

```python
# tests/test_discovery.py
import pytest
from httpx import AsyncClient
from src.ucp_server.server import app

@pytest.mark.asyncio
async def test_discovery_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/.well-known/ucp")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "ucp" in data
        assert data["ucp"]["version"] == "2026-01-11"
        assert "capabilities" in data["ucp"]
        
        # Verificar checkout capability
        caps = {c["name"] for c in data["ucp"]["capabilities"]}
        assert "dev.ucp.shopping.checkout" in caps

@pytest.mark.asyncio
async def test_checkout_create():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/checkout-sessions",
            json={
                "line_items": [
                    {"item": {"id": "book_001", "title": "Test"}, "quantity": 1}
                ],
                "buyer": {"full_name": "Test", "email": "test@test.com"},
                "currency": "BRL"
            },
            headers={
                "UCP-Agent": 'profile="test"',
                "request-signature": "test",
                "idempotency-key": "test-key",
                "request-id": "test-id"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "ready_for_complete"
```

---

## Proximos Passos

1. **Implementar backend** seguindo a estrutura definida
2. **Configurar LangGraph** com os agentes especificados
3. **Desenvolver frontend** com componentes React
4. **Executar testes** de integracao
5. **Documentar API** com OpenAPI/Swagger
