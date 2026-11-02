"""Clustering jerárquico aglomerativo implementado con matrices y ciclos."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class MergeStep:
    left: int
    right: int
    new_cluster: int
    distance: float
    size: int


def _members(cluster: dict[int, list[int]], identifier: int) -> list[int]:
    return cluster[identifier]


def _cluster_distance(first: list[int], second: list[int], distances: list[list[float]], method: str) -> float:
    """Calcula Single, Complete o Average recorriendo todos los pares."""
    values: list[float] = []
    for left in first:
        for right in second:
            values.append(distances[left][right])
    if method == "single":
        best = values[0]
        for value in values[1:]:
            if value < best:
                best = value
        return best
    if method == "complete":
        worst = values[0]
        for value in values[1:]:
            if value > worst:
                worst = value
        return worst
    if method == "average":
        total = 0.0
        for value in values:
            total += value
        return total / len(values)
    raise ValueError("Método de linkage no reconocido")


def agglomerative_clustering(distances: list[list[float]], method: str) -> list[MergeStep]:
    """Fusiona repetidamente los dos clusters más cercanos de manera explícita."""
    count = len(distances)
    clusters = {index: [index] for index in range(count)}
    active = [index for index in range(count)]
    history: list[MergeStep] = []
    next_identifier = count
    while len(active) > 1:
        best_left, best_right, best_distance = active[0], active[1], _cluster_distance(clusters[active[0]], clusters[active[1]], distances, method)
        for left_position in range(len(active)):
            for right_position in range(left_position + 1, len(active)):
                left, right = active[left_position], active[right_position]
                distance = _cluster_distance(clusters[left], clusters[right], distances, method)
                if distance < best_distance:
                    best_left, best_right, best_distance = left, right, distance
        merged = clusters[best_left] + clusters[best_right]
        clusters[next_identifier] = merged
        history.append(MergeStep(best_left, best_right, next_identifier, best_distance, len(merged)))
        active = [identifier for identifier in active if identifier != best_left and identifier != best_right]
        active.append(next_identifier)
        next_identifier += 1
    return history


def single_linkage(distances: list[list[float]]) -> list[MergeStep]:
    return agglomerative_clustering(distances, "single")


def complete_linkage(distances: list[list[float]]) -> list[MergeStep]:
    return agglomerative_clustering(distances, "complete")


def average_linkage(distances: list[list[float]]) -> list[MergeStep]:
    return agglomerative_clustering(distances, "average")


def clusters_at_count(history: list[MergeStep], item_count: int, target_count: int) -> list[list[int]]:
    """Corta el árbol antes de las últimas fusiones para obtener k grupos."""
    if target_count < 1 or target_count > item_count:
        raise ValueError("El número de clusters debe estar entre 1 y el total de artículos")
    groups = {index: [index] for index in range(item_count)}
    for step in history[: item_count - target_count]:
        groups[step.new_cluster] = groups[step.left] + groups[step.right]
        del groups[step.left]
        del groups[step.right]
    return list(groups.values())


def serialise_history(history: list[MergeStep]) -> list[dict]:
    return [asdict(step) for step in history]
