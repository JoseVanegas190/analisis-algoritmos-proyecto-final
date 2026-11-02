"""Coordinación del Requerimiento 2: clustering jerárquico de abstracts."""

from __future__ import annotations

from pathlib import Path

from .classic_similarity import build_tfidf_vectors, cosine_similarity_sparse
from .clustering_evaluation import silhouette_score_manual
from .hierarchical_clustering import (
    average_linkage,
    clusters_at_count,
    complete_linkage,
    serialise_history,
    single_linkage,
)
from .requirement_one import load_articles


def cosine_distance_matrix(vectors: list[dict[str, float]]) -> list[list[float]]:
    """Construye la matriz simétrica 1 - coseno para todos los abstracts."""
    size = len(vectors)
    matrix = [[0.0] * size for _ in range(size)]
    for row in range(size):
        for column in range(row + 1, size):
            distance = 1 - cosine_similarity_sparse(vectors[row], vectors[column])
            matrix[row][column] = distance
            matrix[column][row] = distance
    return matrix


def run_hierarchical_clustering(input_path: str | Path, cluster_count: int = 3) -> dict:
    """Ejecuta los tres linkages y evalúa su silueta sobre la misma matriz."""
    articles = load_articles(input_path)
    if len(articles) < 2:
        raise ValueError("Se requieren al menos dos abstracts para hacer clustering")
    if cluster_count >= len(articles):
        raise ValueError("El número de clusters debe ser menor que el número de abstracts")
    vectors, idf = build_tfidf_vectors([article["abstract"] for article in articles])
    distances = cosine_distance_matrix(vectors)
    implementations = {
        "single_linkage": single_linkage,
        "complete_linkage": complete_linkage,
        "average_linkage": average_linkage,
    }
    methods: dict[str, dict] = {}
    for name, algorithm in implementations.items():
        history = algorithm(distances)
        groups = clusters_at_count(history, len(articles), cluster_count)
        methods[name] = {
            "silhouette": round(silhouette_score_manual(distances, groups), 6),
            "clusters": groups,
            "history": serialise_history(history),
        }
    return {
        "articles": [{"id": article["id"], "title": article["title"]} for article in articles],
        "cluster_count": cluster_count,
        "vector_terms": len(idf),
        "distance_matrix": distances,
        "methods": methods,
        "distance_definition": "1 - similitud coseno TF-IDF calculada manualmente",
    }
