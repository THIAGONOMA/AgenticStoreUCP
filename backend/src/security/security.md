# Módulo Security - Segurança AP2 e Criptografia

Este módulo implementa a camada de segurança da Livraria Virtual UCP, fornecendo:
- **AP2 Security** - Mandatos JWT para pagamentos autônomos (SDK Oficial Google)
- **Key Manager** - Gerenciamento de chaves Ed25519
- **Request Signatures** - Assinaturas de requisições UCP

## Visão Geral

O módulo security fornece:
- **Mandatos AP2 Oficiais** - IntentMandate, CartMandate, PaymentMandate
- **Chaves Ed25519** - Par de chaves pública/privada para assinaturas
- **Assinaturas de Requisições** - Headers de conformidade UCP com assinaturas criptográficas

---

## Arquitetura do Módulo

```
backend/src/security/
├── __init__.py          # Exports públicos
├── key_manager.py       # Gerenciador de chaves Ed25519
├── ap2_security.py      # Mandatos JWT AP2 (orquestração)
├── ap2_types.py         # Tipos oficiais AP2 (re-exportados do SDK)
├── ap2_adapters.py      # Adaptadores e funções de conversão
├── signatures.py        # Assinaturas de requisições
└── security.md          # Esta documentação
```

### Diagrama de Arquitetura

```mermaid
flowchart TB
    subgraph Clients["Clientes"]
        Agent["AI Agent<br/>(Pagamento Autônomo)"]
        UCPClient["UCP Client<br/>(Requisições Assinadas)"]
    end

    subgraph Security["Módulo Security"]
        subgraph AP2["AP2 Security (SDK Oficial Google)"]
            AP2Sec["AP2Security<br/>create_intent_mandate()<br/>create_cart_mandate()<br/>create_payment_mandate()"]
            AP2Types["ap2_types.py<br/>IntentMandate<br/>CartMandate<br/>PaymentMandate"]
            AP2Adapt["ap2_adapters.py<br/>sign_cart_mandate()<br/>validate_cart_mandate()"]
        end
        
        subgraph Keys["Key Management"]
            KeyMgr["KeyManager<br/>sign()<br/>verify()<br/>get_public_jwk()"]
        end
        
        subgraph Signatures["Request Signatures"]
            ReqSigner["RequestSigner<br/>sign_request()<br/>verify_request()"]
            ConformHeaders["ConformanceHeaders<br/>generate()"]
        end
    end

    subgraph SDK["SDK Oficial"]
        GoogleSDK["google-agentic-commerce/AP2<br/>sdk/ap2-repo/"]
    end

    subgraph Crypto["Criptografia"]
        Ed25519["Ed25519<br/>cryptography"]
        JWT["JWT<br/>Base64URL"]
    end

    Agent --> AP2Sec
    UCPClient --> ReqSigner
    
    AP2Sec --> AP2Types
    AP2Sec --> AP2Adapt
    AP2Types --> GoogleSDK
    AP2Adapt --> KeyMgr
    ReqSigner --> KeyMgr
    
    KeyMgr --> Ed25519
    AP2Sec --> JWT
    
    style AP2 fill:#e3f2fd
    style Keys fill:#fff3e0
    style Signatures fill:#e8f5e9
    style SDK fill:#f3e5f5
```

---

## Componentes Detalhados

### 1. Key Manager (`key_manager.py`)

Gerenciador de chaves Ed25519 para assinaturas criptográficas.

#### Diagrama de Classes

```mermaid
classDiagram
    class KeyManager {
        -Ed25519PrivateKey _private_key
        -Ed25519PublicKey _public_key
        +str key_id
        +sign(data: str) str
        +verify(data: str, signature: str) bool
        +get_public_jwk() Dict
        +get_private_bytes() bytes
        +from_private_bytes(bytes, key_id) KeyManager
    }
    
    class Ed25519PrivateKey {
        <<cryptography>>
        +sign(data) bytes
        +public_key() Ed25519PublicKey
    }
    
    class Ed25519PublicKey {
        <<cryptography>>
        +verify(signature, data) void
    }
    
    KeyManager --> Ed25519PrivateKey
    KeyManager --> Ed25519PublicKey
```

