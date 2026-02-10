# C4 Level 1: Diagrama de Contexto

## Visao Geral

O diagrama de contexto mostra a Livraria Virtual UCP e suas interacoes com usuarios, agentes externos e sistemas.

**Importante**: O UCP permite que **agentes externos** (criados por usuarios ou terceiros) acessem a loja diretamente, sem precisar passar pelo frontend. Isso e o diferencial do comercio agentivo.

## Diagrama de Contexto

```mermaid
C4Context
    title Sistema de Livraria Virtual UCP - Diagrama de Contexto

    Person(customer, "Cliente", "Usuario que deseja comprar livros")
    Person(developer, "Desenvolvedor", "Cria agentes que acessam a loja")
    Person(admin, "Administrador", "Gerencia catalogo e pedidos")

    System(bookstore, "Livraria Virtual UCP", "Sistema de e-commerce com suporte a agentes de IA via UCP, A2A, AP2 e MCP")
    System(user_agent, "User Agent", "Agente de IA autonomo com CLI (Typer/Rich) para interagir com lojas UCP")

    System_Ext(gemini, "Google Gemini", "LLM Principal - gemini-2.0-flash-lite")
    System_Ext(openai, "OpenAI/Anthropic", "LLM Fallback - GPT-4/Claude")
    System_Ext(payment, "Payment Gateway", "Processador de pagamentos (mock)")
    System_Ext(other_stores, "Outras Lojas UCP", "Outros e-commerces que implementam UCP")

    Rel(customer, bookstore, "Navega, conversa com agente, compra livros", "HTTPS/WebSocket")
    Rel(customer, user_agent, "Delega tarefas de compra", "CLI/Chat")
    Rel(developer, user_agent, "Desenvolve e configura", "Python/LangGraph")
    Rel(admin, bookstore, "Gerencia catalogo e pedidos", "HTTPS")
    
    Rel(user_agent, bookstore, "Discovery + Checkout", "UCP/A2A/AP2")
    Rel(user_agent, other_stores, "Discovery + Checkout", "UCP/A2A")
    
    Rel(bookstore, gemini, "Intent detection + Response generation", "HTTPS/API")
    Rel(user_agent, gemini, "Intent detection + Response generation", "HTTPS/API")
    Rel(bookstore, openai, "Fallback LLM", "HTTPS/API")
    Rel(bookstore, payment, "Processa pagamentos", "HTTPS/API")
```

## Diagrama Detalhado (Flowchart)

```mermaid
flowchart TB
    subgraph users [Usuarios]
        Customer[Cliente Final]
        Developer[Desenvolvedor]
        Admin[Administrador]
    end

    subgraph user_side [Lado do Usuario]
        Browser[Frontend Web<br/>React + Vite]
        UserAgent[User Agent<br/>LangGraph + CLI]
        CLI[CLI Typer/Rich]
    end

    subgraph store [Livraria Virtual UCP]
        Frontend[Frontend React<br/>:5173]
        APIGateway[API Gateway<br/>:8000]
        StoreAgents[Store Agents<br/>LangGraph + LLM]
        UCPServer[UCP Server<br/>:8182]
        MCPServer[MCP Server<br/>:8183]
        LLMModule[LLM Module<br/>Intent + Response]
    end

    subgraph external [Sistemas Externos]
        Gemini[Google Gemini<br/>gemini-2.0-flash-lite]
        OpenAI[OpenAI/Anthropic<br/>Fallback]
        OtherStores[Outras Lojas UCP]
    end

    Customer -->|Navega| Browser
    Customer -->|Delega tarefas| CLI
    Developer -->|Desenvolve| UserAgent
    Admin -->|Gerencia| Frontend

    Browser --> Frontend
    CLI --> UserAgent
    Frontend --> APIGateway
    APIGateway --> StoreAgents

    UserAgent -->|UCP Discovery| UCPServer
    UserAgent -->|A2A Protocol| StoreAgents
    UserAgent -->|MCP Tools| MCPServer
    UserAgent -->|Compra em outras lojas| OtherStores

    StoreAgents --> LLMModule
    LLMModule --> Gemini
    LLMModule -.->|Fallback| OpenAI
    UserAgent --> Gemini
```

## Dois Modos de Interacao

### Modo 1: Via Frontend (Tradicional)
O cliente acessa a loja pelo navegador e interage com os agentes da loja.

### Modo 2: Via User Agent (Agentivo)
O cliente usa seu proprio agente que descobre e interage com multiplas lojas UCP.

```mermaid
flowchart LR
    subgraph modo1 [Modo 1: Frontend]
        C1[Cliente] --> F1[Frontend]
        F1 --> A1[Agentes da Loja]
        A1 --> U1[UCP Server]
    end

    subgraph modo2 [Modo 2: User Agent]
        C2[Cliente] --> UA[User Agent]
        UA --> U2[UCP Loja A]
        UA --> U3[UCP Loja B]
        UA --> U4[UCP Loja C]
    end
```

