import json
import re
import time
from datetime import datetime
from urllib.parse import quote_plus

import pandas as pd
import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_html(url, session=None, timeout=20, retries=3, backoff_s=1.5):
    session = session or requests.Session()
    last_exc = None

    for attempt in range(retries):
        try:
            resp = session.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            if resp.status_code in (429, 503):
                time.sleep(backoff_s * (attempt + 1))
                continue

            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or resp.encoding
            return resp.text
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(backoff_s * (attempt + 1))

    raise RuntimeError(f"Falha ao baixar a pagina: {url}. Erro: {last_exc}")


def build_search_url(query, offset=1):
    slug = quote_plus(query).replace("+", "-")
    base = f"https://lista.mercadolivre.com.br/{slug}"
    if offset and offset > 1:
        return f"{base}_Desde_{offset}"
    return base


def _to_number_br(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    value_str = str(value)
    value_str = re.sub(r"[^0-9,\.]", "", value_str)

    if value_str.count(",") == 1 and value_str.count(".") >= 1:
        value_str = value_str.replace(".", "").replace(",", ".")
    else:
        value_str = value_str.replace(",", ".")

    try:
        return float(value_str)
    except ValueError:
        return None


def parse_products_from_jsonld(soup):
    products = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        candidates = data if isinstance(data, list) else [data]
        for obj in candidates:
            if not isinstance(obj, dict):
                continue

            item_list = obj.get("itemListElement")
            if not isinstance(item_list, list):
                continue

            for element in item_list:
                item = element.get("item") if isinstance(element, dict) else None
                if not isinstance(item, dict):
                    continue

                offers = item.get("offers") if isinstance(item.get("offers"), dict) else {}
                products.append(
                    {
                        "TITLE": item.get("name"),
                        "PRICE": _to_number_br(offers.get("price")),
                        "URL": item.get("url"),
                    }
                )

    dedup = {}
    for product in products:
        key = product.get("URL") or product.get("TITLE")
        if key and key not in dedup:
            dedup[key] = product
    return list(dedup.values())


def parse_products_from_dom(soup):
    products = []
    items = soup.select("li.ui-search-layout__item, li.ui-search-layout__stack") or []

    for item in items:
        title_el = item.select_one(
            "h2.ui-search-item__title, h2.poly-component__title, a.poly-component__title"
        )
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        link_el = item.select_one("a.ui-search-link, a.poly-component__title")
        url = link_el.get("href") if link_el else None

        price_el = item.select_one(
            "span.andes-money-amount__fraction, div.andes-money-amount-combo__main-container"
        )
        price = _to_number_br(price_el.get_text(" ", strip=True) if price_el else None)
        products.append({"TITLE": title, "PRICE": price, "URL": url})

    return products


def _first_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    return {}


def parse_product_details_from_jsonld(soup):
    product = None
    breadcrumbs = None

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        candidates = data if isinstance(data, list) else [data]
        for obj in candidates:
            if not isinstance(obj, dict):
                continue

            obj_type = obj.get("@type")
            if obj_type == "Product" and product is None:
                product = obj
            if obj_type == "BreadcrumbList" and breadcrumbs is None:
                breadcrumbs = obj

    details = {"CATEGORY": None, "RATING": None, "IN_STOCK": None, "AVAILABILITY": None}

    if isinstance(breadcrumbs, dict):
        elements = breadcrumbs.get("itemListElement")
        if isinstance(elements, list) and elements:
            names = []
            for element in elements:
                if not isinstance(element, dict):
                    continue
                item = element.get("item")
                if isinstance(item, dict) and item.get("name"):
                    names.append(str(item.get("name")).strip())

            if len(names) >= 2:
                names = names[:-1]
            details["CATEGORY"] = " > ".join(names) if names else None

    if details["CATEGORY"] is None and isinstance(product, dict):
        category = product.get("category")
        if isinstance(category, str) and category.strip():
            details["CATEGORY"] = category.strip()

    if isinstance(product, dict):
        aggregate_rating = product.get("aggregateRating")
        if isinstance(aggregate_rating, dict):
            details["RATING"] = _to_number_br(aggregate_rating.get("ratingValue"))

    if isinstance(product, dict):
        offers = _first_dict(product.get("offers"))
        availability = offers.get("availability")
        if isinstance(availability, str) and availability:
            details["AVAILABILITY"] = availability
            if availability.endswith("InStock"):
                details["IN_STOCK"] = True
            elif availability.endswith("OutOfStock"):
                details["IN_STOCK"] = False

    return details


def scrape_search(query, pages=1, sleep_s=1.0):
    session = requests.Session()
    all_products = []

    for page in range(pages):
        offset = 1 + page * 50
        url = build_search_url(query, offset=offset)

        html = fetch_html(url, session=session)
        soup = BeautifulSoup(html, "html.parser")
        products = parse_products_from_jsonld(soup) or parse_products_from_dom(soup)

        if not products:
            raise RuntimeError(
                "Nao foi possivel extrair produtos desta pagina. "
                "O HTML pode ter mudado ou a requisicao foi bloqueada."
            )

        for product in products:
            product["SOURCE_URL"] = url
        all_products.extend(products)
        time.sleep(sleep_s)

    df = pd.DataFrame(all_products)
    df["SCRAPY_DATETIME"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df["PRICE"] = pd.to_numeric(df["PRICE"], errors="coerce")
    df = df.dropna(subset=["TITLE"]).reset_index(drop=True)
    return df


def enrich_with_details(df, max_items=30, sleep_s=1.0):
    if df.empty or "URL" not in df.columns:
        return df

    session = requests.Session()
    urls = [
        url
        for url in df["URL"].dropna().unique().tolist()
        if isinstance(url, str) and url.startswith("http")
    ]
    if max_items is not None:
        urls = urls[: int(max_items)]

    details_by_url = {}
    for url in urls:
        html = fetch_html(url, session=session)
        soup = BeautifulSoup(html, "html.parser")
        details_by_url[url] = parse_product_details_from_jsonld(soup)
        time.sleep(sleep_s)

    details_df = (
        pd.DataFrame.from_dict(details_by_url, orient="index")
        .reset_index()
        .rename(columns={"index": "URL"})
    )
    out_df = df.merge(details_df, on="URL", how="left")
    out_df["RATING"] = pd.to_numeric(out_df.get("RATING"), errors="coerce")
    return out_df
