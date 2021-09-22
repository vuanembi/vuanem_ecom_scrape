import json
from datetime import datetime
import time

import requests
from fake_useragent import UserAgent

NOW = datetime.utcnow()


def scraper_tiki(session, seller_slug, page=1):
    with session.get(
        f"https://api.tiki.vn/v2/seller/stores/{seller_slug}/products",
        params={
            "limit": 50,
            "page": page,
        },
        headers={
            "Accept": "application/json",
            "User-Agent": UserAgent().firefox,
        },
    ) as r:
        res = r.json()
    data = res["data"]
    return data + scraper_tiki(session, seller_slug, page + 1) if data else []


def transform_tiki(rows):
    return [
        {
            "id": row["id"],
            "sku": row["sku"],
            "name": row["name"],
            "url_key": row["url_key"],
            "url_path": row["url_path"],
            "price": row.get("price"),
            "list_price": row.get("list_price"),
            "price_usd": row.get("price_usd"),
            "discount": row.get("discount"),
            "discount_rate": row.get("discount_rate"),
            "rating_average": row.get("rating_average"),
            "review_count": row.get("review_count"),
            "order_count": row.get("order_count"),
            "favourite_count": row.get("favourite_count"),
            "inventory_status": row.get("inventory_status"),
            "is_visible": row.get("is_visible"),
            "productset_group_name": row.get("productset_group_name"),
            "seller": row.get("seller"),
            "seller_product_id": row.get("seller_product_id"),
            "sp_seller_id": row.get("sp_seller_id"),
            "sp_seller_name": row.get("sp_seller_name"),
            "installment_info": row.get("installment_info"),
        }
        for row in rows
    ]


def scraper_lazada(session, seller_slug, page=1):
    with session.get(
        f"https://www.lazada.vn/{seller_slug}/",
        params={
            "ajax": json.dumps(True),
            "from": "wangpu",
            "lang": "vi",
            "langFlag": "vi",
            "pageTypeId": 2,
            "q": "All-Products",
            "page": page,
        },
        headers={
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": UserAgent().chrome,
        },
    ) as r:
        res = r.json()
    data = res["mods"].get("listItems")
    time.sleep(10)
    return data + scraper_lazada(session, seller_slug, page + 1) if data else []


def transform_lazada(rows):
    return [
        {
            "name": row["name"],
            "nid": row["nid"],
            "productUrl": row["productUrl"],
            "image": row.get("image"),
            "originalPrice": row.get("originalPrice"),
            "originalPriceShow": row.get("originalPriceShow"),
            "price": row.get("price"),
            "promotionId": row.get("promotionId"),
            "priceShow": row.get("priceShow"),
            "discount": row.get("discount"),
            "ratingScore": row.get("ratingScore"),
            "review": row.get("review"),
            "installment": row.get("installment"),
            "tItemType": row.get("tItemType"),
            "location": row.get("location"),
            "cheapest_sku": row.get("cheapest_sku"),
            "sku": row.get("sku"),
            "brandId": row.get("brandId"),
            "brandName": row.get("brandName"),
            "sellerId": row.get("sellerId"),
            "mainSellerId": row.get("mainSellerId"),
            "sellerName": row.get("sellerName"),
            "itemId": row.get("itemId"),
            "skuId": row.get("skuId"),
            "inStock": row.get("inStock"),
            "isAD": row.get("isAD"),
            "addToCart": row.get("addToCart"),
        }
        for row in rows
    ]


def scrape(session, seller_slug, ecom="tiki"):
    add_date_scraped = lambda x: {
        **x,
        "_batched_at": NOW.isoformat(timespec="seconds"),
    }
    if ecom == "tiki":
        scraper = scraper_tiki
        transform = transform_tiki
    elif ecom == "lazada":
        scraper = scraper_lazada
        transform = transform_lazada
    else:
        raise ValueError(ecom)
    with open(
        f"exports/[{ecom}]__[{seller_slug}]__[{NOW.strftime('%Y-%m-%d')}].json", "w"
    ) as f:
        json.dump(
            [add_date_scraped(i) for i in transform(scraper(session, seller_slug))],
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
        ],
        # "lazada": [
        #     "zinus-official-store",
        # ],
    }
    with requests.Session() as session:
        [
            scrape(session, seller_slug, ecom)
            for ecom, seller in sellers.items()
            for seller_slug in seller
        ]


main()
