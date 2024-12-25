# anubis

Evaluation dataset for eCommerce search solutions. This repository processes and prepares the ESCI dataset from Amazon Science for eCommerce search evaluation.

## Prerequisites

- Python 3.6+
- Zstd (installation instructions below)
- Git

## Setup Instructions

1. Clone the repository and get the ESCI data:

```bash
# Clone this repository
git clone https://github.com/your-username/anubis.git
cd anubis

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

# Filter for US locale and create en_esci.json
grep '"locale":"us"' esci.json > en_esci.json
```

3. Verify the product distribution:

```bash
# Run the distribution script
python3 esci-s/product_distribution.py

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

## Usage

1. Fetch, validate, and store products for a category:

```bash
python3 src/fetch_products.py ELECTRONICS
```

2. Fetch queries for a category:

```bash
python3 src/fetch_queries.py ELECTRONICS --labels E S --locale us
```

### Available Options

- `--locale`: Product locale (us/es/jp), default: "us"
- `--labels`: ESCI labels to include (E/S/C/I), default: all labels

## Output

The scripts will create a `output` directory containing:

- `{category}_asins.json`: List of valid ASINs for the category
- `{category}_{locale}_{labels}_queries.json`: Queries and their associated products

## Directory Structure

```bash
anubis/
├── esci-data/                      # Cloned ESCI repository
├── esci-s/                         # ESCI dataset files
│   ├── esci.json                   # Decompressed dataset
│   ├── en_esci.json                # US locale dataset
│   └── product_distribution.py
├── src/                            # Source code
│   ├── validate-product-images.py
│   └── fetch-category-queries.py
└── output/                         # Generated files
```