#### Fluxo de Geração de Chaves

```mermaid
flowchart TD
    Start([KeyManager.__init__]) --> Generate[Ed25519PrivateKey.generate]
    Generate --> GetPublic[private_key.public_key]
    GetPublic --> GetBytes[public_key.public_bytes]
    GetBytes --> Encode[base64url_encode(primeiros 8 bytes)]
    Encode --> CreateID["key_id = 'key-' + hash"]
    CreateID --> End([Chave pronta])
```

#### Métodos Principais

| Método | Descrição | Retorno |
|--------|-----------|---------|
| `sign(data)` | Assina dados com chave privada | Assinatura base64url |
| `verify(data, signature)` | Verifica assinatura | bool |
| `get_public_jwk()` | Exporta chave pública em formato JWK | Dict JWK |
| `get_private_bytes()` | Obtém bytes da chave privada (backup) | bytes |
| `from_private_bytes(bytes, key_id)` | Restaura KeyManager de backup | KeyManager |

#### Formato JWK

```json
{
    "kty": "OKP",
    "crv": "Ed25519",
    "x": "base64url_encoded_public_key",
    "kid": "key-abc123",
    "use": "sig",
    "alg": "EdDSA"
}
```

---

### 2. AP2 Types (`ap2_types.py`)

Re-exporta os tipos oficiais do SDK Google AP2.

#### Tipos Principais

```mermaid
classDiagram
    class IntentMandate {
        +str description
        +List~str~ allowed_merchants
        +List~str~ allowed_skus
        +bool requires_user_confirmation
        +bool supports_refund
        +datetime intent_expiry
    }
    
    class CartContents {
        +str id
        +str merchant_agent_id
        +PaymentRequest payment_request
        +bool require_payment_confirmation
        +datetime cart_expiry
    }
    
    class CartMandate {
        +CartContents contents
        +str merchant_authorization
    }
    
    class PaymentMandateContents {
        +str payment_mandate_id
        +str payment_details_id
        +str merchant_agent_id
        +PaymentMethodData selected_payment_method
        +PaymentRequest payment_request
        +Payer payer
        +datetime timestamp
    }
    
    class PaymentMandate {
        +PaymentMandateContents payment_mandate_contents
        +str user_authorization
    }
    
    IntentMandate --> CartMandate : "Merchant processa"
    CartMandate --> PaymentMandate : "Usuário autoriza"
```

#### Tipos de Pagamento (W3C)

```mermaid
classDiagram
    class PaymentRequest {
        +str id
        +PaymentCurrencyAmount total
        +List~PaymentItem~ displayItems
    }
    
    class PaymentCurrencyAmount {
        +str currency
        +str value
    }
    
    class PaymentItem {
        +str label
        +PaymentCurrencyAmount amount
    }
    
    PaymentRequest --> PaymentCurrencyAmount
    PaymentRequest --> PaymentItem
    PaymentItem --> PaymentCurrencyAmount
```

---

### 3. AP2 Adapters (`ap2_adapters.py`)

Funções de conversão e helpers para trabalhar com os tipos AP2.

#### Funções Principais

| Função | Descrição | Retorno |
|--------|-----------|---------|
| `create_intent_mandate(description, merchants, ...)` | Cria IntentMandate | IntentMandate |
| `create_cart_contents(cart_id, items, merchant, ...)` | Cria conteúdo do carrinho | CartContents |
| `sign_cart_mandate(cart_contents, key_manager)` | Assina carrinho com JWT | CartMandate |
| `create_payment_mandate(cart_mandate, payer, ...)` | Cria autorização de pagamento | PaymentMandate |
| `validate_cart_mandate(cart_mandate, public_key)` | Valida assinatura do carrinho | bool |
| `cart_items_to_cart_mandate(items, cart_id, ...)` | Converte itens para mandato | CartMandate |

