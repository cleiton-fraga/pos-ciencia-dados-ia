import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from resources.mercado_livre import enrich_with_details, scrape_search


def build_output_path(output_dir, query):
    stamp = datetime.now().strftime("%Y%m%d")
    safe_query = query.strip().replace("/", "-")
    return Path(output_dir) / f"mercado_livre_{safe_query}_{stamp}.json"


def save_dataframe_as_json(df, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_json(output_path, orient="records", date_format="iso", force_ascii=False)
    except Exception:
        records = df.where(pd.notnull(df), None).to_dict(orient="records")
        with output_path.open("w", encoding="utf-8") as file_handle:
            json.dump(records, file_handle, ensure_ascii=False, indent=2)


def parse_args():
    parser = argparse.ArgumentParser(description="Servico de scraping do Mercado Livre.")
    parser.add_argument("--query", required=True, help="Termo de busca.")
    parser.add_argument("--pages", type=int, default=2, help="Quantidade de paginas de busca.")
    parser.add_argument(
        "--search-sleep",
        type=float,
        default=2.0,
        help="Espera entre paginas de busca (segundos).",
    )
    parser.add_argument(
        "--details-sleep",
        type=float,
        default=1.0,
        help="Espera entre paginas de detalhe (segundos).",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=30,
        help="Maximo de produtos para enriquecer com detalhes.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Diretorio de saida do arquivo JSON.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = build_output_path(args.output_dir, args.query)

    df_mercado_livre = scrape_search(
        query=args.query,
        pages=args.pages,
        sleep_s=args.search_sleep,
    )
    df_mercado_livre = enrich_with_details(
        df_mercado_livre, max_items=args.max_items, sleep_s=args.details_sleep
    )
    save_dataframe_as_json(df_mercado_livre, output_path)

    print(f"Arquivo salvo: {output_path.resolve()} ({len(df_mercado_livre)} registros)")


if __name__ == "__main__":
    main()
