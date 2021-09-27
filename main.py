import json
from datetime import datetime

import requests
from fake_useragent import UserAgent

NOW = datetime.utcnow()

HEADERS = {
    "Accept": "application/json",
    "User-Agent": UserAgent().firefox,
}


def get_products(session, seller_slug, page=1):
    with session.get(
        f"https://api.tiki.vn/v2/seller/stores/{seller_slug}/products",
        params={
            "limit": 50,
            "page": page,
        },
        headers=HEADERS,
    ) as r:
        res = r.json()
    data = res["data"]
    return data + get_products(session, seller_slug, page + 1) if data else []


def get_product_variants(session, id):
    with session.get(
        f"https://tiki.vn/api/v2/products/{id}",
        params={"platform": "web", "spid": "114976771"},
        headers=HEADERS,
    ) as r:
        res = r.json()
    return {
        "id": res["id"],
        "sku": res["sku"],
        "name": res["name"],
        "url_key": res["url_key"],
        "price": res["price"],
        "list_price": res["list_price"],
        "original_price": res["original_price"],
        "discount": res["discount"],
        "discount_rate": res["discount_rate"],
        "configurable_products": [
            {
                "child_id": config_product.get("child_id"),
                "id": config_product["id"],
                "option1": config_product.get("option1"),
                "option2": config_product.get("option2"),
                "price": config_product["price"],
            }
            for config_product in res.get("configurable_products")
        ]
        if res.get("configurable_products", [])
        else [],
    }


def scrape(session, seller_slug, ecom="tiki"):
    add_date_scraped = lambda x: {
        **x,
        "_batched_at": NOW.isoformat(timespec="seconds"),
    }
    products = get_products(session, seller_slug)
    product_ids = [i["id"] for i in products]
    product_variants = [get_product_variants(session, id) for id in product_ids]
    with open(
        f"exports/[{ecom}]__[{seller_slug}]__[{NOW.strftime('%Y-%m-%d')}].json", "w"
    ) as f:
        json.dump(
            [add_date_scraped(i) for i in product_variants],
            f,
            indent=4,
        )


def main():
    sellers = {
        "tiki": [
            "vua-nem-official-store",
            "ru9-the-sleep-company",
            "zinus-official-store",
            "nem-gia-kho",
            "dem-ha-noi",
        ]
    }
    with requests.Session() as session:
        [
            scrape(session, seller_slug, ecom)
            for ecom, seller in sellers.items()
            for seller_slug in seller
        ]


main()
