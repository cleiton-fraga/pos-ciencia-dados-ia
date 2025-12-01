# /usr/bin/python3 -m pip install "elasticsearch<9.0.0,>=8.0.0" --upgrade

# Criação de índice com mapeamento (estrutura do schema).
# Indexação em massa de documentos.
# Busca simples (match).
# Busca multi-campos (multi_match).
# Filtro exato (term).
# Consultas booleanas (must, must_not).
# Agregações (analytics).
# Atualização parcial de documentos.
# Exclusão de documentos.
# Scroll API (consulta paginada para grandes volumes).

from elasticsearch import Elasticsearch
from datetime import datetime

# ================================
# Conexão com Elasticsearch
# ================================
es = Elasticsearch("http://localhost:9200")

if es.ping():
    print("✅ Conexão com o Elasticsearch bem-sucedida!")
else:
    print("❌ Não foi possível conectar ao Elasticsearch. Verifique o Docker.")
    exit()

# ================================
# 1. Criação de índice com mapeamento
# ================================
index_name = "imagens"

# Exclui índice anterior (se existir)
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)

# Cria índice com mapeamento
es.indices.create(
    index=index_name,
    body={
        "mappings": {
            "properties": {
                "url": {"type": "keyword"},
                "descricao": {"type": "text"},
                "tags": {"type": "keyword"},
                "timestamp": {"type": "date"}
            }
        }
    }
)
print(f"📂 Índice '{index_name}' criado com mapeamento!")

# ================================
# 2. Indexação de documentos
# ================================
docs = [
    {"url": "src/modulo2/data/ferrari.avif", "descricao": "foto de uma ferrari vermelha", "tags": ["carro", "luxo"], "timestamp": datetime.now()},
    {"url": "src/modulo2/data/praia.jpg", "descricao": "paisagem de praia no verão", "tags": ["praia", "verão"], "timestamp": datetime.now()},
    {"url": "src/modulo2/data/montanha.jpg", "descricao": "paisagem de montanha com neve", "tags": ["montanha", "neve"], "timestamp": datetime.now()},
    {"url": "src/modulo2/data/cidade.jpg", "descricao": "foto de cidade iluminada à noite", "tags": ["cidade", "noite"], "timestamp": datetime.now()},
]

for i, doc in enumerate(docs, 1):
    es.index(index=index_name, id=i, document=doc)

print("📥 Documentos indexados com sucesso!")

# Força um refresh após indexar
es.indices.refresh(index=index_name)

# ================================
# 3. Busca simples (full-text search)
# ================================
result = es.search(index=index_name, query={"match": {"descricao": "paisagem"}})
print("\n🔍 Busca por 'paisagem':")
for hit in result['hits']['hits']:
    print(hit["_source"])

# ================================
# 4. Busca com múltiplos campos (multi_match)
# ================================
result = es.search(
    index=index_name,
    query={
        "multi_match": {
            "query": "ferrari",
            "fields": ["descricao", "tags"]
        }
    }
)
print("\n🔍 Busca em vários campos (descricao + tags):")
for hit in result['hits']['hits']:
    print(hit["_source"])

# ================================
# 5. Filtro por tags (termo exato)
# ================================
result = es.search(
    index=index_name,
    query={
        "term": {"tags": "praia"}
    }
)
print("\n🔍 Busca por tag 'praia':")
for hit in result['hits']['hits']:
    print(hit["_source"])

# ================================
# 6. Busca booleana (AND / OR / NOT)
# ================================
result = es.search(
    index=index_name,
    query={
        "bool": {
            "must": [{"match": {"descricao": "paisagem"}}],
            "must_not": [{"match": {"descricao": "neve"}}]
        }
    }
)
print("\n🔍 Busca booleana (paisagem, mas não neve):")
for hit in result['hits']['hits']:
    print(hit["_source"])

# ================================
# 7. Agregações (analytics)
# ================================
result = es.search(
    index=index_name,
    size=0,  # não retorna documentos, só agregações
    aggs={
        "tags_count": {"terms": {"field": "tags"}}
    }
)
print("\n📊 Agregação por tags:")
for bucket in result["aggregations"]["tags_count"]["buckets"]:
    print(f"{bucket['key']}: {bucket['doc_count']} documentos")

# ================================
# 8. Atualização parcial de documento
# ================================
es.update(
    index=index_name,
    id=1,
    doc={"doc": {"descricao": "foto de uma Ferrari vermelha de corrida"}}
)
print("\n✏️ Documento ID=1 atualizado!")

# ================================
# 9. Exclusão de documento
# ================================
es.delete(index=index_name, id=4)
print("🗑️ Documento ID=4 removido!")

# ================================
# 10. Scroll (para buscar grandes volumes)
# ================================

# Mensagem inicial para indicar a execução da busca paginada
print("\n📜 Scroll API (buscando tudo em blocos):")

# Primeira busca no índice "imagens"
# - query={"match_all": {}} → busca todos os documentos
# - scroll="1m" → mantém o contexto da busca vivo por 1 minuto no cluster
# - size=2 → retorna 2 documentos por "página"
scroll = es.search(index=index_name, query={"match_all": {}}, scroll="1m", size=2)

# O scroll retorna um "_scroll_id", que é usado para pedir a próxima "página" de resultados
sid = scroll["_scroll_id"]

# Lista com os primeiros documentos retornados
hits = scroll["hits"]["hits"]

# Enquanto ainda houver resultados...
while hits:
    # Itera sobre cada documento retornado e imprime seu conteúdo
    for doc in hits:
        print(doc["_source"])
    
    # Faz nova chamada à API de scroll usando o mesmo scroll_id
    # Isso pega a "próxima página" de documentos
    scroll = es.scroll(scroll_id=sid, scroll="1m")
    
    # Atualiza o scroll_id para a próxima iteração
    sid = scroll["_scroll_id"]
    
    # Atualiza a lista de documentos; se vier vazia, o loop termina
    hits = scroll["hits"]["hits"]
