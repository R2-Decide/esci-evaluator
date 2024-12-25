import json
import os
import argparse
import pandas as pd
from tqdm import tqdm
from product_categories import ProductCategory


def load_valid_asins(category: str) -> list:
    """Load valid ASINs from the output directory"""
    category_filename = category.lower().replace(" & ", "_").replace(" ", "_")
    asins_file = f"output/{category_filename}_asins.json"

    try:
        with open(asins_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"No valid ASINs file found at {asins_file}")
        print("Please run validate-product-images.py first!")
        return []


def fetch_category_queries(
    category: str, valid_asins: list, locale: str, labels: list
) -> list:
    """Fetch queries related to valid ASINs for the given category"""
    base_path = "../esci-data/shopping_queries_dataset"

    print("Reading parquet files...")
    try:
        df_examples = pd.read_parquet(
            f"{base_path}/shopping_queries_dataset_examples.parquet"
        )
        df_products = pd.read_parquet(
            f"{base_path}/shopping_queries_dataset_products.parquet"
        )
    except Exception as e:
        print(f"Error reading parquet files: {e}")
        return []

    print("Filtering products...")
    # Filter products by valid ASINs, locale and labels
    df_examples_filtered = df_examples[
        (df_examples["product_id"].isin(valid_asins))
        & (df_examples["product_locale"] == locale)
        & (df_examples["esci_label"].isin(labels))
    ]

    print("Grouping queries...")
    # Group by query to get all products for each query
    query_groups = (
        df_examples_filtered.groupby("query_id")
        .agg(
            {
                "query": "first",  # Get the query text
                "product_id": list,  # Get list of product IDs
                "esci_label": list,  # Get list of ESCI labels
                "product_locale": list,  # Get list of product locales
            }
        )
        .reset_index()
    )

    # Create the output list with progress bar
    queries_list = []
    for _, row in tqdm(
        query_groups.iterrows(), desc="Processing queries", total=len(query_groups)
    ):
        queries_list.append(
            {
                "query": row["query"],
                "query_id": row["query_id"],
                "product_asins": row["product_id"],
                "esci_labels": row["esci_label"],
                "product_locales": row["product_locale"],
            }
        )

    return queries_list


def save_results(category: str, queries_list: list, locale: str, labels: list) -> None:
    """Save the query results"""
    os.makedirs("output", exist_ok=True)

    # Clean category name for filename
    category_filename = category.lower().replace(" & ", "_").replace(" ", "_")
    labels_str = "".join(sorted(labels))

    # Save queries with their products
    queries_file = f"output/{category_filename}_{locale}_{labels_str}_queries.json"
    with open(queries_file, "w") as f:
        json.dump(queries_list, f, indent=2)

    print(f"\nResults saved:")
    print(f"- Queries data: {queries_file}")
    print(f"Total queries found: {len(queries_list)}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch queries for products in a specific category"
    )
    parser.add_argument(
        "category",
        type=str,
        choices=[cat.name for cat in ProductCategory],
        help="Product category to process",
    )
    parser.add_argument(
        "--locale",
        type=str,
        choices=["us", "es", "jp"],
        default="us",
        help="Product locale (us/es/jp)",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        type=str,
        choices=["E", "S", "C", "I"],
        default=["E", "S", "C", "I"],
        help="ESCI labels to include",
    )

    args = parser.parse_args()

    # Convert enum name to actual category value
    category_value = ProductCategory[args.category].value

    # Load valid ASINs
    print(f"Loading valid ASINs for category: {category_value}")
    valid_asins = load_valid_asins(category_value)

    if not valid_asins:
        return

    print(f"\nFound {len(valid_asins)} valid ASINs")
    print(f"Fetching associated queries for locale: {args.locale}")
    print(f"Including labels: {', '.join(args.labels)}")

    # Fetch and save queries
    queries_list = fetch_category_queries(
        category_value, valid_asins, args.locale, args.labels
    )
    save_results(category_value, queries_list, args.locale, args.labels)


if __name__ == "__main__":
    main()
