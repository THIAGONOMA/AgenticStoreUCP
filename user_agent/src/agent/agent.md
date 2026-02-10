# Módulo Agent - User Agent (Agente Pessoal Genérico)

Este módulo implementa o **User Agent**, um agente pessoal autônomo e genérico que atua como assistente do usuário. O User Agent pode descobrir e interagir com agentes A2A, lojas UCP, usar ferramentas MCP e realizar compras autônomas com pagamento AP2.

## Visão Geral

O User Agent é um agente inteligente que:

- **Conversa** com o usuário de forma natural
- **Descobre e conecta** a agentes A2A e lojas UCP
- **Busca produtos** em múltiplas lojas
- **Gerencia carrinho** multi-loja
- **Compara preços** entre lojas
- **Realiza compras autônomas** com pagamento AP2 (3 mandatos)
- **Usa ferramentas MCP** para ações externas
- **Delega tarefas** para agentes especializados

---

## Arquitetura do Módulo

```
user_agent/src/agent/
├── __init__.py     # Exports públicos do módulo
├── state.py        # Estado compartilhado (UserAgentState)
├── graph.py        # Grafo LangGraph e Runner
├── llm.py          # Integração com LLM (Gemini/OpenAI)
├── agent.md        # Esta documentação
└── nodes/          # Nodes especializados
    ├── discovery.py    # Descoberta de lojas UCP
    ├── shopping.py     # Carrinho e checkout
    ├── compare.py      # Comparação de preços
    └── chat.py         # Conversa via A2A
```

### Diagrama de Arquitetura Geral

```mermaid
flowchart TB
    subgraph User["Usuário"]
        CLI["CLI Interface"]
    end

    subgraph Agent["Módulo Agent"]
        Runner["UserAgentRunner<br/>Gerencia estado"]
        
        subgraph Graph["LangGraph"]
            Router["router_node<br/>Detecção de intenção"]
            Question["question_node<br/>Perguntas gerais"]
            Chat["chat_node<br/>A2A"]
            Agents["agents_node<br/>Gerenciar A2A"]
            Discovery["discovery_node<br/>UCP Discovery"]
            Shopping["shopping_node<br/>Carrinho/Checkout"]
            Compare["compare_node<br/>Comparação"]
            MCP["mcp_node<br/>Ferramentas"]
            Help["help_node<br/>Ajuda"]
        end
        
        State["UserAgentState<br/>Estado compartilhado"]
        
        subgraph LLMModule["LLM Module"]
            LLM["llm.py<br/>Gemini/OpenAI"]
        end
    end

    subgraph External["Serviços Externos"]
        A2A["Agentes A2A<br/>via A2AClient"]
        UCP["Lojas UCP<br/>via UCPClient"]
        MCPTools["Servidores MCP<br/>via MCPClient"]
        AP2["AP2 Security<br/>Pagamento autônomo"]
    end

    CLI --> Runner
    Runner --> Graph
    Graph --> State
    
    Router --> LLM
    Question --> LLM
    Chat --> LLM
    
    Router --> Discovery
    Router --> Shopping
    Router --> Compare
    Router --> Chat
    Router --> Agents
    Router --> MCP
    
    Discovery --> UCP
    Shopping --> UCP
    Shopping --> AP2
    Chat --> A2A
    Agents --> A2A
    MCP --> MCPTools
    
    style Graph fill:#e3f2fd
    style LLMModule fill:#f3e5f5
    style External fill:#fff3e0
```

### Fluxo de Processamento

```mermaid
flowchart LR
    subgraph Entry["Entrada"]
        Msg["Mensagem do Usuário"]
    end

    subgraph Processing["Processamento"]
        Runner["UserAgentRunner"]
        Graph["user_agent_graph.ainvoke()"]
    end

    subgraph Output["Saída"]
        Response["Resposta"]
        State["Estado Atualizado"]
    end

    Msg --> Runner
    Runner --> Graph
    Graph --> Response
    Graph --> State
```

---

## Componentes Principais

### 1. State (`state.py`)

Define o estado compartilhado do User Agent usando TypedDict.

#### Diagrama de Estado

