from conection import get_engine, validate_connection, execute_sql


ddl = """

ALTER TABLE DIM_produto_canonico
  ADD COLUMN sk_categoria INT NULL,
  ADD CONSTRAINT fk_produto_categoria
    FOREIGN KEY (sk_categoria) REFERENCES DIM_categoria(sk_categoria);

CREATE INDEX idx_produto_categoria
  ON DIM_produto_canonico (sk_categoria);


"""

def create_tables():
    engine = get_engine()

    if validate_connection(engine):
        execute_sql(engine, ddl)
    else:
        print("⚠️ Não foi possível criar tabelas porque a conexão falhou.")

if __name__ == "__main__":
    create_tables()
