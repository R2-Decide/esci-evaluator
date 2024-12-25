import json
import os
from tqdm import tqdm
import requests
from concurrent.futures import ThreadPoolExecutor
import argparse
from product_categories import ProductCategory
from typing import Dict, List, Tuple


def validate_image_url(product: Dict) -> Tuple[bool, Dict]:
    """Validate if an image URL is actually downloadable and return product info if valid"""
    if not (image_url := product.get("image")) or not (asin := product.get("asin")):
        return False, {}

    try:
        # Use stream=True to only download the headers and first chunk initially
        response = requests.get(image_url, stream=True, timeout=5)

        if response.status_code == 200:
            # Try to get the first chunk of the image (1024 bytes)
            try:
                next(response.iter_content(1024))
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
            except StopIteration:
                # If we can't get the first chunk, the image is probably empty
                return False, {}
            finally:
                response.close()  # Always close the connection
        else:
            return False, {}

    except Exception as e:
        print(f"\nError validating {asin}: {str(e)}")
    return False, {}


def process_category(category: str) -> Tuple[List[Dict], List[str]]:
    """Process products for a given category and return valid products and ASINs"""
    # Load and filter products for the given category
    valid_products = []
    valid_asins = []

    print(f"Loading products for category: {category}...")
    try:
        # Changed path to point to esci-s directory
        json_path = "../esci-s/en_esci.json"
        if not os.path.exists(json_path):
            print(f"Error: Cannot find {json_path}")
            print("Please make sure you're running the script from the src directory")
            print("Expected directory structure:")
            print("root/")
            print("  ├── esci-s/")
            print("  │   └── en_esci.json")
            print("  └── src/")
            print("      └── validate-product-images.py")
            return [], []

        with open(json_path, "r") as f:
            products = []
            for line in f:
                product = json.loads(line)
                if product.get("category") and product["category"][0] == category:
                    products.append(product)
    except FileNotFoundError:
        print(f"Error: {json_path} not found!")
        print("Please make sure you're running the script from the correct directory")
        return [], []
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in the file")
        return [], []
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return [], []

    print(f"\nFound {len(products)} products in category {category}")

    if not products:
        print(f"Warning: No products found for category '{category}'")
        print("Available categories in the first few products:")
        try:
            with open(json_path, "r") as f:
                sample_categories = set()
                for _ in range(1000):  # Check first 1000 products
                    line = f.readline()
                    if not line:
                        break
                    product = json.loads(line)
                    if product.get("category"):
                        sample_categories.add(product["category"][0])
                print("\n".join(sorted(sample_categories)))
        except Exception:
            pass
        return [], []

    # Validate image URLs with progress bar
    successful = []

    with tqdm(total=len(products), desc="Validating image URLs") as pbar:
        with ThreadPoolExecutor(max_workers=10) as executor:
            for success, product_info in executor.map(validate_image_url, products):
                if success:
                    successful.append(product_info)
                    valid_asins.append(product_info["asin"])
                pbar.update(1)

    return successful, valid_asins


def save_results(category: str, products: List[Dict], asins: List[str]) -> None:
    """Save results to JSON files"""
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)

    # Clean category name for filename
    category_filename = category.lower().replace(" & ", "_").replace(" ", "_")

    # Save full product data
    product_file = f"output/{category_filename}.json"
    with open(product_file, "w") as f:
        json.dump(products, f, indent=2)

    # Save ASINs list to three formats
    # 1. One ASIN per line
    asins_file = f"output/{category_filename}_asins.txt"
    with open(asins_file, "w") as f:
        f.write("\n".join(asins))

    # 2. Comma-separated single line
    asins_csv = f"output/{category_filename}_asins_single_line.txt"
    with open(asins_csv, "w") as f:
        f.write(",".join(asins))

    # 3. JSON format
    asins_json = f"output/{category_filename}_asins.json"
    with open(asins_json, "w") as f:
        json.dump(asins, f, indent=2)

    print(f"\nResults saved:")
    print(f"- Product data: {product_file}")
    print(f"- ASINs list (one per line): {asins_file}")
    print(f"- ASINs list (single line): {asins_csv}")
    print(f"- ASINs list (JSON): {asins_json}")
    print(f"\nTotal valid products/ASINs: {len(asins)}")


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Validate product images for a specific category"
    )
    parser.add_argument(
        "category",
        type=str,
        choices=[
            cat.name for cat in ProductCategory
        ],  # Use enum names instead of values
        help="Product category to process (use enum name, e.g., ELECTRONICS, BOOKS, etc.)",
    )

    args = parser.parse_args()

    # Convert enum name to actual category value
    category_value = ProductCategory[args.category].value

    # Process the category
    valid_products, valid_asins = process_category(category_value)

    # Print summary
    print(f"\nValidation complete!")
    print(f"Successfully validated products: {len(valid_products)}")

    # Save results
    save_results(args.category, valid_products, valid_asins)


if __name__ == "__main__":
    main()
