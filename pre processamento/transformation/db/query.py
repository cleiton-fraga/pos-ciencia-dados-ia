from sqlalchemy import text
import pandas as pd
from conection import get_engine  # ajuste se necessário

def main():
    engine = get_engine()

    query = """
    select * from BRIDGE_produto_listing where sk_listing = 1461;
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
