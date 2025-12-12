## Estudo de Caso 1 — Modelagem de Dados com MongoDB (Marketplace)


### 1. Schemas JSON das coleções

#### 1.1. Coleção `users`

```json
{
  "_id": ObjectId("653f1a..."),
  "type": "customer",             // ou "seller"
  "name": "João Silva",
  "email": "joao.silva@example.com",
  "phone": "+55 79 99999-0000",
  "document": "123.456.789-00",    // CPF/CNPJ se fizer sentido
  "addresses": [
    {
      "label": "home",
      "street": "Rua A, 123",
      "city": "Aracaju",
      "state": "SE",
      "zipCode": "49000-000",
      "country": "BR"
    }
  ],
  "createdAt": ISODate("2025-12-09T13:00:00Z"),
  "updatedAt": ISODate("2025-12-09T13:00:00Z"),
  "stats": {
    "totalOrders": 12,
    "totalSpent": 2300.50
  }
}
```

---

#### 1.2. Coleção `products`

```json
{
  "_id": ObjectId("6540ab..."),
  "name": "Notebook Gamer X",
  "description": "Notebook gamer com RTX 4060...",
  "category": "electronics",
  "sellerId": ObjectId("653f1a..."),      // ref -> users._id (type = "seller")
  "price": {
    "amount": 5999.90,
    "currency": "BRL"
  },
  "stock": {
    "quantity": 42,
    "warehouseLocation": "CD-SP-01"
  },
  "attributes": {                         // atributos variáveis
    "brand": "Dell",
    "ram": "16GB",
    "storage": "512GB SSD",
    "cpu": "Intel i7",
    "gpu": "RTX 4060",
    "color": "Preto",
    "voltage": "Bivolt"
  },
  "tags": ["notebook", "gamer", "rtx", "promo"],
  "rating": {
    "average": 4.6,
    "totalReviews": 128
  },
  "createdAt": ISODate("2025-12-01T10:00:00Z"),
  "updatedAt": ISODate("2025-12-09T10:00:00Z")
}
```

> Observação: as avaliações em si podem ser **embutidas** (quando poucas) ou ficar em outra coleção `reviews`. Vou comentar isso na parte de embedding vs referencing.

---

#### 1.3. Coleção `orders`

```json
{
  "_id": ObjectId("6541ff..."),
  "customerId": ObjectId("653f1a..."),      // ref -> users._id (type = "customer")
  "status": "PAID",                         // CREATED, PAID, SHIPPED, CANCELED etc.
  "items": [
    {
      "productId": ObjectId("6540ab..."),   // ref -> products._id
      "productName": "Notebook Gamer X",    // snapshot
      "unitPrice": 5999.90,                 // snapshot do preço na data
      "quantity": 1,
      "subtotal": 5999.90
    },
    {
      "productId": ObjectId("6540bb..."),
      "productName": "Mouse Gamer RGB",
      "unitPrice": 150.00,
      "quantity": 2,
      "subtotal": 300.00
    }
  ],
  "payment": {
    "method": "credit_card",
    "transactionId": "PAY-123456",
    "paidAt": ISODate("2025-12-09T13:05:00Z")
  },
  "shipping": {
    "address": {
      "street": "Rua A, 123",
      "city": "Aracaju",
      "state": "SE",
      "zipCode": "49000-000",
      "country": "BR"
    },
    "carrier": "Correios",
    "trackingCode": "BR123456789",
    "status": "IN_TRANSIT"
  },
  "createdAt": ISODate("2025-12-09T13:00:00Z"),
  "updatedAt": ISODate("2025-12-09T13:10:00Z")
}
```

---

### 2. Embedding vs Referencing

#### Onde usar **embedding** (inclusão)

**Usado em:**

* `users.addresses`
* `orders.items`
* `orders.shipping`
* `orders.payment`
* `products.attributes`
* (opcional) um resumo de avaliações dentro de `products.rating`

**Por quê?**

