# Estudo de Caso 2 — Modelagem de Dados em Cassandra (Marketplace)

## 1. Por que Cassandra exige design *query-driven*
- Cassandra distribui dados pelo cluster via **partition key**; toda consulta precisa apontar para uma partição ou range conhecido. Sem conhecer a query, a chave de partição pode causar *full scans* e *hotspots*.
- Não há *server-side joins* nem *ad-hoc aggregations* eficientes; por isso, o dado é **desnormalizado** e duplicado para cada padrão de acesso necessário.
- As decisões de **partition key + clustering key + ordem de clustering** determinam latência, paralelismo de leitura e balanceamento. Logo, o schema é derivado das consultas críticas.

## 2. Tabela `orders_by_user` completa
Critério: recuperar rapidamente o histórico de pedidos de um usuário, mais recentes primeiro. Itens do pedido ficam embutidos para evitar *fan-out* em outra tabela.

```cql
CREATE TABLE IF NOT EXISTS orders_by_user (
  user_id          UUID,              -- partition key
  order_date       TIMESTAMP,         -- clustering (desc) para ordenação recente
  order_id         UUID,              -- clustering secundário (desempate)
  status           TEXT,
  total_amount     DECIMAL,
  payment_method   TEXT,
  shipping_address TEXT,
  items            LIST<FROZEN<
                      MAP<TEXT, TEXT>
                    >>,               -- cada item: {product_id, name, unit_price, qty}
  created_at       TIMESTAMP,
  PRIMARY KEY ((user_id), order_date, order_id)
) WITH CLUSTERING ORDER BY (order_date DESC, order_id ASC);
```
Observações:
- `user_id` é a **partition key** → cada usuário concentra seus pedidos em uma partição, permitindo paginação por data.
- `order_date DESC` traz os pedidos mais recentes primeiro (padrão de histórico).
- `order_id` evita colisão de timestamps e permite paginação estável.
- `items` embute o snapshot de produtos no momento do pedido, evitando consultas adicionais.

## 3. Três consultas comuns e impacto na modelagem
1) **Histórico de pedidos de um usuário (mais recentes):**
```sql
SELECT order_id, order_date, status, total_amount
FROM orders_by_user
WHERE user_id = ?
ORDER BY order_date DESC
LIMIT 20;
```
- Motiva `user_id` como partition key e `order_date DESC` como clustering.

2) **Detalhar um pedido específico de um usuário:**
```sql
SELECT *
FROM orders_by_user
WHERE user_id = ? AND order_id = ?;
```
- Exige `order_id` na clustering key para acesso direto ao registro do pedido dentro da partição.

3) **Listar produtos por categoria (catálogo/busca):**
```sql
SELECT product_id, name, price
FROM products
WHERE category = ?
LIMIT 50;
```
- Motiva tabela `products` com `category` como partition key e `product_id` como clustering para varrer por categoria com baixo custo.

(Alternativa adicional frequente) **Avaliações recentes de um produto:** `reviews_by_product` com partition `product_id` e clustering `created_at DESC` para feeds rápidos.

## 4. Por que Cassandra não usa JOIN e impacto na modelagem
- O protocolo de leitura de Cassandra é otimizado para buscar linhas contíguas em uma partição; *joins* requereriam múltiplas partições e coordenação, degradando latência e throughput.
- Sem *joins*, a estratégia é **desnormalizar e duplicar** dados conforme a necessidade das consultas; cada tabela atende a um *query pattern* específico.
- O desenho das chaves (partition/clustering) e a escolha de colunas embutidas (como `items` no pedido) substituem relações tradicionais, garantindo consultas O(1) ou O(log n) dentro da partição.

## 5. Visão resumida das tabelas sugeridas
- `users` — PK: `user_id`. Dados cadastrais.
- `sellers` — PK: `seller_id`. Reputação e métricas.
- `products` — PK: `category`, CK: `product_id`. Busca por categoria.
- `orders_by_user` — PK: `user_id`, CK: `order_date DESC, order_id`. Histórico recente de pedidos (itens embutidos).
- `reviews_by_product` — PK: `product_id`, CK: `created_at DESC, user_id`. Avaliações recentes por produto.