```mermaid
classDiagram
    class UserAgentState {
        <<TypedDict>>
        +str session_id
        +str user_name
        +str user_email
        +List~Message~ messages
        +str current_intent
        +Dict intent_params
        +float intent_confidence
        +bool llm_enabled
        +Dict~str,AgentInfo~ connected_agents
        +str active_agent_url
        +Dict~str,StoreInfo~ discovered_stores
        +str active_store_url
        +Dict~str,A2ASession~ a2a_sessions
        +str active_a2a_session
        +Dict~str,MCPToolInfo~ mcp_tools
        +List~str~ mcp_servers
        +str search_query
        +List~Dict~ search_results
        +List~Dict~ comparison_items
        +List~CartItem~ cart_items
        +int cart_total
        +str applied_discount
        +int discount_amount
        +bool checkout_in_progress
        +str checkout_store
        +str checkout_session_id
        +int checkout_total
        +AP2MandateInfo ap2_mandate
        +List~Dict~ recommendations
        +str next_action
        +str error
        +bool waiting_for_confirmation
        +Dict confirmation_context
    }
    
    class UserIntent {
        <<Enum>>
        QUESTION
        CHAT
        HELP
        DISCOVER_AGENT
        LIST_AGENTS
        TALK_TO_AGENT
        DISCOVER
        SEARCH
        COMPARE
        BUY
        ADD_TO_CART
        REMOVE_FROM_CART
        VIEW_CART
        CHECKOUT
        APPLY_DISCOUNT
        RECOMMEND
        USE_TOOL
        LIST_TOOLS
    }
    
    class AgentInfo {
        <<TypedDict>>
        +str url
        +str name
        +str description
        +str version
        +List~str~ skills
        +bool connected
    }
    
    class StoreInfo {
        <<TypedDict>>
        +str url
        +str name
        +str version
        +bool connected
        +List~str~ capabilities
        +bool a2a_connected
    }
    
    class CartItem {
        <<TypedDict>>
        +str store_url
        +str product_id
        +str title
        +int price
        +int quantity
    }
    
    class A2ASession {
        <<TypedDict>>
        +str store_url
        +str agent_id
        +bool connected
        +str last_message_id
        +List~str~ pending_responses
    }
    
    class AP2MandateInfo {
        <<TypedDict>>
        +str intent_mandate_id
        +str cart_mandate_id
        +str cart_mandate_jwt
        +str payment_mandate_id
        +str payment_mandate_jwt
        +int total_authorized
        +str currency
    }
    
    UserAgentState --> UserIntent
    UserAgentState --> AgentInfo
    UserAgentState --> StoreInfo
    UserAgentState --> CartItem
    UserAgentState --> A2ASession
    UserAgentState --> AP2MandateInfo
```

#### Categorias de Estado

```mermaid
flowchart TB
    subgraph State["UserAgentState"]
        subgraph ID["Identificação"]
            session_id
            user_name
            user_email
        end
        
        subgraph Conv["Conversa"]
            messages
            current_intent
            intent_params
            intent_confidence
        end
        
        subgraph Agents["Agentes A2A"]
            connected_agents
            active_agent_url
            a2a_sessions
            active_a2a_session
        end
        
        subgraph Stores["Lojas UCP"]
            discovered_stores
            active_store_url
        end
        
        subgraph Tools["Ferramentas MCP"]
            mcp_tools
            mcp_servers
        end
        
        subgraph Search["Busca"]
            search_query
            search_results
            comparison_items
        end
        
        subgraph Cart["Carrinho Multi-Loja"]
            cart_items
            cart_total
            applied_discount
            discount_amount
        end
        
        subgraph Checkout["Checkout"]
            checkout_in_progress
            checkout_store
            checkout_session_id
            checkout_total
            ap2_mandate
        end
        
        subgraph Flow["Controle"]
            next_action
            error
            waiting_for_confirmation
            confirmation_context
        end
    end
```

#### Intenções Suportadas

| Categoria | Intenção | Descrição |
|-----------|----------|-----------|
| **Geral** | `question` | Pergunta geral |
| **Geral** | `chat` | Conversa casual |
| **Geral** | `help` | Ajuda |
| **A2A** | `discover_agent` | Descobrir agente por URL |
| **A2A** | `list_agents` | Listar agentes conectados |
| **A2A** | `talk_to_agent` | Falar com agente específico |
| **UCP** | `discover` | Descobrir loja UCP |
| **UCP** | `search` | Buscar produtos |
| **UCP** | `compare` | Comparar produtos |
| **UCP** | `add_to_cart` | Adicionar ao carrinho |
| **UCP** | `remove_from_cart` | Remover do carrinho |
| **UCP** | `view_cart` | Ver carrinho |
| **UCP** | `checkout` | Finalizar compra |
| **UCP** | `apply_discount` | Aplicar cupom |
| **UCP** | `recommend` | Pedir recomendações |
| **MCP** | `use_tool` | Usar ferramenta MCP |
| **MCP** | `list_tools` | Listar ferramentas |