* São dados normalmente **carregados junto** com o documento principal:

  * Quando carrego um pedido, **quase sempre** quero ver itens, pagamento e entrega.
  * Quando carrego o usuário, faz sentido já ter os endereços.
* São dados **fortemente acoplados** ao “pai”:

  * Um item de pedido só faz sentido dentro daquele pedido.
  * O endereço em `shipping` é um snapshot daquele momento (não quero que mude se o usuário mudar o cadastro depois).
* Evita **joins** na aplicação (menos round-trips): 1 query já traz tudo que é necessário para exibir o pedido ou o usuário.

---

#### Onde usar **referencing** (referência)

**Usado em:**

* `products.sellerId` → `users._id`
* `orders.customerId` → `users._id`
* `orders.items[].productId` → `products._id`
* (possível) coleção `reviews` separada, com `productId` e `userId`

**Por quê?**

* Usuários e produtos são entidades **compartilhadas**:

  * Um mesmo `seller` aparece em vários produtos.
  * Um mesmo `product` aparece em vários pedidos.
* Se eu embutisse tudo, teria muito dado **duplicado** e difícil de manter (ex.: dados do vendedor em todos os produtos).
* Referencing permite:

  * Consultar “todos os pedidos de um usuário” via `customerId`;
  * Consultar “todos os produtos de um vendedor” via `sellerId`;
  * E também “todos os pedidos de um certo produto” via `items.productId`.

---

#### E as avaliações de produtos?

Duas abordagens comuns:

#### a) Embutir avaliações em `products` (bom para poucas reviews)

```json
"reviews": [
  {
    "userId": ObjectId("653f1a..."),
    "rating": 5,
    "comment": "Muito bom!",
    "createdAt": ISODate("2025-12-01T12:00:00Z")
  }
]
```

* Bom para: produtos com **poucas reviews** e leitura frequente das avaliações junto com o produto.
* Risco: documentos de produto ficarem muito grandes (limite de 16MB) em cenários de **alto volume de reviews**.

#### b) Coleção separada `reviews` (boa prática para escala)

```json
{
  "_id": ObjectId("6542aa..."),
  "productId": ObjectId("6540ab..."),    // ref -> products._id
  "userId": ObjectId("653f1a..."),       // ref -> users._id
  "rating": 4,
  "comment": "Ótimo custo-benefício!",
  "createdAt": ISODate("2025-12-09T13:20:00Z")
}
```

* Melhor para:

  * Produtos com **muitas avaliações**;
  * Casos em que você quer paginar reviews, filtrar por nota, etc.
* A coleção `products` guarda só o **resumo** (`rating.average` e `rating.totalReviews`) para leitura rápida.

---

### 3. Modelando produtos com atributos variáveis

Requisito: produtos de categorias diferentes (eletrônicos, roupas, livros, etc.) com **atributos específicos** sem ter que ficar alterando schema toda hora.

---

#### Caso 1 – `attributes` como array de pares (name/value)

```json
"attributes": [
  { "name": "ram", "value": "16GB", "unit": null },
  { "name": "storage", "value": "512", "unit": "GB" },
  { "name": "screenSize", "value": "15.6", "unit": "inches" }
]
```

**Vantagens:**

* Útil quando você quer **metadados extras** por atributo (`unit`, `source`, etc.).
* Facilita queries genéricas:
  `attributes.name = "ram" AND attributes.value = "16GB"`.

**Desvantagens:**

* Fica mais verboso para ler/manipular no código.
* Para alguns drivers, lidar com arrays pode ser um pouco mais chato que objetos simples.

---

#### O que eu usaria nesse caso de uso?

* Para um **e-commerce padrão**, eu seguiria com o **objeto flexível** (`attributes: { ... }`) e:

  * Definiria uma **tabela de referência** na aplicação para cada categoria (ex.: quais atributos são esperados).
  * Criaria índices específicos para atributos importantes de busca (ex.: `attributes.color`, `attributes.size`, `attributes.voltage`).

---
