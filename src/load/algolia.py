"""
Upload products to Algolia.

This script assumes that the index has already been created and the ESCI dataset is available.

Usage:
    python src/load/algolia.py --app-id YOUR_ALGOLIA_APP_ID \
                               --api-key YOUR_ALGOLIA_API_KEY \
                               --index-name YOUR_INDEX_NAME \
                               --products-file path/to/products.json
"""

from typing import Dict, List
import argparse
import asyncio

from algoliasearch.search.client import SearchClient
from tqdm import tqdm

from src.utils import load_json


async def push_data_to_algolia(
    client: SearchClient, index_name: str, products: List[Dict]
):
    for item in tqdm(products):
        await client.save_object(
            index_name=index_name,
            body={
                "id": item["platform_id"],
                "title": item["title"],
                "description": item["description"],
                "attributes": item["attrs"],
                "categories": item["category"],
                "image_url": item["image_url"],
            },
        )


async def main(
    algolia_app_id: str, algolia_api_key: str, index_name: str, products_file: str
):
    client = SearchClient(algolia_app_id, algolia_api_key)
    products = await load_json(products_file)
    await push_data_to_algolia(client, index_name, products)
    await client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Push product data to Algolia index")
    parser.add_argument("--app-id", required=True, help="Algolia Application ID")
    parser.add_argument("--api-key", required=True, help="Algolia API Key")
    parser.add_argument("--index-name", required=True, help="Algolia Index Name")
    parser.add_argument(
        "--products-file", required=True, help="Path to products JSON file"
    )

    args = parser.parse_args()

    asyncio.run(
        main(
            algolia_app_id=args.app_id,
            algolia_api_key=args.api_key,
            index_name=args.index_name,
            products_file=args.products_file,
        )
    )