---

### 2. Graph (`graph.py`)

Configura e executa o grafo LangGraph do User Agent.

#### Diagrama do Grafo

```mermaid
flowchart TD
    Start((START)) --> Router["router_node"]
    
    Router --> Route{route_to_node}
    
    Route -->|"question"| Question["question_node"]
    Route -->|"agents"| Agents["agents_node"]
    Route -->|"mcp"| MCP["mcp_node"]
    Route -->|"discovery"| Discovery["discovery_node"]
    Route -->|"shopping"| Shopping["shopping_node"]
    Route -->|"compare"| Compare["compare_node"]
    Route -->|"chat"| Chat["chat_node"]
    Route -->|"help"| Help["help_node"]
    Route -->|"end"| End((END))
    
    Question --> End
    Agents --> End
    MCP --> End
    Discovery --> End
    Shopping --> End
    Compare --> End
    Chat --> End
    Help --> End
    
    style Router fill:#e3f2fd
    style Question fill:#c8e6c9
    style Agents fill:#fff9c4
    style Discovery fill:#ffccbc
    style Shopping fill:#f8bbd9
    style Compare fill:#e1bee7
    style Chat fill:#b2ebf2
    style MCP fill:#d1c4e9
```

#### Função `create_user_agent_graph()`

```mermaid
flowchart TD
    Start([create_user_agent_graph]) --> Create["workflow = StateGraph(UserAgentState)"]
    
    Create --> AddNodes["Adicionar nodes"]
    AddNodes --> N1["add_node('router')"]
    N1 --> N2["add_node('question')"]
    N2 --> N3["add_node('agents')"]
    N3 --> N4["add_node('mcp')"]
    N4 --> N5["add_node('discovery')"]
    N5 --> N6["add_node('shopping')"]
    N6 --> N7["add_node('compare')"]
    N7 --> N8["add_node('chat')"]
    N8 --> N9["add_node('help')"]
    
    N9 --> SetEntry["set_entry_point('router')"]
    
    SetEntry --> AddCond["add_conditional_edges(router, route_to_node)"]
    
    AddCond --> AddEnd1["add_edge('question', END)"]
    AddEnd1 --> AddEnd2["add_edge('agents', END)"]
    AddEnd2 --> AddEnd3["add_edge('mcp', END)"]
    AddEnd3 --> AddEnd4["add_edge('discovery', END)"]
    AddEnd4 --> AddEnd5["add_edge('shopping', END)"]
    AddEnd5 --> AddEnd6["add_edge('compare', END)"]
    AddEnd6 --> AddEnd7["add_edge('chat', END)"]
    AddEnd7 --> AddEnd8["add_edge('help', END)"]
    
    AddEnd8 --> Compile["workflow.compile()"]
    Compile --> Return([Retorna grafo compilado])
```

#### Detecção de Intenção com LLM

O router node usa LLM para detectar intenções de forma inteligente:

```mermaid
flowchart TD
    Start([router_node]) --> GetMessage[Pegar última mensagem]
    GetMessage --> CheckConfirm{Esperando confirmação?}
    
    CheckConfirm -->|Sim| HandleConfirm[_handle_confirmation]
    CheckConfirm -->|Não| CheckLLM{LLM disponível?}
    
    CheckLLM -->|Sim| LLMDetect[detect_intent_with_llm]
    CheckLLM -->|Não| RulesDetect[_detect_intent_keywords]
    
    LLMDetect --> MapIntent[Mapear intent para action]
    RulesDetect --> MapIntent
    HandleConfirm --> MapIntent
    
    MapIntent --> Return([Retorna next_action])
```

#### Classe `UserAgentRunner`

Runner principal que gerencia estado e executa o grafo.

```mermaid
classDiagram
    class UserAgentRunner {
        +UserAgentState state
        +A2AClient _a2a_client
        +initialize(session_id, user_name, user_email) void
        +process_message(message) str
        +is_llm_enabled() bool
        +get_status() Dict
        +get_connected_agents() Dict
        +get_a2a_sessions() Dict
        +connect_agent(agent_url) bool
        +get_discovered_stores() Dict
        +get_cart_summary() Dict
        +connect_store_a2a(store_url) bool
        +disconnect_a2a() void
        +get_mcp_tools() Dict
        +register_mcp_server(server_url) bool
    }
```

