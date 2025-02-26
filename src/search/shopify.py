"""
Benchmark Shopify search queries.

This script evaluates Shopify search performance on a set of queries and saves the results.

Usage:
    python src/search/shopify.py --shop-url YOUR_SHOP_URL \
                                 --access-token YOUR_ACCESS_TOKEN \
                                 --queries-file path/to/queries.json \
                                 --output-file shopify_results.json \
                                 --count 25 \
                                 --api-version 2024-10
"""

import argparse
import asyncio
from typing import Dict, List

import requests
from tqdm import tqdm

from src.utils import load_json, save_json
from src.logger import get_logger

logger = get_logger(__name__)


def get_product_ids(response):
    """Extract product IDs from Shopify search response"""
    try:
        products = response.json()["data"]["products"]["edges"]
        return [product["node"]["sku"] for product in products]
    except KeyError:
        logger.error(f"Error in response format: {response.json()}")
        return []


def create_graphql_query(query_text: str, count: int = 25) -> Dict:
    """Create a GraphQL query for Shopify product search"""
    return {
        "query": f"""
    query SearchProducts {{
        products(first: {count}, query: "title:{query_text}") {{
            edges {{
                node {{
                    id
                    title
                    sku
                }}
            }}
        }}
    }}
    """
    }


async def search_shopify(
    shop_url: str,
    access_token: str,
    api_version: str,
    queries: List[Dict],
    count: int = 25,
):
    """Run benchmark search queries against Shopify store"""
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json",
    }
    results = []

    for query in tqdm(queries, desc="Running search queries"):
        url = f"https://{shop_url}/admin/api/{api_version}/graphql.json"
        data = create_graphql_query(query["query"], count)

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        results.append(
            {
                "query_id": query["query_id"],
                "query": query["query"],
                "response": get_product_ids(response),
            }
        )

        await asyncio.sleep(1)

    return results


async def main(
    shop_url: str,
    access_token: str,
    queries_file: str,
    output_file: str,
    count: int = 25,
    api_version: str = "2024-10",
):
    """Main function to run Shopify search benchmark"""
    logger.info(f"Loading queries from {queries_file}...")
    queries = await load_json(queries_file)
    logger.info(f"Running {len(queries)} search queries against Shopify...")

    results = await search_shopify(shop_url, access_token, api_version, queries, count)

    logger.info(f"Saving results to {output_file}...")
    await save_json(output_file, results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark Shopify search queries")
    parser.add_argument(
        "--shop-url",
        required=True,
        help="Shopify store URL (e.g. your-store.myshopify.com)",
    )
    parser.add_argument(
        "--access-token", required=True, help="Shopify Admin API access token"
    )
    parser.add_argument(
        "--queries-file", required=True, help="Path to queries JSON file"
    )
    parser.add_argument(
        "--output-file",
        default="shopify_results.json",
        help="Path to save results (default: shopify_results.json)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=25,
        help="Number of results per query (default: 25)",
    )
    parser.add_argument(
        "--api-version",
        default="2024-10",
        help="Shopify API version (default: 2024-10)",
    )

    args = parser.parse_args()

    asyncio.run(
        main(
            shop_url=args.shop_url,
            access_token=args.access_token,
            queries_file=args.queries_file,
            output_file=args.output_file,
            count=args.count,
            api_version=args.api_version,
        )
    )
