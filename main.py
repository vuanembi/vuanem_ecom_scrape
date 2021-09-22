import json

import requests
from fake_useragent import UserAgent


def scrape_tiki(seller_slug, page=1):
    with requests.get(
        f"https://api.tiki.vn/v2/seller/stores/{seller_slug}/products",
        params={
            "limit": 50,
            "page": page,
        },
        headers={
            "User-Agent": UserAgent().firefox,
        },
    ) as r:
        res = r.json()
    data = res["data"]
    return data + scrape_tiki(seller_slug, page + 1) if data else []


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


with open("tiki.json", "w") as f:
    data = transform_tiki(scrape_tiki("vua-nem-official-store"))
    json.dump(data, f)
