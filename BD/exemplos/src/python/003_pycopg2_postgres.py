import psycopg2

# Conexão com o banco
conn = psycopg2.connect(
    dbname="mydatabase",
    user="myuser",
    password="mypassword",
    host="localhost",  
    port="5432"
)
cursor = conn.cursor()

# 1. Criar tabela se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS alunos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    idade INT NOT NULL,
    curso VARCHAR(100) NOT NULL
)
""")
conn.commit()

# 2. Inserir dados
cursor.execute("INSERT INTO alunos (nome, idade, curso) VALUES (%s, %s, %s)", ("Ana", 23, "Engenharia"))
cursor.execute("INSERT INTO alunos (nome, idade, curso) VALUES (%s, %s, %s)", ("Bruno", 21, "Direito"))
cursor.execute("INSERT INTO alunos (nome, idade, curso) VALUES (%s, %s, %s)", ("Carla", 23, "Engenharia"))
conn.commit()

# 3. Consulta simples
print("\n=== Todos os alunos ===")
cursor.execute("SELECT id, nome, idade, curso FROM alunos")
for row in cursor.fetchall():
    print(row)

# 4. Consulta com GROUP BY (quantidade de alunos por curso)
print("\n=== Quantidade de alunos por curso ===")
cursor.execute("""
SELECT curso, COUNT(*) as total
FROM alunos
GROUP BY curso
ORDER BY total DESC
""")
for row in cursor.fetchall():
    print(row)

# 5. Consulta com GROUP BY (idade média por curso)
print("\n=== Idade média dos alunos por curso ===")
cursor.execute("""
SELECT curso, AVG(idade) as idade_media
FROM alunos
GROUP BY curso
ORDER BY idade_media DESC
""")
for row in cursor.fetchall():
    print(row)

# Fechar conexão
cursor.close()
conn.close()
