-- Cassandra marketplace schema and sample queries

-- Users and sellers
CREATE TABLE IF NOT EXISTS users (
  user_id uuid,
  name text,
  email text,
  created_at timestamp,
  PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS sellers (
  seller_id uuid,
  name text,
  rating decimal,
  total_sales bigint,
  created_at timestamp,
  PRIMARY KEY (seller_id)
);

-- Catalog
CREATE TABLE IF NOT EXISTS products (
  category text,
  product_id uuid,
  name text,
  price decimal,
  seller_id uuid,
  description text,
  created_at timestamp,
  PRIMARY KEY ((category), product_id)
) WITH CLUSTERING ORDER BY (product_id ASC);

-- Orders by user
CREATE TABLE IF NOT EXISTS orders_by_user (
  user_id uuid,
  order_date timestamp,
  order_id uuid,
  status text,
  total_amount decimal,
  payment_method text,
  shipping_address text,
  items list<frozen<map<text, text>>>,
  created_at timestamp,
  PRIMARY KEY ((user_id), order_date, order_id)
) WITH CLUSTERING ORDER BY (order_date DESC, order_id ASC);

-- Reviews by product
CREATE TABLE IF NOT EXISTS reviews_by_product (
  product_id uuid,
  created_at timestamp,
  user_id uuid,
  rating smallint,
  comment text,
  PRIMARY KEY ((product_id), created_at, user_id)
) WITH CLUSTERING ORDER BY (created_at DESC, user_id ASC);

-- Query helpers
-- 1) Recent orders of a user
SELECT order_id, order_date, status, total_amount
FROM orders_by_user
WHERE user_id = ? 
ORDER BY order_date DESC
LIMIT 20;

-- 2) Details of a specific order for a user
SELECT *
FROM orders_by_user
WHERE user_id = ? AND order_id = ?;

-- 3) List products by category
SELECT product_id, name, price
FROM products
WHERE category = ?
LIMIT 50;

-- 4) Recent reviews for a product
SELECT user_id, rating, comment, created_at
FROM reviews_by_product
WHERE product_id = ?
ORDER BY created_at DESC
LIMIT 50;
