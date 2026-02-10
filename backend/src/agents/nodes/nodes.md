# Módulo Nodes - LangGraph Agent Nodes

Este módulo implementa os **nodes** do grafo de agentes LangGraph para a Livraria Virtual UCP. Cada node representa um agente especializado que processa uma parte específica do fluxo de interação.

## Visão Geral

O módulo nodes contém:
- **Orchestrator** - Roteador principal que detecta intenções e direciona o fluxo
- **Discovery** - Busca de livros e informações sobre a loja
- **Shopping** - Gerenciamento de carrinho e checkout
- **Recommend** - Sistema de recomendações de livros

---

## Arquitetura do Módulo

```
backend/src/agents/nodes/
├── __init__.py      # Exports públicos dos nodes
├── orchestrator.py  # Node orquestrador/roteador
├── discovery.py     # Node de busca e descoberta
├── shopping.py      # Node de carrinho e checkout
├── recommend.py     # Node de recomendações
└── nodes.md         # Esta documentação
```

### Diagrama de Arquitetura

```mermaid
flowchart TB
    subgraph Input["Entrada"]
        User[Usuário/Chat]
        A2A[Requisição A2A]
    end

    subgraph Nodes["LangGraph Nodes"]
        Orch["orchestrator_node<br/>Detecta intenção e roteia"]
        
        subgraph Specialized["Nodes Especializados"]
            Disc["discovery_node<br/>Busca e informações"]
            Shop["shopping_node<br/>Carrinho e checkout"]
            Rec["recommend_node<br/>Recomendações"]
        end
    end

    subgraph Services["Serviços"]
        ProductsDB[(products_repo)]
        DiscountsDB[(discounts_repo)]
        TransactionsDB[(transactions_repo)]
    end

    User --> Orch
    A2A --> Orch
    
    Orch -->|search/help| Disc
    Orch -->|cart/checkout/discount| Shop
    Orch -->|recommend| Rec
    
    Disc --> ProductsDB
    Shop --> ProductsDB
    Shop --> DiscountsDB
    Shop --> TransactionsDB
    Rec --> ProductsDB
```

### Diagrama do Grafo LangGraph

```mermaid
flowchart TD
    Start((Start)) --> Orch[orchestrator_node]
    
    Orch --> Router{route_to_agent}
    
    Router -->|discovery| Disc[discovery_node]
    Router -->|shopping| Shop[shopping_node]
    Router -->|recommend| Rec[recommend_node]
    Router -->|end| End((End))
    
    Disc --> End
    Shop --> End
    Rec --> End
    
    style Orch fill:#e3f2fd
    style Disc fill:#e8f5e9
    style Shop fill:#fff3e0
    style Rec fill:#fce4ec
```

---

## Estado Compartilhado

Todos os nodes compartilham o estado `StoreAgentState` definido em `state.py`.

### Diagrama de Estado

```mermaid
classDiagram
    class StoreAgentState {
        +str session_id
        +str user_id
        +List~Message~ messages
        +str current_intent
        +List~CartItem~ cart_items
        +int cart_total
        +str applied_discount
        +str checkout_session_id
        +str checkout_status
        +str search_query
        +List~Dict~ search_results
        +str selected_book_id
        +List~Dict~ recommendations
        +str next_agent
        +str error
        +str external_agent_id
        +Dict a2a_request
    }
    
    class Message {
        +str role
        +str content
        +str type
        +Dict metadata
    }
    
    class CartItem {
        +str book_id
        +str title
        +int quantity
        +int price
    }
    
    class AgentRole {
        <<enumeration>>
        ORCHESTRATOR
        DISCOVERY
        SHOPPING
        RECOMMEND
        SUPPORT
    }
    
    StoreAgentState --> Message
    StoreAgentState --> CartItem
    StoreAgentState --> AgentRole
```

---

## Nodes Detalhados

### 1. Orchestrator Node (`orchestrator.py`)