##### Métodos Principais

| Método | Parâmetros | Retorno | Descrição |
|--------|------------|---------|-----------|
| `initialize` | session_id, user_name?, user_email? | void | Inicializar estado |
| `process_message` | message | str | Processar mensagem do usuário |
| `get_status` | - | Dict | Obter status geral |
| `connect_agent` | agent_url | bool | Conectar a agente A2A |
| `connect_store_a2a` | store_url | bool | Conectar a loja via A2A |
| `register_mcp_server` | server_url | bool | Registrar servidor MCP |

##### Fluxo `process_message`

```mermaid
sequenceDiagram
    participant U as Usuário
    participant R as UserAgentRunner
    participant G as user_agent_graph
    participant S as state

    U->>R: process_message(message)
    R->>R: Criar Message do usuário
    R->>R: Montar input_state
    
    R->>G: ainvoke(input_state)
    G->>G: router_node(state)
    G->>G: Node especializado
    G-->>R: result (novo estado)
    
    R->>S: state = result
    R->>R: Extrair mensagem do assistente
    
    R-->>U: Resposta (str)
```

---

### 3. LLM Module (`llm.py`)

Módulo de integração com LLMs (Gemini/OpenAI) para melhorar a experiência conversacional.

#### Funcionalidades

- **Detecção de Intenção** - Usa LLM para detectar intenções de forma inteligente
- **Geração de Respostas** - Gera respostas naturais e contextualizadas
- **Formatação de Resultados** - Formata resultados de busca de forma amigável
- **Fallback para Keywords** - Usa regras baseadas em keywords quando LLM não disponível

#### Diagrama de Integração

```mermaid
flowchart LR
    subgraph LLM["llm.py"]
        Detect["detect_intent_with_llm()"]
        Generate["generate_response()"]
        Format["format_search_results_with_llm()"]
        Config["get_llm()"]
    end
    
    subgraph Nodes["Nodes"]
        Router["router_node"]
        Question["question_node"]
        Chat["chat_node"]
    end
    
    subgraph Providers["LLM Providers"]
        Gemini["Google Gemini"]
        OpenAI["OpenAI"]
    end
    
    Router --> Detect
    Question --> Generate
    Chat --> Generate
    
    Detect --> Config
    Generate --> Config
    Format --> Config
    
    Config --> Gemini
    Config --> OpenAI
```

#### Funções Principais

| Função | Descrição | Retorno |
|--------|-----------|---------|
| `detect_intent_with_llm(message, agents, stores, ...)` | Detecta intenção usando LLM | Dict com intent, params, confidence |
| `generate_response(message, context, system_prompt)` | Gera resposta natural | str |
| `format_search_results_with_llm(results, query)` | Formata resultados de busca | str |
| `is_llm_enabled()` | Verifica se LLM está configurado | bool |
| `get_llm()` | Obtém instância do LLM | ChatGoogleGenerativeAI \| ChatOpenAI \| None |

#### System Prompt

O User Agent usa um system prompt específico que define suas capacidades:

```
Você é um assistente pessoal inteligente chamado User Agent.
Você é o agente autônomo do usuário, capaz de realizar diversas tarefas.

Suas capacidades principais:
1. CONVERSAÇÃO GERAL
2. DESCOBERTA DE AGENTES (A2A)
3. COMÉRCIO AUTÔNOMO (UCP)
4. FERRAMENTAS EXTERNAS (MCP)

Você é o representante autônomo do usuário. Quando precisar fazer uma compra,
VOCÊ gera o mandato de pagamento (AP2) - a autorização está com você.
```

#### Fluxo de Detecção de Intenção

```mermaid
sequenceDiagram
    participant Router as router_node
    participant LLM as llm.py
    participant Provider as Gemini/OpenAI

    Router->>LLM: detect_intent_with_llm(message, context)
    LLM->>LLM: Formatar prompt com contexto
    LLM->>Provider: ainvoke(prompt)
    Provider-->>LLM: JSON response
    LLM->>LLM: Parse JSON
    LLM-->>Router: {intent, params, confidence}
    
    alt LLM não disponível
        Router->>LLM: _detect_intent_keywords(message)
        LLM-->>Router: {intent, params, confidence: 0.7}
    end
```

