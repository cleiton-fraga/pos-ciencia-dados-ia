
from __future__ import annotations
import math
import os
from typing import Dict, List, Tuple
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from conection import get_engine  


CSV_PATH = r"/pre processamento/transformation/silver/silver_all.csv"
CHUNK = 800

def chunked_df(df: pd.DataFrame, n: int):
    for i in range(0, len(df), n):
        yield df.iloc[i : i + n]


def clean_nan_records(records: List[dict]) -> List[dict]:
    for r in records:
        for k, v in list(r.items()):
            if isinstance(v, float) and math.isnan(v):
                r[k] = None
    return records

def exec_many(conn, sql, df_part: pd.DataFrame):
    records = clean_nan_records(df_part.to_dict(orient="records"))
    if records:
        conn.execute(sql, records)

def load_silver_all(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["collected_at"] = pd.to_datetime(df.get("collected_at"), errors="coerce")
    df["data_coleta"] = df["collected_at"].dt.date
    df["price"] = pd.to_numeric(df.get("price"), errors="coerce")
    df["rating"] = pd.to_numeric(df.get("rating"), errors="coerce")
    if "in_stock" in df.columns:
        df["in_stock"] = df["in_stock"].astype(bool)
    else:
        df["in_stock"] = False
    df["nome_canonico"] = df.get("title_norm")
    df["nome_canonico"] = df["nome_canonico"].where(pd.notna(df["nome_canonico"]), df.get("title_raw"))
    df["categoria_canonica"] = df.get("category_norm")
    df["categoria_canonica"] = df["categoria_canonica"].where(
        pd.notna(df["categoria_canonica"]), df.get("category_raw")
    )
    df["categoria_canonica"] = df["categoria_canonica"].where(pd.notna(df["categoria_canonica"]), "sem_categoria")
    df["marca_canonico"] = df.get("brand_raw")  
    df["marketplace"] = df.get("source").astype(str)
    df["marketplace_url"] = df.get("source_url")
    df["product_url"] = df.get("url").astype(str)
    df["titulo"] = df.get("title_raw").astype(str)
    df["categoria"] = df.get("category_raw").astype(str)
    df["marca"] = df.get("brand_raw")  
    df = df.dropna(subset=["data_coleta", "marketplace", "product_url", "nome_canonico", "price"])
    return df

def upsert_dim_marketplace(conn, df: pd.DataFrame):
    sql = text("""
        INSERT INTO DIM_marketplace (nome, url)
        VALUES (:nome, :url)
        ON DUPLICATE KEY UPDATE
          url = COALESCE(VALUES(url), url)
    """)
    mp = (
        df[["marketplace", "marketplace_url"]]
        .drop_duplicates()
        .rename(columns={"marketplace": "nome", "marketplace_url": "url"})
    )
    for part in chunked_df(mp, CHUNK):
        exec_many(conn, sql, part)


def upsert_dim_tempo(conn, df: pd.DataFrame):
    datas = sorted(df["data_coleta"].drop_duplicates().tolist())
    rows = []
    for d in datas:
        ts = pd.Timestamp(d)
        mes = int(ts.month)
        rows.append({
            "data_coleta": d,
            "dia": int(ts.day),
            "mes": mes,
            "ano": int(ts.year),
            "semana": int(ts.isocalendar().week),
            "trimestre": int((mes - 1) // 3 + 1),
            "semestre": 1 if mes <= 6 else 2
        })

    sql = text("""
        INSERT INTO DIM_tempo (data_coleta, dia, mes, ano, semana, trimestre, semestre)
        VALUES (:data_coleta, :dia, :mes, :ano, :semana, :trimestre, :semestre)
        ON DUPLICATE KEY UPDATE
          dia=VALUES(dia),
          mes=VALUES(mes),
          ano=VALUES(ano),
          semana=VALUES(semana),
          trimestre=VALUES(trimestre),
          semestre=VALUES(semestre)
    """)
    tempo_df = pd.DataFrame(rows)
    for part in chunked_df(tempo_df, CHUNK):
        exec_many(conn, sql, part)


def upsert_dim_produto_canonico(conn, df: pd.DataFrame):
    sql = text("""
        INSERT INTO DIM_produto_canonico (marca_canonico, nome_canonico, categoria_canonica)
        VALUES (:marca, :nome, :categoria)
        ON DUPLICATE KEY UPDATE
          marca_canonico=VALUES(marca_canonico),
          nome_canonico=VALUES(nome_canonico),
          categoria_canonica=VALUES(categoria_canonica)
    """)
    prod = (
        df[["marca_canonico", "nome_canonico", "categoria_canonica"]]
        .drop_duplicates()
        .rename(columns={
            "marca_canonico": "marca",
            "nome_canonico": "nome",
            "categoria_canonica": "categoria",
        })
    )
    for part in chunked_df(prod, CHUNK):
        exec_many(conn, sql, part)


def fetch_marketplace_map(conn, df: pd.DataFrame) -> Dict[str, int]:
    names = df["marketplace"].drop_duplicates().tolist()
    mp_map: Dict[str, int] = {}
    for part in (names[i:i + 800] for i in range(0, len(names), 800)):
        place = ", ".join([f":n{i}" for i in range(len(part))])
        params = {f"n{i}": v for i, v in enumerate(part)}
        rows = conn.execute(
            text(f"SELECT nome, sk_marketplace FROM DIM_marketplace WHERE nome IN ({place})"),
            params
        ).fetchall()
        mp_map.update({nome: sk for nome, sk in rows})
    return mp_map


def fetch_tempo_map(conn, df: pd.DataFrame) -> Dict:
    datas = sorted(df["data_coleta"].drop_duplicates().tolist())
    tempo_map: Dict = {}
    for part in (datas[i:i + 800] for i in range(0, len(datas), 800)):
        place = ", ".join([f":d{i}" for i in range(len(part))])
        params = {f"d{i}": v for i, v in enumerate(part)}
        rows = conn.execute(
            text(f"SELECT data_coleta, sk_tempo FROM DIM_tempo WHERE data_coleta IN ({place})"),
            params
        ).fetchall()
        tempo_map.update({data: sk for data, sk in rows})
    return tempo_map


def upsert_dim_listing(conn, df: pd.DataFrame, mp_map: Dict[str, int]):
    sql = text("""
        INSERT INTO DIM_listing (sk_marketplace, product_url, marca, categoria, titulo)
        VALUES (:sk_marketplace, :url, :marca, :categoria, :titulo)
        ON DUPLICATE KEY UPDATE
          sk_marketplace=VALUES(sk_marketplace),
          marca=COALESCE(VALUES(marca), marca),
          categoria=COALESCE(VALUES(categoria), categoria),
          titulo=COALESCE(VALUES(titulo), titulo)
    """)
    listing = (
        df[["marketplace", "product_url", "marca", "categoria", "titulo"]]
        .drop_duplicates(subset=["product_url"])
        .copy()
    )
    listing["sk_marketplace"] = listing["marketplace"].map(mp_map)
    listing = listing.dropna(subset=["sk_marketplace"]).rename(columns={"product_url": "url"})
    listing["sk_marketplace"] = listing["sk_marketplace"].astype(int)
    listing = listing[["sk_marketplace", "url", "marca", "categoria", "titulo"]]
    for part in chunked_df(listing, CHUNK):
        exec_many(conn, sql, part)


def fetch_listing_map(conn, df: pd.DataFrame) -> Dict[str, int]:
    urls = df["product_url"].drop_duplicates().tolist()
    listing_map: Dict[str, int] = {}
    for part in (urls[i:i + 800] for i in range(0, len(urls), 800)):
        place = ", ".join([f":u{i}" for i in range(len(part))])
        params = {f"u{i}": v for i, v in enumerate(part)}
        rows = conn.execute(
            text(f"SELECT product_url, sk_listing FROM DIM_listing WHERE product_url IN ({place})"),
            params
        ).fetchall()
        listing_map.update({u: sk for u, sk in rows})
    return listing_map


def fetch_produto_map(conn, df: pd.DataFrame) -> Dict[Tuple, int]:
    prod_df = (
        df[["marca_canonico", "nome_canonico", "categoria_canonica"]]
        .drop_duplicates()
        .copy()
    )
    rows = prod_df.to_records(index=False).tolist()
    prod_map: Dict[Tuple, int] = {}
    for part in (rows[i:i + 200] for i in range(0, len(rows), 200)):
        where = " OR ".join(
            [f"(marca_canonico <=> :m{i} AND nome_canonico=:n{i} AND categoria_canonica=:c{i})"
             for i in range(len(part))]
        )
        params = {}
        for i, (m, n, c) in enumerate(part):
            if isinstance(m, float) and math.isnan(m):
                m = None
            if isinstance(n, float) and math.isnan(n):
                n = None
            if isinstance(c, float) and math.isnan(c):
                c = None
            params[f"m{i}"] = m
            params[f"n{i}"] = n
            params[f"c{i}"] = c
        q = text(f"""
            SELECT marca_canonico, nome_canonico, categoria_canonica, sk_produto
            FROM DIM_produto_canonico
            WHERE {where}
        """)
        res = conn.execute(q, params).fetchall()
        for m, n, c, sk in res:
            prod_map[(m, n, c)] = sk
    return prod_map


def upsert_bridge(conn, df: pd.DataFrame, listing_map: Dict[str, int], prod_map: Dict[Tuple, int]):
    sql = text("""
        INSERT INTO BRIDGE_produto_listing (sk_produto, sk_listing, match_score, metodo)
        VALUES (:sk_produto, :sk_listing, :match_score, :metodo)
        ON DUPLICATE KEY UPDATE
          match_score=VALUES(match_score),
          metodo=VALUES(metodo)
    """)

    rows = []
    for r in df.itertuples(index=False):
        m = r.marca_canonico
        if isinstance(m, float) and math.isnan(m):
            m = None
        key = (m, r.nome_canonico, r.categoria_canonica)

        sk_listing = listing_map.get(r.product_url)
        sk_prod = prod_map.get(key)
        if sk_listing and sk_prod:
            rows.append({
                "sk_produto": int(sk_prod),
                "sk_listing": int(sk_listing),
                "match_score": 1.00,
                "metodo": "silver_exact"
            })

    uniq = {(x["sk_produto"], x["sk_listing"]): x for x in rows}
    bridge_df = pd.DataFrame(list(uniq.values()))

    for part in chunked_df(bridge_df, CHUNK):
        exec_many(conn, sql, part)


def upsert_fato_preco(conn, df: pd.DataFrame, tempo_map: Dict, listing_map: Dict[str, int]):
    sql = text("""
        INSERT INTO FATO_preco (sk_tempo, sk_listing, preco, avaliacao, em_estoque)
        VALUES (:sk_tempo, :sk_listing, :preco, :avaliacao, :em_estoque)
        ON DUPLICATE KEY UPDATE
          preco=VALUES(preco),
          avaliacao=COALESCE(VALUES(avaliacao), avaliacao),
          em_estoque=VALUES(em_estoque)
    """)
    rows = []
    for r in df.itertuples(index=False):
        sk_tempo = tempo_map.get(r.data_coleta)
        sk_listing = listing_map.get(r.product_url)

        if sk_tempo and sk_listing:
            rating = r.rating
            if isinstance(rating, float) and math.isnan(rating):
                rating = None

            rows.append({
                "sk_tempo": int(sk_tempo),
                "sk_listing": int(sk_listing),
                "preco": float(r.price),
                "avaliacao": rating,
                "em_estoque": 1 if bool(r.in_stock) else 0
            })

    fato_df = pd.DataFrame(rows)
    for part in chunked_df(fato_df, CHUNK):
        exec_many(conn, sql, part)


def print_counts(conn):
    tables = [
        "DIM_marketplace",
        "DIM_tempo",
        "DIM_produto_canonico",
        "DIM_listing",
        "BRIDGE_produto_listing",
        "FATO_preco",
    ]
    for t in tables:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"{t}: {n}")


def run(engine: Engine):
    df = load_silver_all(CSV_PATH)
    print(f"Linhas no silver_all (válidas): {len(df)}")
    with engine.begin() as conn:
        upsert_dim_marketplace(conn, df)
        upsert_dim_tempo(conn, df)
        upsert_dim_produto_canonico(conn, df)
        mp_map = fetch_marketplace_map(conn, df)
        tempo_map = fetch_tempo_map(conn, df)
        upsert_dim_listing(conn, df, mp_map)
        listing_map = fetch_listing_map(conn, df)
        prod_map = fetch_produto_map(conn, df)
        upsert_bridge(conn, df, listing_map, prod_map)
        upsert_fato_preco(conn, df, tempo_map, listing_map)
        print_counts(conn)


if __name__ == "__main__":
    print("RODANDO:", os.path.abspath(__file__))
    engine = get_engine()
    run(engine)