O nó orquestrador é o ponto de entrada do grafo. Analisa a mensagem do usuário, detecta a intenção e roteia para o agente apropriado.

#### Funções Exportadas

| Função | Tipo | Descrição |
|--------|------|-----------|
| `orchestrator_node` | async node | Processa estado e define próximo agente |
| `route_to_agent` | routing func | Função de roteamento para o grafo |
| `detect_intent` | helper | Detecta intenção da mensagem |

#### Detecção de Intenção

```mermaid
flowchart LR
    subgraph Keywords["Palavras-chave"]
        R["recomend, suger, similar"]
        S["buscar, procurar, quero"]
        C["carrinho, adicionar"]
        K["comprar, finalizar, pagar"]
        D["cupom, desconto"]
        H["ajuda, ola, oi"]
    end
    
    subgraph Intents["Intenções"]
        IR[recommend]
        IS[search]
        IC[cart]
        IK[checkout]
        ID[discount]
        IH[help]
    end
    
    R --> IR
    S --> IS
    C --> IC
    K --> IK
    D --> ID
    H --> IH
```

#### Mapeamento Intenção → Agente

```mermaid
flowchart LR
    subgraph Intents["Intenções Detectadas"]
        search
        help
        recommend
        cart
        checkout
        discount
    end
    
    subgraph Agents["Agentes de Destino"]
        DISCOVERY
        SHOPPING
        RECOMMEND
    end
    
    search --> DISCOVERY
    help --> DISCOVERY
    recommend --> RECOMMEND
    cart --> SHOPPING
    checkout --> SHOPPING
    discount --> SHOPPING
```

#### Código Principal

```python
async def orchestrator_node(state: StoreAgentState) -> Dict[str, Any]:
    """
    Decide para qual agente rotear baseado na mensagem.
    
    Returns:
        next_agent: Nome do próximo agente
        current_intent: Intenção detectada
    """
```

#### Tratamento A2A

Quando recebe uma requisição A2A, o orchestrator mapeia a ação diretamente:

| Ação A2A | Agente |
|----------|--------|
| `search`, `get_products` | DISCOVERY |
| `checkout`, `create_order` | SHOPPING |
| `recommend` | RECOMMEND |

---

### 2. Discovery Node (`discovery.py`)

Node responsável por busca de livros e informações sobre a loja.

#### Responsabilidades

- Buscar livros por termo
- Listar categorias disponíveis
- Fornecer detalhes de livros
- Responder perguntas sobre a loja (help)

#### Diagrama de Fluxo

```mermaid
flowchart TD
    Start([discovery_node]) --> A2A{É requisição A2A?}
    
    A2A -->|Sim| A2AHandler[_handle_a2a_request]
    A2A -->|Não| Intent{Qual intenção?}
    
    Intent -->|help| Help[_get_help_message]
    Intent -->|search| Extract[_extract_search_term]
    
    Extract --> HasTerm{Tem termo?}
    HasTerm -->|Sim| Search[products_repo.search]
    HasTerm -->|Não| Categories[Listar categorias]
    
    Search --> Found{Encontrou?}
    Found -->|Sim| Format[_format_search_results]
    Found -->|Não| NotFound["Não encontrei..."]
    
    A2AHandler --> End([Retorna estado])
    Help --> End
    Format --> End
    NotFound --> End
    Categories --> End
```

#### Funções Internas

| Função | Descrição |
|--------|-----------|
| `_handle_a2a_request` | Processa requisições A2A (search, get_products) |
| `_extract_search_term` | Remove stop words e extrai termo de busca |
| `_get_help_message` | Retorna mensagem de boas-vindas |
| `_format_search_results` | Formata resultados para exibição |
| `_format_categories` | Formata lista de categorias |

#### Exemplo de Saída

```python
{
    "messages": [Message(...)],
    "search_results": [
        {"id": "book_001", "title": "...", "price": 4990, ...}
    ],
    "search_query": "python",
    "next_agent": None  # Fim do fluxo
}
```

