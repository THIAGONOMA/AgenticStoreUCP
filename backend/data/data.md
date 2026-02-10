# Dados do Backend - Livraria Virtual UCP

Este diretório contém todos os dados persistidos do sistema da Livraria Virtual UCP, incluindo catálogo de produtos, códigos de desconto e bancos de dados transacionais.

## Visão Geral dos Arquivos

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `books_catalog.csv` | CSV | Catálogo inicial de livros para importação |
| `discount_codes.csv` | CSV | Códigos de desconto promocionais |
| `products.db` | SQLite | Banco de dados de produtos e descontos |
| `transactions.db` | SQLite | Banco de dados de transações e checkout |

---

## Arquivos CSV

### books_catalog.csv

Arquivo de catálogo contendo os livros disponíveis na livraria. Usado para importação inicial no banco de dados.

**Estrutura:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | string | Identificador único (ex: `book_001`) |
| `title` | string | Título do livro |
| `author` | string | Nome do autor |
| `description` | string | Descrição/sinopse do livro |
| `price` | integer | Preço em centavos (ex: 4990 = R$ 49,90) |
| `category` | string | Categoria do livro |
| `isbn` | string | Código ISBN único |
| `stock` | integer | Quantidade em estoque |

**Categorias disponíveis:**
- Tecnologia
- Ciência
- Programação
- Inteligência Artificial
- DevOps
- Segurança
- Frontend
- Arquitetura
- Data Science
- Qualidade
- Ferramentas
- Sistemas
- Gestão

**Exemplo de dados:**

```csv
id,title,author,description,price,category,isbn,stock
book_001,O Codigo do Futuro,Ana Silva,Uma jornada pela evolucao da programacao...,4990,Tecnologia,978-85-0001-001-0,50
book_003,Python para Todos,Maria Santos,Guia completo de Python para iniciantes...,3990,Programacao,978-85-0001-003-4,100
```

**Total de livros:** 20 títulos

---

### discount_codes.csv

Códigos promocionais de desconto disponíveis na loja.

**Estrutura:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `code` | string | Código do cupom (ex: `PRIMEIRA10`) |
| `title` | string | Descrição do desconto |
| `type` | string | Tipo: `percentage` ou `fixed` |
| `value` | integer | Valor (% ou centavos) |
| `min_purchase` | integer | Compra mínima em centavos |
| `max_uses` | integer | Máximo de usos (vazio = ilimitado) |

**Cupons disponíveis:**

| Código | Descrição | Tipo | Valor | Mínimo |
|--------|-----------|------|-------|--------|
| `PRIMEIRA10` | 10% na primeira compra | Percentual | 10% | - |
| `LIVROS20` | 20% em compras acima de R$100 | Percentual | 20% | R$ 100,00 |
| `FRETE0` | Frete Grátis | Fixo | R$ 0 | R$ 50,00 |
| `TECH15` | 15% em livros de Tecnologia | Percentual | 15% | - |
| `BEMVINDO` | R$10 de desconto de boas-vindas | Fixo | R$ 10,00 | R$ 20,00 |

---

## Bancos de Dados SQLite

### products.db

Banco de dados principal contendo produtos e configurações de desconto.

#### Tabela: `books`

Armazena os livros do catálogo.

```sql
CREATE TABLE books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,          -- Preço em centavos
    category TEXT,
    isbn TEXT UNIQUE,
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para otimização
CREATE INDEX idx_books_category ON books(category);
CREATE INDEX idx_books_author ON books(author);
```

#### Tabela: `discount_codes`

Armazena os códigos de desconto com controle de uso.

```sql
CREATE TABLE discount_codes (
    code TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL,              -- 'percentage' ou 'fixed'
    value INTEGER NOT NULL,          -- Valor do desconto
    min_purchase INTEGER DEFAULT 0,  -- Compra mínima em centavos
    max_uses INTEGER,                -- Máximo de usos (NULL = ilimitado)
    current_uses INTEGER DEFAULT 0,  -- Contador de usos
    valid_from TIMESTAMP,            -- Data de início da validade
    valid_until TIMESTAMP,           -- Data de fim da validade
    active INTEGER DEFAULT 1         -- 1 = ativo, 0 = inativo
);
```

---

### transactions.db

Banco de dados de transações, checkout e pagamentos.

#### Tabela: `buyers`

Armazena informações dos compradores.

```sql
CREATE TABLE buyers (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_buyers_email ON buyers(email);
```

#### Tabela: `checkout_sessions`

Sessões de checkout (carrinho e processo de compra).

```sql
CREATE TABLE checkout_sessions (
    id TEXT PRIMARY KEY,
    buyer_id TEXT,
    status TEXT DEFAULT 'draft',     -- draft, pending, completed, cancelled
    currency TEXT DEFAULT 'BRL',
    subtotal INTEGER DEFAULT 0,      -- Subtotal em centavos
    discount_total INTEGER DEFAULT 0, -- Total de descontos
    shipping_total INTEGER DEFAULT 0, -- Total de frete
    total INTEGER DEFAULT 0,          -- Total final
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id)
);
```