---

## Submódulos

### Nodes (Nodes Especializados)

O submódulo `nodes/` contém os nodes especializados do User Agent.

```mermaid
flowchart LR
    subgraph Nodes["nodes/"]
        Discovery["discovery.py<br/>Descoberta UCP"]
        Shopping["shopping.py<br/>Carrinho/Checkout"]
        Compare["compare.py<br/>Comparação"]
        Chat["chat.py<br/>A2A Chat"]
    end
    
    Router["router_node"] -->|discover/search| Discovery
    Router -->|cart/checkout| Shopping
    Router -->|compare| Compare
    Router -->|talk_to_agent| Chat
```

| Node | Responsabilidade | Intenções |
|------|------------------|-----------|
| **discovery** | Descobrir lojas UCP, buscar produtos | discover, search, recommend |
| **shopping** | Carrinho multi-loja, checkout, AP2 | add_to_cart, remove_from_cart, view_cart, checkout, apply_discount |
| **compare** | Comparar preços entre lojas | compare |
| **chat** | Conversa via A2A com Store Agents | talk_to_agent, chat |

#### Discovery Node

Responsável por descobrir lojas UCP e buscar produtos.

**Funcionalidades:**
- Descobrir lojas por URL via UCP discovery
- Buscar produtos em lojas conectadas
- Formatar resultados de busca

**Fluxo:**

```mermaid
sequenceDiagram
    participant Router as router_node
    participant Discovery as discovery_node
    participant UCP as UCPClient
    participant Store as Loja UCP

    Router->>Discovery: intent=discover/search
    Discovery->>Discovery: Extrair URL ou query
    
    alt Descobrir Loja
        Discovery->>UCP: discover(url)
        UCP->>Store: GET /.well-known/ucp
        Store-->>UCP: UCP Profile
        UCP-->>Discovery: StoreInfo
        Discovery->>Discovery: Adicionar a discovered_stores
    else Buscar Produtos
        Discovery->>UCP: search(query)
        UCP->>Store: GET /books/search?q=query
        Store-->>UCP: Products[]
        UCP-->>Discovery: search_results
    end
    
    Discovery-->>Router: {messages, discovered_stores, search_results}
```

#### Shopping Node

Gerencia carrinho multi-loja e checkout com AP2.

**Funcionalidades:**
- Adicionar/remover itens do carrinho (multi-loja)
- Aplicar cupons de desconto
- Criar checkout sessions via UCP
- Executar pagamento com AP2 (3 mandatos)
- Integração com VirtualWallet para controle de saldo

**Integração com Wallet:**
O shopping_node usa a VirtualWallet para verificar saldo e debitar compras:

```python
from user_agent.src.wallet import get_wallet

wallet = get_wallet()

# Verificar se pode pagar
if wallet.can_pay(checkout_total):
    # Gerar token de pagamento
    token = wallet.generate_payment_token(session_id)
    # Completar checkout...
    # Debitar carteira
    wallet.debit(checkout_total, f"Compra {session_id}")
```

**Fluxo de Checkout:**

```mermaid
sequenceDiagram
    participant Router as router_node
    participant Shopping as shopping_node
    participant UCP as UCPClient
    participant AP2 as AP2 Security
    participant Store as Loja UCP

    Router->>Shopping: intent=checkout
    Shopping->>Shopping: Preparar resumo do carrinho
    Shopping-->>Router: Pedir confirmação
    
    Router->>Shopping: intent=execute_checkout (confirmado)
    
    Shopping->>AP2: Criar Intent Mandate
    AP2-->>Shopping: intent_mandate_jwt
    
    Shopping->>UCP: create_checkout_session(cart_items)
    UCP->>Store: POST /checkout-sessions
    Store-->>UCP: checkout_session_id
    UCP-->>Shopping: session_id
    
    Shopping->>AP2: Criar Cart Mandate
    AP2-->>Shopping: cart_mandate_jwt
    
    Shopping->>UCP: complete_checkout(session_id, cart_mandate_jwt)
    UCP->>Store: POST /checkout-sessions/{id}/complete
    Store->>Store: Validar cart mandate
    Store->>AP2: Validar cart mandate
    AP2-->>Store: Valid
    Store->>AP2: Criar Payment Mandate
    AP2-->>Store: payment_mandate_jwt
    Store-->>UCP: CheckoutSession (completed)
    UCP-->>Shopping: Success
    
    Shopping->>Shopping: Limpar carrinho
    Shopping-->>Router: Compra concluída
```

