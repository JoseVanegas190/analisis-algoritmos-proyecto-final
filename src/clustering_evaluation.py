"""Métrica interna explícita para evaluar agrupamientos."""

from __future__ import annotations


def silhouette_score_manual(distances: list[list[float]], clusters: list[list[int]]) -> float:
    """Promedia siluetas individuales a(i) y b(i) sin bibliotecas de clustering."""
    if len(clusters) < 2:
        return 0.0
    assignment: dict[int, int] = {}
    for cluster_index, cluster in enumerate(clusters):
        for item in cluster:
            assignment[item] = cluster_index
    total = 0.0
    for item, own_cluster in assignment.items():
        own_items = clusters[own_cluster]
        if len(own_items) == 1:
            silhouette = 0.0
        else:
            intra_total = 0.0
            for other in own_items:
                if other != item:
                    intra_total += distances[item][other]
            intra = intra_total / (len(own_items) - 1)
            nearest = None
            for cluster_index, cluster in enumerate(clusters):
                if cluster_index == own_cluster:
                    continue
                inter_total = 0.0
                for other in cluster:
                    inter_total += distances[item][other]
                average = inter_total / len(cluster)
                if nearest is None or average < nearest:
                    nearest = average
            scale = max(intra, nearest or 0.0)
            silhouette = 0.0 if scale == 0 else ((nearest or 0.0) - intra) / scale
        total += silhouette
    return total / len(assignment) if assignment else 0.0
