# Lista de Documentações do Projeto

Este arquivo lista todos os arquivos `.md` de documentação do projeto Livraria Virtual UCP, organizados por categoria.

---

## Índice

- [Documentação Raiz](#documentação-raiz)
- [Documentação Geral (docs/)](#documentação-geral-docs)
- [Arquitetura (docs/architecture/)](#arquitetura-docsarchitecture)
- [Building (docs/building/)](#building-docsbuilding)
- [Backend (backend/)](#backend-backend)
- [UCP Server (backend/src/ucp_server/)](#ucp-server-backendsrcucp_server)
- [Agents (backend/src/agents/)](#agents-backendsrcagents)
- [MCP (backend/src/mcp/)](#mcp-backendsrcmcp)
- [User Agent (user_agent/)](#user-agent-user_agent)
- [Frontend (frontend/)](#frontend-frontend)

---

## Documentação Raiz

| Arquivo | Caminho | Descrição |
|---------|---------|-----------|
| **README.md** | [`README.md`](../README.md) | Documentação principal do projeto. Visão geral, instalação, execução e estrutura. |

---

## Documentação Geral (docs/)

| Arquivo | Caminho | Descrição |
|---------|---------|-----------|
| **guide.md** | [`docs/guide.md`](guide.md) | Guia completo de instalação e execução. Pré-requisitos, configuração, execução de serviços e troubleshooting. |
| **CHANGELOG.md** | [`docs/CHANGELOG.md`](CHANGELOG.md) | Histórico de mudanças do projeto. Versões, features, correções e migrações de SDK. |
| **techSpec.md** | [`docs/techSpec.md`](techSpec.md) | Especificação técnica completa. Protocolos (UCP, A2A, MCP, AP2), tecnologias e decisões arquiteturais. |
| **listdocs.md** | [`docs/listdocs.md`](listdocs.md) | Este arquivo. Lista de todas as documentações do projeto. |

---

## Arquitetura (docs/architecture/)

| Arquivo | Caminho | Descrição |
|---------|---------|-----------|
| **README.md** | [`docs/architecture/README.md`](architecture/README.md) | Índice da documentação de arquitetura. Guia de navegação dos diagramas C4. |
| **overview.md** | [`docs/architecture/overview.md`](architecture/overview.md) | Diagrama de Contexto (C4 Level 1). Visão geral do sistema e atores externos. |
| **containers.md** | [`docs/architecture/containers.md`](architecture/containers.md) | Diagrama de Containers (C4 Level 2). Frontend, Backend, UCP Server, databases. |
| **components.md** | [`docs/architecture/components.md`](architecture/components.md) | Diagrama de Componentes (C4 Level 3). Detalhes internos de cada container. |
| **flows.md** | [`docs/architecture/flows.md`](architecture/flows.md) | Diagramas de Sequência e Atividade. Fluxos de compra, busca, checkout e A2A. |
| **data-model.md** | [`docs/architecture/data-model.md`](architecture/data-model.md) | Modelo de Dados (ER Diagram). Estrutura das tabelas SQLite e relacionamentos. |

---

## Building (docs/building/)

| Arquivo | Caminho | Descrição |
|---------|---------|-----------|
| **basicPlan.md** | [`docs/building/basicPlan.md`](building/basicPlan.md) | Plano de implementação do projeto. Fases, critérios de aceitação e checklist. |
| **testPlan.md** | [`docs/building/testPlan.md`](building/testPlan.md) | Plano de testes. Testes unitários, integração, E2E e critérios de aceitação. |

---

## Backend (backend/)

| Arquivo | Caminho | Descrição |
|---------|---------|-----------|
| **data.md** | [`backend/data/data.md`](../backend/data/data.md) | Documentação dos dados e bancos SQLite. Estrutura de `products.db` e `transactions.db`. |
| **src.md** | [`backend/src/src.md`](../backend/src/src.md) | Documentação principal do backend. Arquitetura, módulos, SDKs oficiais e fluxos. |
| **db.md** | [`backend/src/db/db.md`](../backend/src/db/db.md) | Camada de persistência. Repositories, conexões e operações de banco de dados. |
| **security.md** | [`backend/src/security/security.md`](../backend/src/security/security.md) | Módulo de segurança AP2 (SDK Google). Mandatos JWT, chaves Ed25519 e assinaturas. |

---

## UCP Server (backend/src/ucp_server/)

| Arquivo | Caminho | Descrição |
|---------|---------|-----------|
| **ucp.md** | [`backend/src/ucp_server/ucp.md`](../backend/src/ucp_server/ucp.md) | Servidor Universal Commerce Protocol. Discovery, rotas e integração com SDK oficial. |
| **capabilities.md** | [`backend/src/ucp_server/capabilities/capabilities.md`](../backend/src/ucp_server/capabilities/capabilities.md) | Capabilities UCP. Checkout, Discount e Fulfillment com especificações detalhadas. |
| **models.md** | [`backend/src/ucp_server/models/models.md`](../backend/src/ucp_server/models/models.md) | Modelos Pydantic UCP. Checkout, catálogo, pagamentos e tipos de dados. |
| **routes.md** | [`backend/src/ucp_server/routes/routes.md`](../backend/src/ucp_server/routes/routes.md) | Rotas HTTP do UCP Server. Endpoints REST para catálogo e checkout. |
| **services.md** | [`backend/src/ucp_server/services/services.md`](../backend/src/ucp_server/services/services.md) | Serviços UCP. Shopping service, payment handlers e lógica de negócio. |

---

## Agents (backend/src/agents/)

| Arquivo | Caminho | Descrição |
|---------|---------|-----------|
| **agents.md** | [`backend/src/agents/agents.md`](../backend/src/agents/agents.md) | Sistema de agentes LangGraph. State, Graph, Runner e orquestração. |
| **a2a.md** | [`backend/src/agents/a2a/a2a.md`](../backend/src/agents/a2a/a2a.md) | Protocolo Agent-to-Agent (SDK oficial). Handlers, adapters e comunicação entre agentes. |
| **nodes.md** | [`backend/src/agents/nodes/nodes.md`](../backend/src/agents/nodes/nodes.md) | Agent Nodes. Discovery, Shopping, Recommend e processamento de intenções. |

---

## MCP (backend/src/mcp/)

| Arquivo | Caminho | Descrição |
|---------|---------|-----------|
| **mcp.md** | [`backend/src/mcp/mcp.md`](../backend/src/mcp/mcp.md) | Model Context Protocol (SDK FastMCP). Servidor, HTTP API e progressive disclosure. |
| **tools.md** | [`backend/src/mcp/tools/tools.md`](../backend/src/mcp/tools/tools.md) | Ferramentas MCP. 7 tools disponíveis: search, cart, checkout, discount, etc. |

---

## User Agent (user_agent/)

| Arquivo | Caminho | Descrição |
|---------|---------|-----------|
| **userAgent.md** | [`user_agent/userAgent.md`](../user_agent/userAgent.md) | Documentação principal do User Agent. Agente pessoal autônomo, CLI, arquitetura e fluxos. |
| **agent.md** | [`user_agent/src/agent/agent.md`](../user_agent/src/agent/agent.md) | Módulo Agent (LangGraph). Estado compartilhado, grafo, nodes e integração com LLM. |
| **client.md** | [`user_agent/src/clients/client.md`](../user_agent/src/clients/client.md) | Clientes de Protocolo. UCPClient, A2AClient, MCPClient e integração com serviços externos. |
| **ap2.md** | [`user_agent/src/security/ap2.md`](../user_agent/src/security/ap2.md) | Segurança AP2. AP2Client, UserKeyManager e fluxo de 3 mandatos para pagamentos autônomos. |

---

## Frontend (frontend/)

| Arquivo | Caminho | Descrição |
|---------|---------|-----------|
| **front.md** | [`frontend/front.md`](../frontend/front.md) | Documentação completa do frontend React. Componentes, hooks, estado global, integração com backend e fluxos de uso. |

---

## Resumo por Categoria

| Categoria | Qtd | Descrição |
|-----------|-----|-----------|
| **Raiz** | 1 | README principal |
| **docs/** | 4 | Guia de instalação, changelog, spec técnica, lista de docs |
| **docs/architecture/** | 6 | Diagramas C4 e fluxos |
| **docs/building/** | 2 | Planos de implementação e testes |
| **backend/** | 4 | Dados, source, DB e security |
| **backend/ucp_server/** | 5 | UCP Server completo |
| **backend/agents/** | 3 | Sistema de agentes |
| **backend/mcp/** | 2 | MCP e ferramentas |
| **user_agent/** | 4 | User Agent completo |
| **frontend/** | 1 | Frontend React |
| **Total** | **32** | Arquivos de documentação |

---

## SDKs Externos (Referência)

Os SDKs oficiais clonados em `sdk/` possuem sua própria documentação:

| SDK | Localização | Documentação Principal |
|-----|-------------|------------------------|
| **UCP Python** | `sdk/ucp-python/` | `sdk/ucp-python/README.md` |
| **AP2 (Google)** | `sdk/ap2-repo/` | `sdk/ap2-repo/README.md` |

> **Nota:** A documentação dos SDKs não está listada aqui pois são repositórios externos. Consulte diretamente os READMEs de cada SDK para mais detalhes.

---

## Mapa Visual

```
FuturesUCP/
├── README.md                              # Documentação principal
│
├── docs/
│   ├── listdocs.md                        # Este arquivo
│   ├── guide.md                           # Guia de instalação e execução
│   ├── CHANGELOG.md                       # Histórico de mudanças
│   ├── techSpec.md                        # Especificação técnica
│   │
│   ├── architecture/
│   │   ├── README.md                      # Índice arquitetura
│   │   ├── overview.md                    # C4 Level 1 - Contexto
│   │   ├── containers.md                  # C4 Level 2 - Containers
│   │   ├── components.md                  # C4 Level 3 - Componentes
│   │   ├── flows.md                       # Diagramas de sequência
│   │   └── data-model.md                  # Modelo de dados (ER)
│   │
│   └── building/
│       ├── basicPlan.md                   # Plano de implementação
│       └── testPlan.md                    # Plano de testes
│
└── backend/
    ├── data/
    │   └── data.md                        # Dados e SQLite
    │
    └── src/
        ├── src.md                         # Backend principal
        │
        ├── db/
        │   └── db.md                      # Persistência
        │
        ├── security/
        │   └── security.md                # AP2 Security (SDK Google)
        │
        ├── mcp/
        │   ├── mcp.md                     # MCP Server (FastMCP)
        │   └── tools/
        │       └── tools.md               # Ferramentas MCP
        │
        ├── agents/
        │   ├── agents.md                  # Sistema de agentes
        │   ├── a2a/
        │   │   └── a2a.md                 # Protocolo A2A (SDK)
        │   └── nodes/
        │       └── nodes.md               # Agent Nodes
        │
        └── ucp_server/
            ├── ucp.md                     # UCP Server (SDK)
            ├── capabilities/
            │   └── capabilities.md        # Capabilities UCP
            ├── models/
            │   └── models.md              # Modelos Pydantic
            ├── routes/
            │   └── routes.md              # Rotas HTTP
            └── services/
                └── services.md            # Serviços UCP
    │
    ├── user_agent/
    │   ├── userAgent.md                   # User Agent principal
    │   └── src/
    │       ├── agent/
    │       │   └── agent.md               # Agente LangGraph
    │       ├── clients/
    │       │   └── client.md              # Clientes de Protocolo
    │       └── security/
    │           └── ap2.md                # Segurança AP2
    │
    └── frontend/
        └── front.md                       # Frontend React
```

---

## Como Navegar

1. **Instalação:** Siga o [`docs/guide.md`](guide.md) para instalar e executar todos os serviços
2. **Começando:** Leia o [`README.md`](../README.md) para visão geral
3. **Arquitetura:** Siga a ordem em [`docs/architecture/README.md`](architecture/README.md)
4. **Técnico:** Consulte [`docs/techSpec.md`](techSpec.md) para detalhes de protocolos
5. **Backend:** Entre em [`backend/src/src.md`](../backend/src/src.md) e siga os links
6. **User Agent:** Entre em [`user_agent/userAgent.md`](../user_agent/userAgent.md) e siga os links
7. **Frontend:** Consulte [`frontend/front.md`](../frontend/front.md) para detalhes da interface web
8. **Mudanças:** Acompanhe o [`docs/CHANGELOG.md`](CHANGELOG.md)

---

*Última atualização: 2026-02-04*