#### Fluxo de Assinatura do Carrinho

```mermaid
sequenceDiagram
    participant M as Merchant
    participant A as ap2_adapters
    participant K as KeyManager

    M->>A: create_cart_contents(cart_id, items)
    A-->>M: CartContents
    
    M->>A: sign_cart_mandate(cart_contents, key_manager)
    A->>A: compute_cart_hash(cart_contents)
    A->>A: Criar JWT payload {iss, sub, aud, cart_hash, cart_id}
    A->>K: sign(header.payload)
    K-->>A: signature
    A->>A: CartMandate(contents, merchant_authorization=JWT)
    A-->>M: CartMandate (assinado)
```

---

### 4. AP2 Security (`ap2_security.py`)

Orquestrador de mandatos AP2 - coordena a criação e validação dos 3 tipos de mandatos.

#### Diagrama de Classes

```mermaid
classDiagram
    class AP2Security {
        +KeyManager key_manager
        +create_intent_mandate(description, merchants, ...) IntentMandate
        +create_cart_mandate(cart_items, cart_id, ...) CartMandate
        +create_payment_mandate(cart_mandate, payer, ...) PaymentMandate
        +validate_cart_mandate(cart_mandate) MandateValidationResult
        +get_full_mandate_flow(cart_items, cart_id, ...) Dict
        +create_mandate(amount, currency, ...) str
        +validate_mandate(jwt, ...) MandateValidationResult
        +is_sdk_available() bool
    }
    
    class MandatePayload {
        +int max_amount
        +str currency
        +to_dict() Dict
    }
    
    class MandateValidationResult {
        +bool valid
        +str error
        +Dict payload
        +MandatePayload mandate
        +IntentMandate intent_mandate
        +CartMandate cart_mandate
        +PaymentMandate payment_mandate
    }
    
    AP2Security --> KeyManager
    AP2Security --> MandatePayload
    AP2Security --> MandateValidationResult
```

#### Fluxo Completo de Mandatos AP2

```mermaid
flowchart TD
    subgraph Step1["1. IntentMandate"]
        User1["👤 Usuário"]
        Intent["IntentMandate<br/>description: 'Comprar livros'<br/>allowed_merchants: ['livraria-ucp']"]
        User1 -->|"expressa intenção"| Intent
    end
    
    subgraph Step2["2. CartMandate"]
        Merchant["🏪 Merchant"]
        Cart["CartContents<br/>items: [livro1, livro2]<br/>total: R$ 89.80"]
        CartSigned["CartMandate<br/>+ merchant_authorization (JWT)"]
        Merchant -->|"monta carrinho"| Cart
        Cart -->|"assina com Ed25519"| CartSigned
    end
    
    subgraph Step3["3. PaymentMandate"]
        User2["👤 Usuário"]
        Payment["PaymentMandate<br/>selected_payment_method<br/>payer: {name, email}<br/>+ user_authorization (JWT)"]
        User2 -->|"autoriza pagamento"| Payment
    end
    
    subgraph Step4["4. Settlement"]
        Processor["💳 Processador"]
        Result["✅ Pagamento Processado<br/>Recibo gerado"]
        Processor -->|"valida e executa"| Result
    end
    
    Intent --> Merchant
    CartSigned --> User2
    Payment --> Processor
    
    style Step1 fill:#e3f2fd
    style Step2 fill:#fff3e0
    style Step3 fill:#e8f5e9
    style Step4 fill:#f3e5f5
```

#### Método `get_full_mandate_flow()`

Este método gera os 3 mandatos em sequência:

```python
def get_full_mandate_flow(
    self,
    cart_items: List[Dict],
    cart_id: str,
    description: str = "",
    merchant_name: str = "Livraria Virtual UCP",
    payer_name: str = "Usuario",
    payer_email: str = "usuario@example.com",
    payment_method: str = "dev.ucp.mock_payment"
) -> Dict[str, Any]:
    """
    Retorna:
    {
        "intent_mandate": IntentMandate,
        "cart_mandate": CartMandate,
        "payment_mandate": PaymentMandate,
        "sdk_available": bool
    }
    """
```

