from sqlalchemy import text
import pandas as pd
from conection import get_engine  # ajuste se necessário

def main():
    engine = get_engine()

    query = """
SELECT
  p.sk_produto,
  p.marca_canonico,
  p.nome_canonico,
  p.categoria_canonica,
  p.sk_categoria,
  a.nome
FROM DIM_produto_canonico p
join DIM_categoria a on a.sk_categoria = p.sk_categoria
WHERE p.sk_categoria = 3
ORDER BY p.nome_canonico;

    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
