import json
from datetime import datetime
import asyncio

import requests
import aiofiles
import aiohttp

NOW = datetime.utcnow()

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
}


async def get_tiki_products(session, seller_slug, page=1):
    async with session.get(
        f"https://api.tiki.vn/v2/seller/stores/{seller_slug}/products",
        params={
            "limit": 50,
            "page": page,
        },
        headers=HEADERS,
    ) as r:
        res = await r.json()
    data = res["data"]
    return (
        data + await get_tiki_products(session, seller_slug, page + 1) if data else []
    )


async def get_tiki_product_variants(session, id):
    async with session.get(
        f"https://tiki.vn/api/v2/products/{id}",
        params={
            "platform": "web",
            "spid": "114976771",
        },
        headers=HEADERS,
    ) as r:
        res = await r.json()
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


async def get_tiki(session, seller_slug):
    products = await get_tiki_products(session, seller_slug)
    product_ids = [i["id"] for i in products]
    tasks = [
        asyncio.create_task(get_tiki_product_variants(session, id))
        for id in product_ids
    ]
    return asyncio.gather(*tasks)


async def get_shopee_shop_id(session, seller_slug):
    async with session.get(
        "https://shopee.vn/api/v4/shop/get_shop_detail",
        params={
            "sort_sold_out": 0,
            "username": seller_slug,
        },
        headers=HEADERS,
    ) as r:
        res = await r.json()
    return res["data"]["shopid"]


async def get_shopee_products(session, shop_id, offset=0):
    limit = 30
    async with session.get(
        "https://shopee.vn/api/v4/search/search_items",
        params={
            "by": "pop",
            "entry_point": "ShopBySearch",
            "limit": limit,
            "match_id": shop_id,
            "newest": offset,
            "order": "desc",
            "page_type": "shop",
            "scenario": "PAGE_OTHERS",
            "version": 2,
        },
    ) as r:
        res = await r.json()
    results = res["items"]
    next_ = (
        await get_shopee_products(session, shop_id, offset + limit)
        if results
        else results
    )
    return results + next_


async def get_shopee_product_variants(session, item_id, shop_id):
    async with session.get(
        "https://shopee.vn/api/v4/item/get",
        params={
            "itemid": item_id,
            "shopid": shop_id,
        },
        headers=HEADERS,
    ) as r:
        res = await r.json()
    return {
        "itemid": res["data"]["itemid"],
        "name": res["data"]["name"],
        "shopid": res["data"]["shopid"],
        "show_discount": res["data"]["show_discount"],
        "price": res["data"]["price"],
        "price_before_discount": res["data"]["price_before_discount"],
        "price_max": res["data"]["price_max"],
        "price_max_before_discount": res["data"]["price_max_before_discount"],
        "price_min": res["data"]["price_min"],
        "price_min_before_discount": res["data"]["price_min_before_discount"],
        "models": [
            {
                "itemid": model.get("itemid"),
                "modelid": model.get("modelid"),
                "name": model.get("name"),
                "price": model.get("price"),
                "price_before_discount": model.get("price_before_discount"),
            }
            for model in res["data"]["models"]
        ]
        if res["data"].get("models")
        else [],
    }


async def get_shopee(session, seller_slug):
    shop_id = await get_shopee_shop_id(session, seller_slug)
    products = await get_shopee_products(session, shop_id)
    products = [product["item_basic"]["itemid"] for product in products]
    tasks = [
        asyncio.create_task(get_shopee_product_variants(session, item_id, shop_id))
        for item_id in products
    ]
    return asyncio.gather(*tasks)


def main():
    add_date_scraped = lambda x: {
        **x,
        "_batched_at": NOW.isoformat(timespec="seconds"),
    }

    async def scrape(sellers):
        connector = aiohttp.TCPConnector(limit=5)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [
                await scrape_one(session, seller_slug, ecom)
                for ecom, seller in sellers.items()
                for seller_slug in seller
            ]

            data = await asyncio.gather(*tasks)
            for options, data in list(
                zip(
                    [
                        {"ecom": ecom, "seller_slug": seller_slug}
                        for ecom, seller in sellers.items()
                        for seller_slug in seller
                    ],
                    data,
                )
            ):
                with open(
                    f"exports/[{options['ecom']}]__[{options['seller_slug']}]__{NOW.strftime('%Y-%m-%d')}.json",
                    "w",
                ) as f:
                    json.dump([add_date_scraped(i) for i in data], f, indent=4)

    async def scrape_one(session, seller_slug, ecom="tiki"):
        if ecom == "shopee":
            scraper = get_shopee
        elif ecom == "tiki":
            scraper = get_tiki
        return await scraper(session, seller_slug)

    sellers = {
        "tiki": [
            "vua-nem-official-store",
            "ru9-the-sleep-company",
            "zinus-official-store",
            "nem-gia-kho",
            "dem-ha-noi",
        ],
        "shopee": [
            "vua_nem_official_store",
        ],
    }
    asyncio.run(scrape(sellers))


main()
