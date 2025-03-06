# esci-evaluator

Evaluation dataset for eCommerce search solutions. This repository processes and prepares the ESCI dataset from Amazon Science for eCommerce search evaluation.

## Prerequisites

- Python 3.6+
- Zstd (installation instructions below)
- Git

## Setup Instructions

1. Clone the repository and get the ESCI data:

```bash
# Clone this repository
git clone https://github.com/your-username/esci-evaluator.git
cd esci-evaluator

# Clone ESCI data repository
git clone https://github.com/amazon-science/esci-data.git
```

2. Download and prepare the ESCI dataset:

```bash
# Create esci-s directory if it doesn't exist
mkdir -p esci-s

# Download the compressed dataset
wget https://esci-s.s3.amazonaws.com/esci.json.zst -P esci-s/

# Install Zstd
## For Ubuntu/Debian:
sudo apt-get install zstd

## For macOS:
brew install zstd

## For Windows:
## Download from https://github.com/facebook/zstd/releases and add to PATH

# Decompress the dataset
zstd -d esci-s/esci.json.zst
```

3. Verify the product distribution:

```bash
# Run the distribution script
python3 -m src.dataset.product_distribution

# Output should show category distribution similar to:
{
    "Clothing, Shoes & Jewelry": 236346,
    "Home & Kitchen": 142662,
    "Sports & Outdoors": 60114,
    ...
}
```

4. Set up Python environment:

```bash
# Create and activate virtual environment
# Install dependencies and create the virtual environment using Poetry
poetry install

# Activate the virtual environment (if needed, optional step)
poetry shell
```

## Create Dataset

1. Fetch, validate, and store products for a category:

> *Takes about 3-5 minutes to complete*

```bash
python3 -m src.dataset.fetch_products ELECTRONICS --locale us
```

1. Fetch queries for a category:

```bash
python3 -m src.dataset.fetch_queries ELECTRONICS --labels E S --locale us
```

### Available Options

- `--locale`: Product locale (us/es/jp), default: "us"
- `--labels`: ESCI labels to include (E/S/C/I), default: all labels

## Output

The scripts will create a `data` directory containing:

- `{category}.json`: List of products for the category
- `valid_asins_{category}.json`: List of valid ASINs for the category
- `{category}_{locale}_{labels}_queries.json`: Queries and their associated products

## Load Products

Load product data into your search platform of choice:

```zsh
# Load to Algolia
poetry run python src/load/algolia.py --app-id YOUR_APP_ID --api-key YOUR_API_KEY --index-name YOUR_INDEX --products-file data/products.json

# Load to Doofinder
poetry run python src/load/doofinder.py --token YOUR_TOKEN --search-url YOUR_SEARCH_URL --management-url YOUR_MANAGEMENT_URL --hash-id YOUR_HASH_ID --index-name YOUR_INDEX --products-file data/products.json

# Load to Shopify
poetry run python src/load/shopify.py --shop YOUR_SHOP --token YOUR_TOKEN --products-file data/products.json
```

## Run Benchmarks

Run search queries against each platform:

```zsh
# Benchmark Algolia
poetry run python src/search/algolia.py --app-id YOUR_APP_ID --api-key YOUR_API_KEY --index-name YOUR_INDEX --queries-file data/queries.json --output-file results/algolia_results.json

# Benchmark Doofinder
poetry run python src/search/doofinder.py --token YOUR_TOKEN --search-url YOUR_SEARCH_URL --hash-id YOUR_HASH_ID --queries-file data/queries.json --output-file results/doofinder_results.json

# Benchmark Shopify
poetry run python src/search/shopify.py --shop-url YOUR_SHOP_URL --access-token YOUR_ACCESS_TOKEN --queries-file data/queries.json --output-file results/shopify_results.json
```

## Evaluate Results

Evaluate the results using the provided evaluation script:

```bash
python3 -m src.evaluate.evaluate_search_results
```

## License

This project is licensed under the terms of the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