---

### 3. Shopping Node (`shopping.py`)

Node responsável pelo gerenciamento do carrinho e processo de checkout.

#### Responsabilidades

- Adicionar/remover itens do carrinho
- Aplicar cupons de desconto
- Criar sessões de checkout
- Processar pedidos A2A

#### Diagrama de Fluxo

```mermaid
flowchart TD
    Start([shopping_node]) --> A2A{É requisição A2A?}
    
    A2A -->|Sim| A2ACheckout[_handle_a2a_checkout]
    A2A -->|Não| Intent{Qual intenção?}
    
    Intent -->|cart| CartAction{Ação?}
    Intent -->|discount| Discount[Aplicar cupom]
    Intent -->|checkout| Checkout[Criar checkout]
    
    CartAction -->|adicionar| Add[_add_to_cart]
    CartAction -->|remover| Remove[_remove_from_cart]
    CartAction -->|ver| View[_format_cart]
    
    Add --> UpdateState[Atualizar cart_items]
    Remove --> UpdateState
    
    Discount --> Validate[discounts_repo.validate]
    Validate -->|válido| ApplyDiscount[Aplicar desconto]
    Validate -->|inválido| InvalidCode[Cupom inválido]
    
    Checkout --> HasItems{Tem itens?}
    HasItems -->|Sim| CreateCheckout[_create_checkout]
    HasItems -->|Não| Empty[Carrinho vazio]
    
    CreateCheckout --> CreateBuyer[transactions_repo.create_buyer]
    CreateBuyer --> CreateSession[transactions_repo.create_session]
    
    A2ACheckout --> End([Retorna estado])
    UpdateState --> End
    View --> End
    ApplyDiscount --> End
    InvalidCode --> End
    CreateSession --> End
    Empty --> End
```

#### Funções Internas

| Função | Descrição |
|--------|-----------|
| `_add_to_cart` | Adiciona item ao carrinho (por índice ou busca) |
| `_remove_from_cart` | Remove item do carrinho por índice |
| `_create_checkout` | Cria sessão de checkout completa |
| `_handle_a2a_checkout` | Processa checkout via A2A |
| `_format_cart` | Formata carrinho para exibição |
| `_extract_discount_code` | Extrai código de cupom da mensagem |

#### Fluxo de Checkout

```mermaid
sequenceDiagram
    participant U as Usuário
    participant S as Shopping Node
    participant T as transactions_repo
    participant D as discounts_repo

    U->>S: "finalizar compra"
    S->>T: create_buyer(email, name)
    T-->>S: buyer_id
    S->>T: create_session(buyer_id, line_items)
    T-->>S: checkout_id
    
    alt Tem cupom
        S->>D: validate_and_calculate(code, total)
        D-->>S: (valid, discount_amount)
        S->>T: apply_discount(checkout_id, code)
    end
    
    S->>T: get_session(checkout_id)
    T-->>S: session_details
    S-->>U: "Checkout criado! ID: xxx"
```

---

### 4. Recommend Node (`recommend.py`)

Node responsável pelo sistema de recomendações de livros.

#### Responsabilidades

- Recomendar por livro selecionado
- Recomendar por categorias do carrinho
- Recomendar por categoria mencionada
- Listar livros populares

#### Diagrama de Fluxo

```mermaid
flowchart TD
    Start([recommend_node]) --> A2A{É requisição A2A?}
    
    A2A -->|Sim| A2ARec[_handle_a2a_recommend]
    A2A -->|Não| Context{Qual contexto?}
    
    Context -->|selected_book_id| ByBook[_recommend_by_book]
    Context -->|cart_items| ByCart[_recommend_by_categories]
    Context -->|categoria na msg| ByCat[_recommend_by_category]
    Context -->|nenhum| Popular[_get_popular_books]
    
    ByBook --> Format[_format_recommendations]
    ByCart --> Format
    ByCat --> Format
    Popular --> Format
    
    A2ARec --> End([Retorna estado])
    Format --> End
```