#### Compare Node

Compara produtos entre lojas para encontrar melhores preços.

**Funcionalidades:**
- Comparar produtos por índices dos resultados
- Comparação automática de produtos similares
- Formatação de comparação com melhor preço destacado

#### Chat Node

Conversa via A2A com Store Agents.

**Funcionalidades:**
- Conectar via A2A a lojas
- Enviar mensagens ao Store Agent
- Processar respostas e manter contexto
- Fallback para busca direta se A2A falhar

---

## Exports do Módulo

O `__init__.py` exporta os seguintes componentes:

```python
from user_agent.src.agent import (
    # Estado
    UserAgentState,
    create_initial_state,
    Message,
    CartItem,
    StoreInfo,
    AgentInfo,
    MCPToolInfo,
    A2ASession,
    AP2MandateInfo,
    UserIntent,
    
    # Grafo
    user_agent_graph,
    UserAgentRunner,
    
    # LLM
    is_llm_enabled,
    get_llm,
    detect_intent_with_llm,
)
```

### Diagrama de Exports

```mermaid
flowchart TB
    subgraph Module["agent/__init__.py"]
        subgraph FromState["from state.py"]
            UserAgentState
            create_initial_state
            Message
            CartItem
            StoreInfo
            AgentInfo
            MCPToolInfo
            A2ASession
            AP2MandateInfo
            UserIntent
        end
        
        subgraph FromGraph["from graph.py"]
            user_agent_graph
            UserAgentRunner
        end
        
        subgraph FromLLM["from llm.py"]
            is_llm_enabled
            get_llm
            detect_intent_with_llm
        end
    end
```

---

## Fluxos de Uso

### Fluxo de Descoberta de Loja

```mermaid
sequenceDiagram
    participant U as Usuário
    participant R as UserAgentRunner
    participant G as user_agent_graph
    participant D as discovery_node
    participant UCP as UCPClient

    U->>R: "descobrir http://localhost:8182"
    R->>G: ainvoke(state)
    G->>G: router_node (intent=discover)
    G->>D: discovery_node(state)
    D->>UCP: discover(url)
    UCP->>UCP: GET /.well-known/ucp
    UCP-->>D: StoreInfo
    D-->>G: {discovered_stores: {...}}
    G-->>R: result
    R-->>U: "✅ Loja descoberta: Livraria Virtual UCP"
```

### Fluxo de Busca e Compra

```mermaid
sequenceDiagram
    participant U as Usuário
    participant R as Runner
    participant D as Discovery
    participant S as Shopping
    participant AP2 as AP2

    Note over U,AP2: 1. Buscar Produtos
    U->>R: "buscar python"
    R->>D: discovery_node
    D-->>U: Lista de livros

    Note over U,AP2: 2. Adicionar ao Carrinho
    U->>R: "adicionar 1"
    R->>S: shopping_node
    S-->>U: "Adicionado! Total: R$ 39,90"

    Note over U,AP2: 3. Finalizar Compra
    U->>R: "comprar"
    R->>S: shopping_node (checkout)
    S-->>U: "Confirmar compra? Total: R$ 39,90"

    Note over U,AP2: 4. Confirmar e Pagar (AP2)
    U->>R: "sim"
    R->>S: shopping_node (execute_checkout)
    S->>AP2: Criar mandatos (intent, cart, payment)
    AP2-->>S: JWTs
    S->>S: Completar checkout via UCP
    S-->>U: "✅ Compra concluída!"
```

### Fluxo de Conversa A2A

```mermaid
sequenceDiagram
    participant U as Usuário
    participant R as Runner
    participant C as chat_node
    participant A2A as A2AClient
    participant Store as Store Agent

    U->>R: "perguntar ao agente: tem livros de python?"
    R->>C: chat_node
    C->>C: Verificar sessão A2A
    
    alt Sessão não existe
        C->>A2A: connect(store_url)
        A2A->>Store: CONNECT
        Store-->>A2A: RESPONSE (connected)
        A2A-->>C: Connected
    end
    
    C->>A2A: send_message(message)
    A2A->>Store: REQUEST {action: "search", query: "python"}
    Store->>Store: Processar com Store Agents
    Store-->>A2A: RESPONSE {products: [...]}
    A2A-->>C: Response
    C-->>R: Mensagem formatada
    R-->>U: "Sim! Encontrei 5 livros..."
```

