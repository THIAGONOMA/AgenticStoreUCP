# Plano de Execucao - Livraria Virtual UCP

## Resumo Executivo

Este projeto implementa uma **livraria virtual ficticia** que demonstra a integracao completa do ecossistema de protocolos para comercio agentivo:

- **UCP (Universal Commerce Protocol)** - Protocolo aberto do Google para comercio
- **A2A (Agent-to-Agent)** - Comunicacao entre agentes autonomos
- **AP2 (Agent Payments Protocol)** - Pagamentos seguros entre agentes
- **MCP (Model Context Protocol)** - Protocolo da Anthropic para contexto de modelos

O objetivo e criar uma demonstracao funcional onde agentes de IA podem descobrir, recomendar e realizar compras de livros de forma autonoma.

### Dois Modos de Interacao

O projeto demonstra **dois modos** de interacao com a loja:

1. **Via Frontend** - Usuario acessa a loja pelo navegador e interage com os agentes da loja
2. **Via User Agent** - Usuario usa seu proprio agente autonomo para acessar a loja (e outras lojas UCP)

```
+------------------+     +------------------+     +------------------+
|    Usuario       |     |    Usuario       |     |    Usuario       |
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         v                        v                        v
+--------+---------+     +--------+---------+     +--------+---------+
|    Frontend      |     |   User Agent     |     |   User Agent     |
|    (React)       |     |   (LangGraph)    |     |   (LangGraph)    |
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         v                        |                        |
+--------+---------+              |                        |
|  Store Agents    |<-------------+                        |
|  (Loja interna)  |                                       |
+--------+---------+                                       |
         |                                                 |
         v                                                 v
+--------+---------+                              +--------+---------+
|   UCP Server     |<-----------------------------+  Outras Lojas   |
|   (Livraria)     |                              |     UCP         |
+------------------+                              +------------------+
```

---

## Fases de Implementacao

### Fase 1: Fundacao (Infraestrutura Base)

| ID | Tarefa | Descricao | Entregavel |
|----|--------|-----------|------------|
| 1.1 | Setup do Projeto | Criar estrutura de pastas, configurar ambientes Python e Node | `pyproject.toml`, `package.json` |
| 1.2 | Banco de Dados | Implementar SQLite com modelos de livros e transacoes | `products.db`, `transactions.db` |
| 1.3 | Catalogo Inicial | Criar CSV com 20+ livros ficticios e script de importacao | `books_catalog.csv` |

**Criterio de Aceitacao:** Ambiente configurado, banco populado com dados de teste.

---

### Fase 2: Servidor UCP (Backend Core)

| ID | Tarefa | Descricao | Entregavel |
|----|--------|-----------|------------|
| 2.1 | Discovery Endpoint | Implementar `/.well-known/ucp` com perfil da livraria | `discovery.py` |
| 2.2 | Checkout Capability | CRUD de sessoes de checkout conforme spec UCP | `checkout.py` |
| 2.3 | Discount Extension | Aplicacao de cupons de desconto | `discount.py` |
| 2.4 | Fulfillment Extension | Opcoes de entrega e frete | `fulfillment.py` |
| 2.5 | Payment Handlers | Mock de handlers de pagamento | `payment.py` |

**Criterio de Aceitacao:** Servidor responde corretamente a requests UCP, validado contra SDK oficial.

---

### Fase 3: Seguranca AP2

| ID | Tarefa | Descricao | Entregavel |
|----|--------|-----------|------------|
| 3.1 | Key Manager | Gerenciamento de chaves Ed25519 | `key_manager.py` |
| 3.2 | AP2 Mandates | Geracao de mandatos JWT para pagamentos | `ap2_security.py` |
| 3.3 | Request Signatures | Assinatura e validacao de requests | `signatures.py` |

**Criterio de Aceitacao:** Transacoes assinadas criptograficamente, mandatos validos gerados.

---

### Fase 4: Camada MCP

