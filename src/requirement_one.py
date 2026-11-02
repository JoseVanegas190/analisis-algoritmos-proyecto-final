"""Coordinación del Requerimiento 1: similitud entre abstracts."""

from __future__ import annotations

import json
from pathlib import Path

from .classic_similarity import compare_classic_methods
from .embedding_similarity import compare_embedding_methods


def load_articles(input_path: str | Path) -> list[dict[str, str]]:
    """Carga artículos con abstract; conserva su orden dentro del corpus."""
    records = json.loads(Path(input_path).read_text(encoding="utf-8"))
    articles: list[dict[str, str]] = []
    for index, record in enumerate(records):
        abstract = record.get("abstract")
        if abstract:
            articles.append({
                "id": str(index),
                "title": record.get("title") or record.get("file_name", f"Artículo {index + 1}"),
                "authors": record.get("authors") or "No disponible",
                "abstract": abstract,
            })
    return articles


def compare_articles(input_path: str | Path, first_id: str, second_id: str, include_embeddings: bool = True) -> dict:
    """Compara dos abstracts seleccionados mediante seis enfoques."""
    articles = load_articles(input_path)
    selected: dict[str, dict[str, str]] = {}
    for article in articles:
        if article["id"] == first_id or article["id"] == second_id:
            selected[article["id"]] = article
    if first_id == second_id or first_id not in selected or second_id not in selected:
        raise ValueError("Selecciona dos artículos diferentes que tengan abstract")
    first, second = selected[first_id], selected[second_id]
    corpus = [article["abstract"] for article in articles]
    result = {
        "article_a": {"id": first["id"], "title": first["title"], "authors": first["authors"]},
        "article_b": {"id": second["id"], "title": second["title"], "authors": second["authors"]},
        "classic": compare_classic_methods(first["abstract"], second["abstract"], corpus),
    }
    if include_embeddings:
        result["embeddings"] = compare_embedding_methods(first["abstract"], second["abstract"])
    return result


def compare_selected_articles(input_path: str | Path, selected_ids: list[str], include_embeddings: bool = True) -> list[dict]:
    """Compara cada par posible de una selección dinámica de dos o más artículos."""
    if len(selected_ids) < 2:
        raise ValueError("Selecciona al menos dos artículos")
    results: list[dict] = []
    for first_position in range(len(selected_ids) - 1):
        for second_position in range(first_position + 1, len(selected_ids)):
            results.append(compare_articles(input_path, selected_ids[first_position], selected_ids[second_position], include_embeddings))
    return results
