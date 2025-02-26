"""
Upload products to Doofinder.

This script transforms and uploads product data to a Doofinder index in batches.
It assumes you have a Doofinder account and the ESCI dataset is available.

Usage:
    python src/load/doofinder.py --token YOUR_DOOFINDER_TOKEN \
                                 --region YOUR_DOOFINDER_INDEX_REGION \
                                 --hash-id YOUR_DOOFINDER_HASH_ID \
                                 --index-name YOUR_INDEX_NAME \
                                 --products-file path/to/products.json \
                                 --output-file doofinder_upload_status.json
"""

import argparse
import asyncio
from typing import Any, Dict, List

import pydoof
from tqdm import tqdm

from src.utils import load_json, save_json


def transform_product(product: Dict[str, Any]) -> Dict[str, Any]:
    """Transform product data to Doofinder format"""
    return {
        "id": product.get("platform_id"),
        "title": product["title"],
        "description": product.get("description", ""),
        "image_url": product.get("image_url", ""),
        "link": product.get("url", ""),
        "price": 0.0,
        "categories": product.get("category", []),
        "availability": "in stock",
    }


def batch(iterable, size=100):
    """Yield successive batches of size from iterable"""
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def push_data_to_doofinder(
    hash_id: str, index_name: str, products: List[Dict[str, Any]]
):
    """Upload products in batches of 100"""
    batches = list(batch(products, 100))
    results = []

    for product_batch in tqdm(batches, desc="Uploading products to Doofinder"):
        transformed_products = [transform_product(product) for product in product_batch]
        result = pydoof.items.bulk_create(hash_id, index_name, transformed_products)
        results.append(result)

    return results


async def main(
    doofinder_token: str,
    doofinder_search_url: str,
    doofinder_management_url: str,
    doofinder_hash_id: str,
    index_name: str,
    products_file: str,
    output_file: str,
):
    pydoof.token = doofinder_token
    pydoof.search_url = doofinder_search_url
    pydoof.management_url = doofinder_management_url

    products = await load_json(products_file)

    results = await asyncio.to_thread(
        push_data_to_doofinder, doofinder_hash_id, index_name, products
    )

    await save_json(output_file, results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload product data to Doofinder index"
    )
    parser.add_argument("--token", required=True, help="Doofinder API Token")
    parser.add_argument("--region", required=True, help="Doofinder Index Region")
    parser.add_argument("--hash-id", required=True, help="Doofinder Hash ID")
    parser.add_argument("--index-name", required=True, help="Doofinder Index Name")
    parser.add_argument(
        "--products-file", required=True, help="Path to products JSON file"
    )
    parser.add_argument(
        "--output-file",
        default="results.json",
        help="Path to save results (default: results.json)",
    )

    args = parser.parse_args()

    search_url = f"https://{args.region}-search.doofinder.com"
    management_url = f"https://{args.region}-api.doofinder.com"
    asyncio.run(
        main(
            doofinder_token=args.token,
            doofinder_search_url=search_url,
            doofinder_management_url=management_url,
            doofinder_hash_id=args.hash_id,
            index_name=args.index_name,
            products_file=args.products_file,
            output_file=args.output_file,
        )
    )
