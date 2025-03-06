import asyncio
import math
from typing import Dict, List, Union

from src.utils import append_to_json, load_json


# Compute DCG
def compute_dcg(relevance_scores: List[int], k: int) -> float:
    """Compute Discounted Cumulative Gain (DCG)"""
    dcg = 0
    for i, rel in enumerate(relevance_scores[:k], start=1):
        dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg


# Compute NDCG
def compute_ndcg(
    ground_truth_relevance: List[int], retrieved_relevance: List[int], k: int
) -> float:
    """Compute Normalized Discounted Cumulative Gain (NDCG)"""
    # DCG for retrieved results
    dcg = compute_dcg(retrieved_relevance, k)
    # Ideal DCG (IDCG)
    ideal_relevance = sorted(ground_truth_relevance, reverse=True)
    idcg = compute_dcg(ideal_relevance, k)
    # Avoid division by zero
    return dcg / idcg if idcg > 0 else 0


def get_relevance_score(
    product_id: str,
    query_data: dict[str, str | list[str]],
    relevance_mapping: Dict[str, int],
) -> int:
    """Get relevance score for a product based on ground truth"""
    # If product not in ground truth, return 0 (Irrelevant)
    if product_id not in query_data["product_asins"]:
        return 0

    idx = query_data["product_asins"].index(product_id)
    label = query_data["esci_labels"][idx]
    return relevance_mapping.get(label, 0)


async def compute_metrics(
    ground_truth: List[Dict[str, Union[str, List[str]]]],
    retrieved_results: Dict[str, List[str]],
    relevance_mapping: Dict[str, int],
    k: int = 10,
) -> Dict[str, float]:
    precision_scores = []
    recall_scores = []
    f1_scores = []
    ndcg_scores = []
    reciprocal_ranks = []
    total_relevant_products = 0
    total_queries = len(ground_truth)

    for query_data in ground_truth:
        query_id = str(query_data["query_id"])

        # Get relevant products from ground truth data
        # # Only consider E, S, C as relevant for precision/recall
        relevant_products = [
            asin
            for asin, label in zip(
                query_data["product_asins"], query_data["esci_labels"]
            )
            if label in ["E", "S", "C"]
        ]
        relevant_products_set = set(relevant_products)

        # Get retrieved products
        retrieved_products = retrieved_results.get(query_id, [])[:k]
        retrieved_products = [str(prod_id).upper() for prod_id in retrieved_products]
        retrieved_products_set = set(retrieved_products)

        # Precision@k
        precision = (
            len(relevant_products_set & retrieved_products_set)
            / len(retrieved_products[:k])
            if retrieved_products
            else 0
        )
        precision_scores.append(precision)

        # Recall@k
        recall = (
            len(relevant_products_set & retrieved_products_set)
            / len(relevant_products_set)
            if relevant_products_set
            else 0
        )
        recall_scores.append(recall)

        # F1 Score
        f1 = (
            (2 * precision * recall / (precision + recall))
            if (precision + recall) > 0
            else 0
        )
        f1_scores.append(f1)

        # Mean Reciprocal Rank
        rr: float = 0.0
        for rank, product in enumerate(retrieved_products, start=1):
            if product in relevant_products:
                rr = 1 / rank
                break
        reciprocal_ranks.append(rr)

        # NDCG
        # Ground truth relevance scores sorted by relevance mapping values
        ground_truth_relevance = sorted(
            [relevance_mapping[label] for label in query_data["esci_labels"]],
            reverse=True,
        )

        # Get relevance scores for retrieved products
        retrieved_relevance = [
            get_relevance_score(prod_id, query_data, relevance_mapping)
            for prod_id in retrieved_products
        ]
        ndcg = compute_ndcg(ground_truth_relevance, retrieved_relevance, k)
        ndcg_scores.append(ndcg)

        # Count relevant products shown
        total_relevant_products += len(relevant_products_set & retrieved_products_set)

    # Aggregate metrics
    avg_precision = (
        sum(precision_scores) / len(precision_scores) if precision_scores else 0
    )
    avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0
    avg_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0
    avg_relevant_products = (
        total_relevant_products / total_queries if total_queries else 0
    )

    return {
        "precision@k": avg_precision,
        "recall@k": avg_recall,
        "f1_score": avg_f1,
        "ndcg@k": avg_ndcg,
        "mrr": mrr,
        "avg_relevant_products": avg_relevant_products,
    }


async def evaluate_pipeline(
    ground_truth_path: str,
    results_path: str,
    relevance_mapping: Dict[str, int],
    k: int = 10,
) -> Dict[str, float]:
    ground_truth = await load_json(ground_truth_path)
    # Filter ground truth by number of products
    ground_truth_k = [item for item in ground_truth if len(item["product_asins"]) >= k]
    print(
        f"Number of ground truth queries with at least {k} retrieved products:",
        len(ground_truth_k),
    )

    search_results = await load_json(results_path)
    retrieved_results = {
        str(item["query_id"]): item["response"] for item in search_results
    }
    metrics = await compute_metrics(
        ground_truth_k, retrieved_results, relevance_mapping, k=k
    )

    return metrics


async def main():
    # Relevance mapping for ESCI labels
    relevance_mapping = {
        "E": 3,  # Exact match
        "S": 2,  # Substitute
        "C": 1,  # Complement
        "I": 0,  # Irrelevant
    }

    search_engines = [
        "r2decide",
        "algolia",
        "doofinder",
        "shopify",
    ]

    for engine in search_engines:
        metrics = await evaluate_pipeline(
            ground_truth_path="data/electronics_us_ES_queries.json",
            results_path=f"results/{engine}_results.json",
            relevance_mapping=relevance_mapping,
            k=5,
        )

        await append_to_json("results/benchmark_metrics.json", {engine: metrics})
        print(metrics)


if __name__ == "__main__":
    asyncio.run(main())
