"""
Benchmark Algolia search queries.

This script evaluates Algolia search performance on a set of queries and saves the results.

Usage:
    python src/search/algolia.py --app-id YOUR_ALGOLIA_APP_ID \
                                 --api-key YOUR_ALGOLIA_API_KEY \
                                 --index-name YOUR_INDEX_NAME \
                                 --queries-file path/to/queries.json \
                                 --output-file algolia_results.json \
                                 --count 25
"""

import argparse
import asyncio
from typing import Dict, List

from algoliasearch.search.client import SearchClient
from tqdm import tqdm

from src.utils import load_json, save_json
from src.logger import get_logger

logger = get_logger(__name__)


def get_product_ids(response):
    """Extract product IDs from Algolia search response"""
    products = response.to_dict()["results"][0]["hits"]
    return [product["id"] for product in products]


async def search_algolia(
    client: SearchClient, index_name: str, queries: List[Dict], count: int = 25
):
    """Run benchmark search queries against Algolia index"""
    results = []
    for query in tqdm(queries, desc="Running search queries"):
        response = await client.search(
            search_method_params={
                "requests": [
                    {
                        "indexName": index_name,
                        "query": query["query"],
                        "hitsPerPage": count,
                    }
                ]
            }
        )
        results.append(
            {
                "query_id": query["query_id"],
                "query": query["query"],
                "response": get_product_ids(response),
            }
        )
    return results


async def main(
    algolia_app_id: str,
    algolia_api_key: str,
    index_name: str,
    queries_file: str,
    output_file: str,
    count: int = 25,
):
    """Main function to run Algolia benchmark"""
    logger.info(f"Loading queries from {queries_file}...")
    client = SearchClient(algolia_app_id, algolia_api_key)
    queries = await load_json(queries_file)
    logger.info(f"Running {len(queries)} search queries against Algolia...")

    results = await search_algolia(client, index_name, queries, count)

    logger.info(f"Saving results to {output_file}...")
    await save_json(output_file, results)
    await client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark Algolia search queries")
    parser.add_argument("--app-id", required=True, help="Algolia Application ID")
    parser.add_argument("--api-key", required=True, help="Algolia API Key")
    parser.add_argument("--index-name", required=True, help="Algolia Index Name")
    parser.add_argument(
        "--queries-file", required=True, help="Path to queries JSON file"
    )
    parser.add_argument(
        "--output-file",
        default="algolia_results.json",
        help="Path to save results (default: algolia_results.json)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=25,
        help="Number of results per query (default: 25)",
    )

    args = parser.parse_args()

    asyncio.run(
        main(
            algolia_app_id=args.app_id,
            algolia_api_key=args.api_key,
            index_name=args.index_name,
            queries_file=args.queries_file,
            output_file=args.output_file,
            count=args.count,
        )
    )
