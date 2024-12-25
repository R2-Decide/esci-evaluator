"""
Fetch, validate, and store products for a specific category
"""

import argparse
import asyncio
import json
import logging
import os
from typing import Dict, List, Tuple

import aiohttp
from aiohttp import ClientError
from tqdm.asyncio import tqdm

from product_config import ProductCategory
from tqdm import tqdm as tqdm_sync

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def append_to_json(file_path: str, data: List[Dict]) -> None:
    """Append data to a JSON file"""
    if os.path.exists(file_path):
        with open(file_path, "r+", encoding="utf-8") as f:
            existing_data = json.load(f)
            existing_data.extend(data)
            f.seek(0)
            json.dump(existing_data, f, indent=2)
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def load_from_json(file_path: str) -> List[Dict]:
    """Load data from a JSON file"""
    if not os.path.exists(file_path):
        logger.error("Cannot find %s", file_path)
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in tqdm_sync(f, desc="Loading JSON data")]


async def validate_image_url(
    session: aiohttp.ClientSession, product: Dict
) -> Tuple[bool, Dict]:
    """Validate if an image URL is actually downloadable and return product info if valid"""
    if not (image_url := product.get("image")) or not (asin := product.get("asin")):
        return False, {}

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(image_url, timeout=timeout) as response:
            if response.status == 200:
                # Try to get the first chunk of the image (1024 bytes)
                try:
                    async for _ in response.content.iter_chunked(1024):
                        return True, {
                            "asin": asin,
                            "title": product.get("title", ""),
                            "image_url": image_url,
                            "category": product.get("category", []),
                            "price": product.get("price", ""),
                            "stars": product.get("stars", ""),
                            "ratings": product.get("ratings", ""),
                            "attrs": product.get("attrs", {}),
                            "bullets": product.get("bullets", []),
                            "description": product.get("description", ""),
                            "info": product.get("info", {}),
                            "reviews": product.get("reviews", []),
                            "locale": product.get("locale", ""),
                        }
                except ClientError:
                    return False, {}
            else:
                return False, {}
    except (ClientError, asyncio.TimeoutError) as e:
        logger.error("Error validating %s: %s", asin, str(e))
    return False, {}


async def process_category(category: str, locale: str) -> Tuple[List[Dict], List[str]]:
    """Process products for a given category and return valid products and ASINs"""
    valid_asins = []

    logger.info("Loading products for category: %s...", category)
    json_path = "esci-s/esci.json"
    products = load_from_json(json_path)
    products = [
        product
        for product in tqdm(products, desc="Filtering products by category")
        if product.get("category")
        and product["category"][0] == category
        and product.get("locale") == locale
    ]

    logger.info("Found %d products in category %s", len(products), category)

    if not products:
        logger.warning("No products found for category '%s'", category)
        logger.info("Available categories in the first few products:")
        sample_categories = set(
            product["category"][0] for product in products if product.get("category")
        )
        logger.info("\n".join(sorted(sample_categories)))
        return [], []

    # Validate image URLs with progress bar
    successful = []

    async with aiohttp.ClientSession() as session:
        tasks = [validate_image_url(session, product) for product in products]
        for task in tqdm.as_completed(
            tasks, desc="Validating image URLs", total=len(products)
        ):
            success, product_info = await task
            if success:
                successful.append(product_info)
                valid_asins.append(product_info["asin"])

    return successful, valid_asins


def save_results(category: str, products: List[Dict], asins: List[str]) -> None:
    """Save results to JSON files"""
    os.makedirs("output", exist_ok=True)

    category_filename = category.lower().replace(" & ", "_").replace(" ", "_")

    product_file = f"output/{category_filename}.json"
    append_to_json(product_file, products)

    logger.info("Results saved:")
    logger.info("- Product data: %s", product_file)
    logger.info("Total valid products/ASINs: %d", len(asins))


async def main():
    """Fetch, validate, and store products for a specific category"""
    parser = argparse.ArgumentParser(
        description="Validate product images for a specific category"
    )
    parser.add_argument(
        "category",
        type=str,
        choices=[cat.name for cat in ProductCategory],
        help="Product category to process (use enum name, e.g., ELECTRONICS, BOOKS, etc.)",
    )
    parser.add_argument(
        "--locale",
        type=str,
        choices=["us", "es", "jp"],
        default="us",
        help="Product locale (us/es/jp)",
    )

    args = parser.parse_args()

    category_value = ProductCategory[args.category].value

    valid_products, valid_asins = await process_category(category_value, args.locale)

    logger.info("Validation complete!")
    logger.info("Successfully validated products: %d", len(valid_products))

    save_results(args.category, valid_products, valid_asins)


if __name__ == "__main__":
    asyncio.run(main())