## Descricao dos Elementos

### Pessoas/Atores

| Ator | Descricao | Interacoes |
|------|-----------|------------|
| **Cliente** | Usuario final que busca e compra livros | Usa frontend OU delega para seu User Agent |
| **Desenvolvedor** | Cria e configura agentes personalizados | Desenvolve User Agents com LangGraph |
| **Administrador** | Responsavel pela gestao da loja | Gerencia catalogo, pedidos, descontos |

### Sistemas

| Sistema | Tipo | Responsabilidade |
|---------|------|------------------|
| **Livraria Virtual UCP** | Principal | E-commerce com endpoints UCP, A2A, MCP |
| **User Agent** | Externo | Agente autonomo do usuario com CLI Typer/Rich |
| **Google Gemini** | Externo | LLM Principal - Intent detection e response generation |
| **OpenAI/Anthropic** | Externo | LLM Fallback - GPT-4/Claude como alternativa |
| **Outras Lojas UCP** | Externo | Demonstra interoperabilidade multi-loja |

## User Agent - O Agente do Usuario

O **User Agent** e um agente de IA que o usuario/desenvolvedor pode criar para:

1. **Descobrir lojas**: Acessa `/.well-known/ucp` de qualquer loja
2. **Comparar precos**: Consulta multiplas lojas simultaneamente
3. **Executar compras**: Realiza checkout autonomamente com AP2
4. **Receber recomendacoes**: Usa agentes da loja via A2A

### Capacidades do User Agent

```mermaid
mindmap
  root((User Agent))
    Discovery
      Descobrir lojas UCP
      Listar capabilities
      Identificar payment handlers
      Descobrir A2A agents
    Shopping
      Buscar produtos
      Comparar precos multi-loja
      Adicionar ao carrinho
      Aplicar cupons
    Checkout
      Criar sessao UCP
      Gerar mandato AP2
      3-Mandate Flow
      Completar pagamento
    Comunicacao
      A2A WebSocket
      MCP para ferramentas
      CLI Typer/Rich
    LLM
      Google Gemini
      Intent detection
      Response generation
      Fallback OpenAI
```

## Protocolos no Contexto

```mermaid
flowchart TB
    subgraph user_side [Lado do Usuario]
        UserAgent[User Agent]
    end

    subgraph protocols [Protocolos]
        UCP[UCP<br/>Discovery + Checkout]
        A2A[A2A<br/>Agent-to-Agent]
        AP2[AP2<br/>Pagamentos Seguros]
        MCP[MCP<br/>Ferramentas]
    end

    subgraph store_side [Lado da Loja]
        StoreAgents[Agentes da Loja]
        UCPServer[UCP Server]
        MCPServer[MCP Server]
    end

    UserAgent -->|GET /.well-known/ucp| UCP
    UCP -->|Capabilities| UCPServer

    UserAgent -->|Mensagens estruturadas| A2A
    A2A -->|Orquestracao| StoreAgents

    UserAgent -->|Mandatos JWT| AP2
    AP2 -->|Validacao| UCPServer

    UserAgent -->|Tool calls| MCP
    MCP -->|Execucao| MCPServer
```

## Fluxo de Alto Nivel com User Agent

```mermaid
flowchart TD
    A[Usuario quer comprar livro] --> B{Como interagir?}
    
    B -->|Frontend| C[Acessa loja pelo navegador]
    C --> D[Conversa com agente da loja]
    D --> E[Agente da loja faz checkout]
    
    B -->|User Agent| F[Pede ao seu agente]
    F --> G[User Agent descobre lojas UCP]
    G --> H[User Agent compara precos]
    H --> I[User Agent escolhe melhor opcao]
    I --> J[User Agent executa checkout]
    J --> K[User Agent gera mandato AP2]
    
    E --> L[Compra finalizada]
    K --> L
```

## Vantagens do Modelo com User Agent

| Aspecto | Sem User Agent | Com User Agent |
|---------|----------------|----------------|
| **Descoberta** | Manual, loja por loja | Automatica via UCP |
| **Comparacao** | Usuario compara manualmente | Agente compara automaticamente |
| **Checkout** | Preenche formularios | Autonomo com AP2 |
| **Personalizacao** | Limitada ao frontend | Totalmente customizavel |
| **Multi-loja** | Processos separados | Unificado pelo agente |

## Decisoes de Arquitetura

1. **Dual Mode**: Sistema suporta tanto frontend tradicional quanto acesso via User Agent
2. **UCP First**: Todas as operacoes de comercio passam pelo UCP Server
3. **A2A Aberto**: Agentes externos podem se comunicar com agentes da loja
4. **AP2 para Autonomia**: User Agent pode completar compras sem intervencao humana
5. **MCP para Extensibilidade**: Ferramentas expostas via MCP para qualquer agente