#### Estratégias de Recomendação

```mermaid
flowchart LR
    subgraph Input["Contexto de Entrada"]
        Book["Livro selecionado"]
        Cart["Itens no carrinho"]
        Category["Categoria mencionada"]
        None["Sem contexto"]
    end
    
    subgraph Strategy["Estratégia"]
        SameGenre["Mesmo gênero"]
        CartCategories["Categorias do carrinho"]
        CategoryBooks["Livros da categoria"]
        Popular["Populares/Aleatório"]
    end
    
    subgraph Output["Saída"]
        Recs["5 recomendações<br/>com reason"]
    end
    
    Book --> SameGenre --> Recs
    Cart --> CartCategories --> Recs
    Category --> CategoryBooks --> Recs
    None --> Popular --> Recs
```

#### Funções Internas

| Função | Descrição |
|--------|-----------|
| `_recommend_by_book` | Recomenda livros da mesma categoria |
| `_recommend_by_category` | Recomenda livros de uma categoria |
| `_recommend_by_categories` | Recomenda de múltiplas categorias |
| `_get_popular_books` | Retorna livros "populares" (mock) |
| `_handle_a2a_recommend` | Processa recomendações A2A |
| `_extract_category` | Extrai categoria da mensagem |
| `_format_recommendations` | Formata recomendações para exibição |

#### Exemplo de Saída

```python
{
    "messages": [Message(...)],
    "recommendations": [
        {
            "id": "book_003",
            "title": "Python para Todos",
            "author": "Maria Santos",
            "price": 3990,
            "price_formatted": "R$ 39,90",
            "category": "Programacao",
            "reason": "Mesmo gênero: Programacao"
        }
    ],
    "search_results": [...],  # Permite adicionar ao carrinho
    "next_agent": None
}
```

---

## Fluxos de Interação

### Fluxo Completo de Compra (Chat)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant O as Orchestrator
    participant D as Discovery
    participant S as Shopping
    participant R as Recommend

    U->>O: "Olá"
    O->>D: intent=help
    D-->>U: "Bem-vindo! Posso ajudar com..."

    U->>O: "Buscar livros de Python"
    O->>D: intent=search
    D-->>U: "Encontrei: 1. Python para Todos..."

    U->>O: "Me recomende similares"
    O->>R: intent=recommend
    R-->>U: "Recomendações: 1. Data Science..."

    U->>O: "Adicionar 1 ao carrinho"
    O->>S: intent=cart
    S-->>U: "Adicionado! Total: R$ 39,90"

    U->>O: "Aplicar cupom PROMO10"
    O->>S: intent=discount
    S-->>U: "Cupom aplicado! Novo total: R$ 35,91"

    U->>O: "Finalizar compra"
    O->>S: intent=checkout
    S-->>U: "Checkout criado! ID: xxx..."
```

### Fluxo A2A

```mermaid
sequenceDiagram
    participant A as Agente Externo
    participant O as Orchestrator
    participant D as Discovery
    participant S as Shopping

    A->>O: a2a_request: {action: "search", payload: {query: "python"}}
    O->>D: route to discovery
    D-->>A: {search_results: [...]}

    A->>O: a2a_request: {action: "create_order", payload: {items: [...]}}
    O->>S: route to shopping
    S-->>A: {checkout_session_id: "xxx", cart_total: 7980}
