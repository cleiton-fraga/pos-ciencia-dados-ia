// Script de provisionamento para MongoDB (shell mongo ou mongosh)
// Cria DB, coleções com validação básica e índices alinhados ao caso de uso.

const dbName = "marketplace";
const db = connect(`${dbName}`);

// USERS
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["type", "name", "email", "createdAt"],
      properties: {
        type: { enum: ["customer", "seller"] },
        name: { bsonType: "string" },
        email: { bsonType: "string" },
        phone: { bsonType: "string" },
        document: { bsonType: "string" },
        addresses: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              label: { bsonType: "string" },
              street: { bsonType: "string" },
              city: { bsonType: "string" },
              state: { bsonType: "string" },
              zipCode: { bsonType: "string" },
              country: { bsonType: "string" }
            }
          }
        },
        stats: {
          bsonType: "object",
          properties: {
            totalOrders: { bsonType: "int" },
            totalSpent: { bsonType: "double" }
          }
        },
        createdAt: { bsonType: "date" },
        updatedAt: { bsonType: "date" }
      }
    }
  }
});

db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ type: 1 });

// PRODUCTS
db.createCollection("products", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "category", "sellerId", "price", "stock", "createdAt"],
      properties: {
        name: { bsonType: "string" },
        description: { bsonType: "string" },
        category: { bsonType: "string" },
        sellerId: { bsonType: "objectId" },
        price: {
          bsonType: "object",
          required: ["amount", "currency"],
          properties: {
            amount: { bsonType: ["double", "decimal"] },
            currency: { bsonType: "string" }
          }
        },
        stock: {
          bsonType: "object",
          properties: {
            quantity: { bsonType: "int" },
            warehouseLocation: { bsonType: "string" }
          }
        },
        attributes: { bsonType: "object" }, // flexível
        tags: { bsonType: "array", items: { bsonType: "string" } },
        rating: {
          bsonType: "object",
          properties: {
            average: { bsonType: ["double", "decimal"] },
            totalReviews: { bsonType: "int" }
          }
        },
        createdAt: { bsonType: "date" },
        updatedAt: { bsonType: "date" }
      }
    }
  }
});

db.products.createIndex({ category: 1, "price.amount": 1 });
db.products.createIndex({ sellerId: 1, "price.amount": 1 });
// Índices opcionais para atributos usados em busca
db.products.createIndex({ "attributes.color": 1 });
db.products.createIndex({ "attributes.voltage": 1 });

// ORDERS
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["customerId", "status", "items", "createdAt"],
      properties: {
        customerId: { bsonType: "objectId" },
        status: { enum: ["CREATED", "PAID", "SHIPPED", "CANCELED"] },
        items: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["productId", "productName", "unitPrice", "quantity", "subtotal"],
            properties: {
              productId: { bsonType: "objectId" },
              productName: { bsonType: "string" },
              unitPrice: { bsonType: ["double", "decimal"] },
              quantity: { bsonType: "int" },
              subtotal: { bsonType: ["double", "decimal"] }
            }
          }
        },
        payment: {
          bsonType: "object",
          properties: {
            method: { bsonType: "string" },
            transactionId: { bsonType: "string" },
            paidAt: { bsonType: "date" }
          }
        },
        shipping: {
          bsonType: "object",
          properties: {
            address: { bsonType: "object" },
            carrier: { bsonType: "string" },
            trackingCode: { bsonType: "string" },
            status: { bsonType: "string" }
          }
        },
        createdAt: { bsonType: "date" },
        updatedAt: { bsonType: "date" }
      }
    }
  }
});

db.orders.createIndex({ customerId: 1, createdAt: -1 });
db.orders.createIndex({ "items.productId": 1, createdAt: -1 });

// REVIEWS (opcional, para alto volume)
db.createCollection("reviews", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["productId", "userId", "rating", "createdAt"],
      properties: {
        productId: { bsonType: "objectId" },
        userId: { bsonType: "objectId" },
        rating: { bsonType: "int" },
        comment: { bsonType: "string" },
        createdAt: { bsonType: "date" }
      }
    }
  }
});

db.reviews.createIndex({ productId: 1, createdAt: -1 });
db.reviews.createIndex({ userId: 1, createdAt: -1 });

print("MongoDB provisioning complete for DB:", dbName);