**Status possíveis:**
- `draft` - Carrinho em construção
- `pending` - Aguardando pagamento
- `completed` - Compra finalizada
- `cancelled` - Compra cancelada

#### Tabela: `line_items`

Itens individuais dentro de uma sessão de checkout.

```sql
CREATE TABLE line_items (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    book_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,     -- Preço unitário em centavos
    subtotal INTEGER NOT NULL,       -- quantity * unit_price
    discount INTEGER DEFAULT 0,      -- Desconto aplicado no item
    total INTEGER NOT NULL,          -- Valor final do item
    FOREIGN KEY (session_id) REFERENCES checkout_sessions(id)
);

CREATE INDEX idx_line_items_session ON line_items(session_id);
```

#### Tabela: `applied_discounts`

Descontos aplicados em uma sessão de checkout.

```sql
CREATE TABLE applied_discounts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    code TEXT NOT NULL,              -- Código do cupom
    title TEXT NOT NULL,             -- Descrição do desconto
    amount INTEGER NOT NULL,         -- Valor do desconto em centavos
    automatic INTEGER DEFAULT 0,     -- 1 = automático, 0 = manual
    allocation_path TEXT,            -- Caminho de alocação (linha/total)
    FOREIGN KEY (session_id) REFERENCES checkout_sessions(id)
);
```

#### Tabela: `payments`

Registros de pagamento (integração AP2).

```sql
CREATE TABLE payments (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    handler_id TEXT NOT NULL,        -- ID do handler de pagamento
    token TEXT,                      -- Token de pagamento
    mandate_jwt TEXT,                -- JWT do mandato AP2
    status TEXT DEFAULT 'pending',   -- pending, processing, completed, failed
    amount INTEGER NOT NULL,         -- Valor em centavos
    processed_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES checkout_sessions(id)
);
```

---

## Diagrama de Relacionamentos

```
┌─────────────────┐
│  products.db    │
├─────────────────┤
│  books          │◄─────────────────────────────────┐
│  discount_codes │◄──────────────────────┐          │
└─────────────────┘                       │          │
                                          │          │
┌─────────────────────────────────────────┼──────────┼─────────┐
│  transactions.db                        │          │         │
├─────────────────────────────────────────┴──────────┴─────────┤
│                                                               │
│  ┌───────────┐      ┌────────────────────┐                   │
│  │  buyers   │──1:N─│ checkout_sessions  │                   │
│  └───────────┘      └─────────┬──────────┘                   │
│                               │                               │
│                     ┌─────────┼─────────┐                    │
│                     │         │         │                    │
│                    1:N       1:N       1:N                   │
│                     │         │         │                    │
│                     ▼         ▼         ▼                    │
│              ┌──────────┐ ┌─────────┐ ┌──────────┐          │
│              │line_items│ │applied_ │ │ payments │          │
│              │          │ │discounts│ │          │          │
│              └──────────┘ └─────────┘ └──────────┘          │
│                    │           │                             │
│                    │           │                             │
│                    ▼           ▼                             │
│              (ref: books) (ref: discount_codes)              │
└──────────────────────────────────────────────────────────────┘
```

---

## Notas de Implementação

### Formato de Preços

Todos os valores monetários são armazenados em **centavos** (inteiros) para evitar problemas de precisão com ponto flutuante.

| Valor Display | Valor Armazenado |
|---------------|------------------|
| R$ 49,90 | 4990 |
| R$ 100,00 | 10000 |
| R$ 0,99 | 99 |

### Geração de IDs

Os IDs seguem os padrões:
- Livros: `book_XXX` (ex: `book_001`)
- Sessões: UUID v4
- Pagamentos: UUID v4
- Line Items: UUID v4

### Importação de Dados

Os arquivos CSV servem como fonte inicial de dados. Na inicialização do sistema, os dados são importados para os bancos SQLite correspondentes se as tabelas estiverem vazias.

---

## Uso com Protocolos

### UCP (Universal Commerce Protocol)

Os dados de `products.db` alimentam os endpoints de discovery e catálogo UCP.

### A2A (Agent-to-Agent)

Agentes externos consultam produtos via A2A usando dados de `products.db`.

### AP2 (Agent Payments Protocol)

A tabela `payments` armazena tokens e mandatos JWT para validação de pagamentos autônomos.

---

## Manutenção

### Backup

```bash
# Backup dos bancos de dados
cp backend/data/products.db backend/data/products.db.bak
cp backend/data/transactions.db backend/data/transactions.db.bak
```

### Reset dos Dados

Para reiniciar com dados limpos, remova os arquivos `.db` e reinicie o servidor. Os dados serão reimportados dos arquivos CSV.

```bash
rm backend/data/products.db backend/data/transactions.db
# Reiniciar o servidor para reimportar dados
```
