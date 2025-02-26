"""
Benchmark Doofinder search queries.

This script evaluates Doofinder search performance on a set of queries and saves the results.

Usage:
    python src/search/doofinder.py --token YOUR_DOOFINDER_TOKEN \
                                  --region YOUR_DOOFINDER_INDEX_REGION \
                                  --hash-id YOUR_DOOFINDER_HASH_ID \
                                  --queries-file path/to/queries.json \
                                  --output-file doofinder_results.json \
                                  --count 25
"""

import argparse
import asyncio
from typing import Dict, List

import pydoof
from tqdm import tqdm

from src.utils import load_json, save_json
from src.logger import get_logger

logger = get_logger(__name__)


def get_product_ids(response):
    """Extract product IDs from Doofinder search response"""
    try:
        products = response["results"]
        return [product["id"] for product in products]
    except KeyError:
        logger.error(f"Error in response format: {response.json()}")
        return []


def search_doofinder(hash_id: str, queries: List[Dict], count: int = 25):
    """Run benchmark search queries against Doofinder index"""
    results = []
    for query in tqdm(queries, desc="Running search queries"):
        response = pydoof.search.query(
            hashid=hash_id,
            query=query["query"],
            rpp=count,
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
    doofinder_token: str,
    doofinder_search_url: str,
    doofinder_hash_id: str,
    queries_file: str,
    output_file: str,
    count: int = 25,
):
    """Main function to run Doofinder benchmark"""
    logger.info(f"Loading queries from {queries_file}...")
    pydoof.token = doofinder_token
    pydoof.search_url = doofinder_search_url

    queries = await load_json(queries_file)
    logger.info(f"Running {len(queries)} search queries against Doofinder...")

    results = await asyncio.to_thread(
        search_doofinder, doofinder_hash_id, queries, count
    )

    logger.info(f"Saving results to {output_file}...")
    await save_json(output_file, results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark Doofinder search queries")
    parser.add_argument("--token", required=True, help="Doofinder API Token")
    parser.add_argument("--region", required=True, help="Doofinder Index Region")
    parser.add_argument("--hash-id", required=True, help="Doofinder Hash ID")
    parser.add_argument(
        "--queries-file", required=True, help="Path to queries JSON file"
    )
    parser.add_argument(
        "--output-file",
        default="doofinder_results.json",
        help="Path to save results (default: doofinder_results.json)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=25,
        help="Number of results per query (default: 25)",
    )

    args = parser.parse_args()

    search_url = f"https://{args.region}-search.doofinder.com"
    asyncio.run(
        main(
            doofinder_token=args.token,
            doofinder_search_url=search_url,
            doofinder_hash_id=args.hash_id,
            queries_file=args.queries_file,
            output_file=args.output_file,
            count=args.count,
        )
    )