---

### 5. Request Signatures (`signatures.py`)

Assinaturas de requisições UCP para conformidade e segurança.

#### Diagrama de Classes

```mermaid
classDiagram
    class RequestSigner {
        +KeyManager key_manager
        +sign_request(payload, method, path) Dict
        +verify_request(headers, payload, method, path) Tuple
    }
    
    class ConformanceHeaders {
        <<static>>
        +generate(include_signature) Dict
    }
    
    RequestSigner --> KeyManager
```

#### Headers Gerados

```json
{
    "request-id": "uuid",
    "idempotency-key": "uuid",
    "ucp-timestamp": "1704067200",
    "ucp-nonce": "hex16",
    "request-signature": "base64url_signature",
    "ucp-key-id": "key-abc123"
}
```

---

## Fluxos de Uso

### Fluxo de Pagamento com 3 Mandatos (AP2 Oficial)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant A as User Agent
    participant S as Store Agent
    participant AP2 as AP2Security
    participant P as Payment Processor

    Note over U,P: 1. IntentMandate - Usuário expressa intenção
    U->>A: "Quero comprar livros de Python"
    A->>AP2: create_intent_mandate(description, merchants)
    AP2-->>A: IntentMandate
    A->>S: Enviar IntentMandate

    Note over U,P: 2. CartMandate - Merchant monta e assina carrinho
    S->>S: Buscar produtos, calcular preços
    S->>AP2: create_cart_mandate(cart_items, cart_id)
    AP2->>AP2: Criar CartContents
    AP2->>AP2: Assinar com JWT (Ed25519)
    AP2-->>S: CartMandate (assinado)
    S-->>A: CartMandate para aprovação

    Note over U,P: 3. PaymentMandate - Usuário autoriza pagamento
    A->>U: "Carrinho: R$ 89.80. Confirmar?"
    U->>A: "Sim, confirmar"
    A->>AP2: create_payment_mandate(cart_mandate, payer)
    AP2->>AP2: Criar PaymentMandateContents
    AP2->>AP2: Assinar autorização (Ed25519)
    AP2-->>A: PaymentMandate

    Note over U,P: 4. Settlement - Processamento
    A->>P: PaymentMandate
    P->>AP2: validate_cart_mandate(cart_mandate)
    AP2-->>P: {valid: true}
    P->>P: Processar pagamento
    P-->>A: Recibo
    A-->>U: "Compra finalizada! ✅"
```

### Fluxo Simplificado (Mandato Legacy)

Para compatibilidade, o método `create_mandate()` ainda está disponível:

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant Store as Store (AP2Security)
    participant Payment as Payment Handler

    Agent->>Store: Solicitar mandate para R$ 100
    Store->>Store: create_mandate(10000, "BRL", "agent-001")
    Store-->>Agent: JWT mandate (legacy)

    Agent->>Payment: Pagar com mandate JWT
    Payment->>Store: validate_mandate(jwt, "agent-001", 8000)
    Store-->>Payment: {valid: true, mandate: {...}}
    Payment-->>Agent: Pagamento autorizado
```

---

## Instâncias Globais

O módulo exporta três instâncias globais (singletons):

```mermaid
flowchart LR
    subgraph Globals["Instâncias Globais"]
        ServerKM["_server_key_manager<br/>KeyManager"]
        AP2Sec["_ap2_security<br/>AP2Security"]
        ReqSigner["_request_signer<br/>RequestSigner"]
    end
    
    subgraph Getters["Funções de Acesso"]
        GetKM["get_server_key_manager()"]
        GetAP2["get_ap2_security()"]
        GetSigner["get_request_signer()"]
    end
    
    GetKM --> ServerKM
    GetAP2 --> AP2Sec
    GetSigner --> ReqSigner
    
    AP2Sec --> ServerKM
    ReqSigner --> ServerKM
```