---

## Gerenciamento de Estado

### Ciclo de Vida do Estado

```mermaid
stateDiagram-v2
    [*] --> Initialized: initialize()
    Initialized --> Active: process_message()
    Active --> Active: process_message()
    Active --> Waiting: waiting_for_confirmation
    Waiting --> Active: Confirmação recebida
    Active --> [*]: Fim da sessão
    
    note right of Active: Estado persiste entre mensagens<br/>Mantém contexto completo
```

### Estado Multi-Loja

O User Agent mantém estado separado para múltiplas lojas:

```mermaid
flowchart TB
    subgraph State["UserAgentState"]
        subgraph Stores["Lojas Descobertas"]
            Store1["http://localhost:8182<br/>Livraria Virtual UCP"]
            Store2["http://outra-loja:8182<br/>Outra Loja"]
        end
        
        subgraph Cart["Carrinho Multi-Loja"]
            Item1["Store1: Python Book<br/>R$ 39,90"]
            Item2["Store2: JS Book<br/>R$ 29,90"]
        end
        
        subgraph Sessions["Sessões A2A"]
            Session1["Store1: A2A Session"]
            Session2["Store2: A2A Session"]
        end
    end
```

---

## Integração com Outros Módulos

```mermaid
flowchart TB
    subgraph Agent["Módulo Agent"]
        Runner
        Graph
        State
        Nodes
    end
    
    subgraph Integrations["Integrações"]
        A2AClient["clients/A2AClient<br/>Comunicação A2A"]
        UCPClient["clients/UCPClient<br/>Comunicação UCP"]
        MCPClient["clients/MCPClient<br/>Ferramentas MCP"]
        AP2Client["security/AP2Client<br/>Pagamento Autônomo"]
    end
    
    subgraph External["Externo"]
        CLI["CLI Interface"]
        A2AAgents["Agentes A2A"]
        UCPStores["Lojas UCP"]
        MCPServers["Servidores MCP"]
    end
    
    CLI --> Runner
    Runner --> Graph
    Graph --> State
    Graph --> Nodes
    
    Nodes --> A2AClient
    Nodes --> UCPClient
    Nodes --> MCPClient
    Nodes --> AP2Client
    
    A2AClient --> A2AAgents
    UCPClient --> UCPStores
    MCPClient --> MCPServers
    AP2Client --> UCPStores
```

---

## Instâncias Globais

O módulo exporta uma instância global do grafo:

```python
# Grafo compilado (imutável)
user_agent_graph = create_user_agent_graph()
```

### Uso Recomendado

```python
from user_agent.src.agent import UserAgentRunner

# Criar runner
runner = UserAgentRunner()
runner.initialize(session_id="sess_123", user_name="João")

# Processar mensagem
response = await runner.process_message("buscar livros de python")

# Verificar status
status = runner.get_status()
print(f"Lojas: {status['stores_count']}, Carrinho: {status['cart_count']}")
```

---

## Dependências

```mermaid
flowchart TB
    subgraph External["Externas"]
        langgraph["langgraph<br/>StateGraph, END"]
        structlog["structlog<br/>Logging"]
        langchain["langchain-google-genai<br/>ChatGoogleGenerativeAI"]
        langchain_openai["langchain-openai<br/>ChatOpenAI"]
    end
    
    subgraph Internal["Internas"]
        clients["../clients/<br/>A2AClient, UCPClient, MCPClient"]
        security["../security/<br/>AP2Client"]
        config["../config<br/>settings"]
    end
    
    subgraph Agent["Módulo Agent"]
        state["state.py"]
        graph["graph.py"]
        llm["llm.py"]
        nodes["nodes/"]
    end
    
    graph --> langgraph
    graph --> structlog
    graph --> state
    graph --> nodes
    graph --> llm
    
    nodes --> state
    nodes --> clients
    nodes --> security
    
    llm --> langchain
    llm --> langchain_openai
    llm --> config
```

---

## Referências

- **Clients:** [`../clients/client.md`](../clients/client.md)
- **Security:** [`../security/`](../security/)
- **Config:** [`../config.py`](../config.py)
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Google Gemini:** https://ai.google.dev/
- **OpenAI:** https://platform.openai.com/