| ID | Tarefa | Descricao | Entregavel |
|----|--------|-----------|------------|
| 4.1 | MCP Server | Servidor FastMCP expondo ferramentas | `server.py` |
| 4.2 | Tool Registry | Registry com deferred loading | `tool_registry.py` |
| 4.3 | UCP Proxy | Proxy para chamadas ao servidor UCP | `ucp_proxy.py` |
| 4.4 | Sandbox | Ambiente seguro para execucao de codigo | `sandbox.py` |

**Criterio de Aceitacao:** Ferramentas UCP acessiveis via protocolo MCP.

---

### Fase 5: Store Agents - Agentes da Loja (LangGraph)

| ID | Tarefa | Descricao | Entregavel |
|----|--------|-----------|------------|
| 5.1 | Estado Compartilhado | Definir TypedDict para estado dos agentes | `state.py` |
| 5.2 | Discovery Agent | Agente que descobre capacidades UCP | `discovery_agent.py` |
| 5.3 | Shopping Agent | Agente que executa checkout | `shopping_agent.py` |
| 5.4 | Recommend Agent | Agente que recomenda livros | `recommend_agent.py` |
| 5.5 | Orquestrador A2A | Coordenacao entre agentes | `orchestrator.py` |
| 5.6 | A2A Endpoint | Endpoint para receber requests de agentes externos | `a2a_endpoint.py` |

**Criterio de Aceitacao:** Agentes se comunicam via A2A, aceitam requests de agentes externos.

---

### Fase 6: User Agent - Agente do Usuario (Novo!)

O **User Agent** e um agente autonomo que o usuario executa em seu ambiente para interagir com lojas UCP. Este e o diferencial do comercio agentivo!

| ID | Tarefa | Descricao | Entregavel |
|----|--------|-----------|------------|
| 6.1 | UCP Client | Cliente HTTP para consumir APIs UCP | `ucp_client.py` |
| 6.2 | Stores Registry | Registro de lojas descobertas | `stores_registry.py` |
| 6.3 | Discovery Node | Node LangGraph para descobrir lojas | `nodes/discovery.py` |
| 6.4 | Shopping Node | Node para executar compras | `nodes/shopping.py` |
| 6.5 | Compare Node | Node para comparar precos | `nodes/compare.py` |
| 6.6 | A2A Client | Cliente para comunicar com Store Agents | `a2a_client.py` |
| 6.7 | AP2 Client | Geracao de mandatos para pagamentos | `ap2_client.py` |
| 6.8 | Main Graph | Grafo principal do User Agent | `agent.py` |
| 6.9 | CLI Interface | Interface de linha de comando (Rich/Typer) | `cli.py` |

**Criterio de Aceitacao:** User Agent consegue descobrir lojas, comparar precos e executar compras autonomamente.

**Estrutura do User Agent:**
```
user_agent/
├── __init__.py
├── agent.py              # Main LangGraph
├── cli.py                # CLI Interface
├── config.py             # Configuracoes
├── clients/
│   ├── ucp_client.py     # Cliente UCP
│   ├── a2a_client.py     # Cliente A2A
│   └── ap2_client.py     # Cliente AP2
├── nodes/
│   ├── discovery.py      # Discovery node
│   ├── shopping.py       # Shopping node
│   └── compare.py        # Compare node
├── state/
│   ├── agent_state.py    # Estado do agente
│   └── stores_registry.py # Registro de lojas
└── utils/
    └── formatters.py     # Formatacao de output
```

---

### Fase 7: Frontend React

| ID | Tarefa | Descricao | Entregavel |
|----|--------|-----------|------------|
| 7.1 | Setup Vite + React | Configurar projeto com Tailwind | Projeto React |
| 7.2 | Catalogo de Livros | Grid responsivo com cards | `BookCatalog.tsx` |
| 7.3 | Carrinho | Gerenciamento de itens | `Cart.tsx` |
| 7.4 | Checkout Flow | Interface de finalizacao | `Checkout.tsx` |
| 7.5 | Chat com Agente | Interface conversacional | `AgentChat.tsx` |
| 7.6 | WebSocket | Comunicacao em tempo real | `websocket.ts` |