---

## Exports do Módulo

```python
from backend.src.security import (
    # Key Manager
    KeyManager,
    get_server_key_manager,
    
    # AP2 Security
    AP2Security,
    get_ap2_security,
    MandatePayload,
    MandateValidationResult,
    
    # Tipos AP2 Oficiais (SDK Google)
    IntentMandate,
    CartMandate,
    CartContents,
    PaymentMandate,
    PaymentMandateContents,
    PaymentRequest,
    PaymentItem,
    PaymentCurrencyAmount,
    PaymentResponse,
    is_ap2_sdk_available,
    AP2_SDK_AVAILABLE,
    
    # Adapters AP2
    create_intent_mandate,
    create_cart_contents,
    sign_cart_mandate,
    create_payment_mandate,
    validate_cart_mandate,
    cart_items_to_cart_mandate,
    
    # Request Signatures
    RequestSigner,
    ConformanceHeaders,
    get_request_signer,
)
```

---

## Exemplos de Uso

### Fluxo Completo com 3 Mandatos (Recomendado)

```python
from backend.src.security import get_ap2_security, is_ap2_sdk_available

# Verificar se SDK está disponível
print(f"SDK AP2 disponível: {is_ap2_sdk_available()}")

ap2 = get_ap2_security()

# Itens do carrinho
cart_items = [
    {"title": "Clean Code em Python", "price": 4990, "quantity": 1},
    {"title": "Python para Todos", "price": 3990, "quantity": 1}
]

# Gerar fluxo completo de mandatos
mandates = ap2.get_full_mandate_flow(
    cart_items=cart_items,
    cart_id="cart_123",
    description="Comprar livros de programação",
    payer_name="João Silva",
    payer_email="joao@example.com"
)

# Acessar mandatos individuais
intent = mandates["intent_mandate"]
cart = mandates["cart_mandate"]
payment = mandates["payment_mandate"]

print(f"IntentMandate: {intent.description}")
print(f"CartMandate ID: {cart.contents.id}")
print(f"CartMandate assinado: {cart.merchant_authorization is not None}")
print(f"PaymentMandate ID: {payment.payment_mandate_contents.payment_mandate_id}")
```

### Criar Mandatos Individualmente

```python
from backend.src.security import get_ap2_security

ap2 = get_ap2_security()

# 1. IntentMandate
intent = ap2.create_intent_mandate(
    description="Comprar livros de Python",
    merchants=["livraria-ucp"],
    skus=["book-001", "book-002"]
)

# 2. CartMandate (após merchant montar carrinho)
cart_items = [{"title": "Livro", "price": 4990, "quantity": 1}]
cart_mandate = ap2.create_cart_mandate(
    cart_items=cart_items,
    cart_id="cart_456"
)

# 3. PaymentMandate (após usuário confirmar)
payment_mandate = ap2.create_payment_mandate(
    cart_mandate=cart_mandate,
    payer_name="Maria",
    payer_email="maria@example.com"
)
```

### Validar CartMandate

```python
from backend.src.security import get_ap2_security

ap2 = get_ap2_security()

# Validar assinatura do carrinho
result = ap2.validate_cart_mandate(cart_mandate)

if result.valid:
    print("CartMandate válido!")
    print(f"  - Formato JWT: ✓")
    print(f"  - Assinatura Ed25519: ✓")
    print(f"  - Hash do carrinho: ✓")
else:
    print(f"Erro: {result.error}")
```

### Mandato Legacy (Compatibilidade)

```python
from backend.src.security import get_ap2_security

ap2 = get_ap2_security()

# Criar mandate (formato antigo)
mandate_jwt = ap2.create_mandate(
    amount=10000,  # R$ 100,00 em centavos
    currency="BRL",
    beneficiary="agent-001",
    expiry_seconds=3600
)

# Validar mandate
result = ap2.validate_mandate(
    jwt=mandate_jwt,
    expected_audience="agent-001",
    required_amount=8000
)

if result.valid:
    print(f"Mandate válido! Limite: R$ {result.mandate.max_amount / 100:.2f}")
```

