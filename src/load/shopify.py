"""
Upload products to Shopify.

This script imports products into a Shopify store and sets the SKU for each product.

Usage:
    python src/load/shopify.py --shop YOUR_STORE_NAME \
                               --token YOUR_ADMIN_API_TOKEN \
                               --products-file path/to/products.json \
                               --api-version 2024-10
"""

import argparse
import asyncio
import json
from typing import Any, Dict, List

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tqdm import tqdm

from src.logger import get_logger
from src.utils import load_json

logger = get_logger(__name__)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(
        (requests.exceptions.RequestException, requests.exceptions.HTTPError)
    ),
)
def create_product(
    shop_url: str, access_token: str, api_version: str, product_item: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a product with automatic retry"""
    endpoint = f"https://{shop_url}.myshopify.com/admin/api/{api_version}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token,
    }
    query = """
    mutation populateProduct($product: ProductCreateInput!, $media: [CreateMediaInput!]) {
        productCreate(product: $product, media: $media) {
            product {
                id
                title
                status
                variants {
                    edges {
                        node {
                            id
                            inventoryItem {
                                id
                            }
                        }
                    }
                }
            }
            userErrors {
                field
                message
            }
        }
    }
    """

    variables = {
        "media": [
            {
                "originalSource": product_item["image_url"],
                "alt": product_item["title"][:255],
                "mediaContentType": "IMAGE",
            }
        ],
        "product": {
            "title": product_item["title"][:255],
            "category": "gid://shopify/TaxonomyCategory/el",
            "descriptionHtml": product_item["description"],
            "handle": product_item["platform_id"],
            "productType": (
                product_item["category"][-1]
                if product_item["category"]
                else "Electronics"
            ),
            "seo": {
                "title": product_item["title"][:255],
                "description": product_item["description"],
            },
            "status": "ACTIVE",
            "tags": product_item["category"],
        },
    }

    response = requests.post(
        endpoint,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()
    result = response.json()

    if errors := result.get("errors"):
        return {"error": errors, "data": product_item}

    if user_errors := result.get("data", {}).get("productCreate", {}).get("userErrors"):
        return {"error": user_errors, "data": product_item}

    return {"result": result["data"]["productCreate"], "data": product_item}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(
        (requests.exceptions.RequestException, requests.exceptions.HTTPError)
    ),
)
def update_sku(
    shop_url: str, access_token: str, api_version: str, inventory_item_id: str, sku: str
) -> Dict[str, Any]:
    """Update SKU with automatic retry"""
    endpoint = f"https://{shop_url}.myshopify.com/admin/api/{api_version}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token,
    }

    # Remove the gid://shopify/InventoryItem/ prefix if present
    if "gid://shopify/InventoryItem/" in inventory_item_id:
        inventory_item_id = inventory_item_id.replace(
            "gid://shopify/InventoryItem/", ""
        )

    query = """
    mutation inventoryItemUpdate($inventoryItemId: ID!, $sku: String!) {
        inventoryItemUpdate(id: $inventoryItemId, input: { sku: $sku }) {
            inventoryItem {
                id
                sku
            }
            userErrors {
                field
                message
            }
        }
    }
    """

    variables = {
        "inventoryItemId": f"gid://shopify/InventoryItem/{inventory_item_id}",
        "sku": sku,
    }

    response = requests.post(
        endpoint,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


async def process_product(
    shop_url: str, access_token: str, api_version: str, product_item: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a single product - create and update SKU"""
    # Create product
    create_result = await asyncio.to_thread(
        create_product, shop_url, access_token, api_version, product_item
    )

    if "error" in create_result:
        return create_result

    # Extract inventory item ID
    try:
        product_data = create_result["result"]["product"]
        variant_edge = product_data["variants"]["edges"][0]
        inventory_item_id = variant_edge["node"]["inventoryItem"]["id"]

        # Update SKU
        sku_result = await asyncio.to_thread(
            update_sku,
            shop_url,
            access_token,
            api_version,
            inventory_item_id,
            product_item["platform_id"],
        )

        # Combine results
        create_result["sku_update"] = sku_result
        return create_result
    except (KeyError, IndexError) as e:
        create_result["error"] = f"Failed to update SKU: {str(e)}"
        return create_result


async def push_products_to_shopify(
    shop_url: str,
    access_token: str,
    api_version: str,
    products: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Import products and update SKUs sequentially"""
    results = []
    for product in tqdm(products, desc="Importing products", unit="product"):
        result = await process_product(shop_url, access_token, api_version, product)
        results.append(result)
        await asyncio.sleep(1)

    return results


async def main(
    shop: str,
    token: str,
    products_file: str,
    api_version: str = "2024-10",
):
    logger.info(f"Loading products from {products_file}...")
    products = await load_json(products_file)
    logger.info(f"Processing {len(products)} products")

    results = await push_products_to_shopify(shop, token, api_version, products)

    # logger.info summary
    success_count = sum(1 for result in results if "error" not in result)
    error_count = sum(1 for result in results if "error" in result)

    logger.info("\nImport Summary")
    logger.info(f"Total products: {len(products)}")
    logger.info(f"Successfully imported: {success_count}")
    logger.info(f"Failed to import: {error_count}")

    if error_count > 0:
        logger.info("\nError details:")
        for result in filter(lambda r: "error" in r, results):
            logger.info(f"\nProduct: {result['data']['title']}")
            logger.error(f"Error: {json.dumps(result['error'], indent=2)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload products to Shopify")
    parser.add_argument(
        "--shop", required=True, help="Shopify store name (e.g. your-store)"
    )
    parser.add_argument("--token", required=True, help="Admin API access token")
    parser.add_argument("--products-file", required=True, help="Path to products.json")
    parser.add_argument("--api-version", default="2024-10", help="Shopify API version")

    args = parser.parse_args()

    asyncio.run(
        main(
            shop=args.shop,
            token=args.token,
            products_file=args.products_file,
            api_version=args.api_version,
        )
    )