**Criterio de Aceitacao:** Interface funcional, integrada com backend via API e WebSocket.

---

### Fase 8: Integracao e Demo

| ID | Tarefa | Descricao | Entregavel |
|----|--------|-----------|------------|
| 8.1 | Integracao E2E | Conectar todos os componentes | Sistema integrado |
| 8.2 | Testes | Testes de discovery, checkout e agentes | `tests/` |
| 8.3 | Script de Demo | Script para executar demonstracao | `run_demo.sh` |
| 8.4 | Demo User Agent | Script de demo do User Agent | `demo_user_agent.py` |
| 8.5 | Documentacao | README com instrucoes de uso | `README.md` |

**Criterio de Aceitacao:** Demo funcional executavel com um comando, mostrando ambos os modos de interacao.

---

## Checklist de Entregaveis

### Backend (Loja)
- [x] Servidor UCP funcional na porta 8182
- [x] Endpoint `/.well-known/ucp` retornando perfil valido
- [x] Checkout completo (criar, atualizar, completar)
- [x] Descontos aplicaveis via cupom
- [x] Seguranca AP2 com mandatos JWT
- [x] Servidor MCP expondo ferramentas

### Store Agents (Agentes da Loja)
- [x] Discovery Agent funcionando
- [x] Shopping Agent executando checkouts
- [x] Recommend Agent sugerindo livros
- [x] Orquestrador coordenando via A2A
- [x] A2A Endpoint para agentes externos

### User Agent (Agente do Usuario) - NOVO!
- [x] UCP Client consumindo APIs UCP
- [x] Discovery de multiplas lojas
- [x] Comparacao de precos entre lojas
- [x] Compra autonoma com AP2
- [x] Comunicacao A2A com Store Agents
- [x] CLI funcional com Rich/Typer

### Frontend
- [x] Catalogo de livros renderizando
- [x] Carrinho funcional
- [x] Chat com agente operacional
- [x] Checkout integrado com UCP

### Documentacao
- [x] Arquitetura documentada com diagramas
- [x] Especificacao tecnica completa
- [x] README com instrucoes

---

## Ordem de Execucao Recomendada

```
Fase 1 (Fundacao)
    |
    v
Fase 2 (Servidor UCP) -----> Fase 3 (AP2 Security)
    |                              |
    v                              v
Fase 4 (MCP Layer) <--------------+
    |
    v
Fase 5 (Store Agents) -----> Fase 6 (User Agent)
    |                              |
    v                              |
Fase 7 (Frontend React)            |
    |                              |
    v                              v
Fase 8 (Integracao e Demo) <-------+
```

**Nota**: As Fases 6 (User Agent) e 7 (Frontend) podem ser desenvolvidas em paralelo.

---

## Cenarios de Demo

### Demo 1: Compra via Frontend
1. Usuario acessa `http://localhost:5173`
2. Navega pelo catalogo de livros
3. Abre chat e pede: "Quero um livro sobre Python"
4. Agente da loja recomenda livros
5. Usuario adiciona ao carrinho
6. Usuario aplica cupom e finaliza compra

### Demo 2: Compra via User Agent
1. Usuario executa `python -m user_agent`
2. Digita: "Descubra lojas de livros"
3. User Agent faz discovery em `localhost:8182`
4. Usuario: "Busque livros sobre IA"
5. User Agent busca e mostra resultados
6. Usuario: "Compre o primeiro com cupom TECH15"
7. User Agent executa checkout completo com AP2

### Demo 3: User Agent com A2A
1. User Agent conecta via A2A com Store Agents
2. Pede recomendacoes personalizadas
3. Recebe sugestoes dos agentes da loja
4. Executa compra baseada na recomendacao

---

## Proximos Passos

Apos aprovar este plano, a execucao comeca pela **Fase 1** com a criacao da estrutura do projeto.