```

---

## Diagrama de Classes

```mermaid
classDiagram
    class orchestrator_node {
        +process(state) Dict
    }
    
    class discovery_node {
        +process(state) Dict
        -_handle_a2a_request(state) Dict
        -_extract_search_term(msg) str
        -_get_help_message() str
        -_format_search_results(results) str
        -_format_categories(cats) str
    }
    
    class shopping_node {
        +process(state) Dict
        -_add_to_cart(msg, state, items) Dict
        -_remove_from_cart(msg, items) Dict
        -_create_checkout(items, total, discount, session) Dict
        -_handle_a2a_checkout(state) Dict
        -_format_cart(items, total, discount) str
        -_extract_discount_code(msg) str
    }
    
    class recommend_node {
        +process(state) Dict
        -_recommend_by_book(book_id) List
        -_recommend_by_category(cat) List
        -_recommend_by_categories(cats) List
        -_get_popular_books() List
        -_handle_a2a_recommend(state) Dict
        -_extract_category(msg) str
        -_format_recommendations(recs, ctx) str
    }
    
    class route_to_agent {
        +route(state) Literal
    }
    
    class detect_intent {
        +detect(message) str
    }
    
    orchestrator_node --> route_to_agent
    orchestrator_node --> detect_intent
    orchestrator_node ..> discovery_node : routes to
    orchestrator_node ..> shopping_node : routes to
    orchestrator_node ..> recommend_node : routes to
```

---

## Dependências

### Dependências por Node

```mermaid
flowchart TB
    subgraph Nodes
        O[orchestrator]
        D[discovery]
        S[shopping]
        R[recommend]
    end
    
    subgraph State["../state.py"]
        StoreAgentState
        Message
        CartItem
        AgentRole
    end
    
    subgraph DB["../../db/"]
        products_repo
        discounts_repo
        transactions_repo
    end
    
    O --> StoreAgentState
    O --> AgentRole
    
    D --> StoreAgentState
    D --> Message
    D --> products_repo
    
    S --> StoreAgentState
    S --> Message
    S --> CartItem
    S --> products_repo
    S --> discounts_repo
    S --> transactions_repo
    
    R --> StoreAgentState
    R --> Message
    R --> products_repo
```

### Tabela de Dependências

| Node | state.py | products_repo | discounts_repo | transactions_repo |
|------|----------|---------------|----------------|-------------------|
| orchestrator | ✅ | - | - | - |
| discovery | ✅ | ✅ | - | - |
| shopping | ✅ | ✅ | ✅ | ✅ |
| recommend | ✅ | ✅ | - | - |

---

## Exports do Módulo

O `__init__.py` exporta as seguintes funções:

```python
from .orchestrator import orchestrator_node
from .discovery import discovery_node
from .shopping import shopping_node
from .recommend import recommend_node

__all__ = [
    "orchestrator_node",
    "discovery_node",
    "shopping_node",
    "recommend_node",
]
```

### Uso no Grafo

```python
from langgraph.graph import StateGraph
from backend.src.agents.nodes import (
    orchestrator_node,
    discovery_node,
    shopping_node,
    recommend_node
)
from backend.src.agents.nodes.orchestrator import route_to_agent

# Criar grafo
graph = StateGraph(StoreAgentState)

# Adicionar nodes
graph.add_node("orchestrator", orchestrator_node)
graph.add_node("discovery", discovery_node)
graph.add_node("shopping", shopping_node)
graph.add_node("recommend", recommend_node)

# Configurar roteamento
graph.add_conditional_edges(
    "orchestrator",
    route_to_agent,
    {
        "discovery": "discovery",
        "shopping": "shopping",
        "recommend": "recommend",
        "end": END
    }
)
```

---

## Tratamento de Erros

Todos os nodes seguem o padrão de tratamento de erros:

```mermaid
flowchart TD
    Node[Node Processing] --> TryCatch{try/except}
    
    TryCatch -->|success| Return[Retorna estado atualizado]
    TryCatch -->|error| Log[logger.error]
    Log --> ErrorState[Retorna estado com error]
    
    Return --> End([next_agent = None])
    ErrorState --> End
```

### Logs Estruturados

Todos os nodes usam `structlog` para logging estruturado:

```python
logger.info("Node processing", session=state["session_id"])
logger.info("Intent detected", intent=intent, message=message[:50])
logger.error("Processing error", error=str(e))
```