### Executar Demo

```bash
# Executar demonstração completa do AP2
make demo-ap2
```

---

## Dependências

```mermaid
flowchart TB
    subgraph External["Dependências Externas"]
        Crypto["cryptography<br/>Ed25519, serialization"]
        Base64["base64<br/>urlsafe_b64encode/decode"]
        JSON["json<br/>Serialização"]
        Time["time<br/>Timestamp"]
        UUID["uuid<br/>IDs únicos"]
    end
    
    subgraph SDK["SDK Oficial Google"]
        AP2SDK["google-agentic-commerce/AP2<br/>sdk/ap2-repo/<br/>ap2.types.mandate<br/>ap2.types.payment_request"]
    end
    
    subgraph Internal["Dependências Internas"]
        Config["../config<br/>settings.ap2_key_id"]
    end
    
    subgraph Security["Módulo Security"]
        KeyMgr["key_manager.py"]
        AP2["ap2_security.py"]
        Types["ap2_types.py"]
        Adapters["ap2_adapters.py"]
        Signatures["signatures.py"]
    end
    
    Types --> AP2SDK
    
    KeyMgr --> Crypto
    KeyMgr --> Base64
    
    AP2 --> KeyMgr
    AP2 --> Types
    AP2 --> Adapters
    AP2 --> JSON
    AP2 --> Time
    AP2 --> Base64
    
    Adapters --> KeyMgr
    Adapters --> Types
    
    Signatures --> KeyMgr
    Signatures --> JSON
    Signatures --> Time
    Signatures --> UUID
    
    KeyMgr --> Config
```

---

## Segurança

### Algoritmos Utilizados

| Componente | Algoritmo | Propósito |
|------------|-----------|-----------|
| Assinaturas | Ed25519 (EdDSA) | Assinatura digital |
| Codificação | Base64URL | Codificação de dados binários |
| Tokens | JWT | Estrutura de mandatos |
| Hash | SHA-256 | Integridade do carrinho |

### Validações de Segurança

#### IntentMandate
- ✅ Expiração configurável
- ✅ Lista de merchants permitidos
- ✅ Lista de SKUs permitidos (opcional)
- ✅ Flag de confirmação do usuário

#### CartMandate
- ✅ Assinatura JWT com Ed25519
- ✅ Hash SHA-256 do conteúdo do carrinho
- ✅ Validação de expiração
- ✅ Detecção de adulteração (preços, quantidades)

#### PaymentMandate
- ✅ Autorização JWT do usuário
- ✅ Referência ao CartMandate original
- ✅ Dados do pagador incluídos
- ✅ Timestamp de autorização

#### Request Signature
- ✅ Verificação de assinatura Ed25519
- ✅ Validação de timestamp (prevenção de replay)
- ✅ Verificação de nonce
- ✅ Validação de idade máxima

---

## Benefícios do SDK Oficial

| Benefício | Descrição |
|-----------|-----------|
| **Padronizado** | Segue especificação oficial do Google |
| **Interoperável** | Compatível com outros implementadores AP2 |
| **Seguro** | Criptografia Ed25519 em todos os mandatos |
| **Auditável** | Cadeia de mandatos cria trilha não-repudiável |
| **Extensível** | Suporta diferentes rails de pagamento |

---

## Referências

- **SDK Oficial AP2:** https://github.com/google-agentic-commerce/AP2
- **AP2 Protocol:** Agent Payments Protocol v2
- **Ed25519:** https://ed25519.cr.yp.to/
- **JWT:** https://jwt.io/
- **JWK:** https://datatracker.ietf.org/doc/html/rfc7517
- **W3C Payment Request:** https://www.w3.org/TR/payment-request/
