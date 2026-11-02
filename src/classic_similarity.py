"""Algoritmos clásicos de similitud implementados con estructuras básicas."""

from __future__ import annotations

from math import log, sqrt

from .text_processing import tokenize


def levenshtein_distance(tokens_a: list[str], tokens_b: list[str]) -> tuple[int, list[list[int]]]:
    """Construye explícitamente la matriz de edición entre dos secuencias."""
    rows, columns = len(tokens_a) + 1, len(tokens_b) + 1
    matrix = [[0] * columns for _ in range(rows)]
    for row in range(rows):
        matrix[row][0] = row
    for column in range(columns):
        matrix[0][column] = column
    for row in range(1, rows):
        for column in range(1, columns):
            replacement = matrix[row - 1][column - 1] + (tokens_a[row - 1] != tokens_b[column - 1])
            insertion = matrix[row][column - 1] + 1
            deletion = matrix[row - 1][column] + 1
            matrix[row][column] = min(replacement, insertion, deletion)
    return matrix[-1][-1], matrix


def levenshtein_similarity(text_a: str, text_b: str) -> dict:
    """Normaliza la distancia de Levenshtein como similitud entre 0 y 1."""
    tokens_a, tokens_b = tokenize(text_a), tokenize(text_b)
    distance, matrix = levenshtein_distance(tokens_a, tokens_b)
    scale = max(len(tokens_a), len(tokens_b))
    return {
        "score": 1.0 if scale == 0 else 1 - distance / scale,
        "distance": distance,
        "tokens_a": len(tokens_a),
        "tokens_b": len(tokens_b),
        "matrix": matrix,
    }


def needleman_wunsch_similarity(text_a: str, text_b: str, match: int = 1, mismatch: int = -1, gap: int = -1) -> dict:
    """Alineamiento global de tokens mediante programación dinámica propia."""
    tokens_a, tokens_b = tokenize(text_a), tokenize(text_b)
    rows, columns = len(tokens_a) + 1, len(tokens_b) + 1
    matrix = [[0] * columns for _ in range(rows)]
    for row in range(1, rows):
        matrix[row][0] = matrix[row - 1][0] + gap
    for column in range(1, columns):
        matrix[0][column] = matrix[0][column - 1] + gap
    for row in range(1, rows):
        for column in range(1, columns):
            diagonal = matrix[row - 1][column - 1] + (match if tokens_a[row - 1] == tokens_b[column - 1] else mismatch)
            up = matrix[row - 1][column] + gap
            left = matrix[row][column - 1] + gap
            matrix[row][column] = max(diagonal, up, left)
    score = matrix[-1][-1]
    maximum = max(len(tokens_a), len(tokens_b)) * match
    minimum = max(len(tokens_a), len(tokens_b)) * gap
    normalised = 1.0 if maximum == minimum else (score - minimum) / (maximum - minimum)
    return {"score": normalised, "alignment_score": score, "matrix": matrix, "tokens_a": len(tokens_a), "tokens_b": len(tokens_b)}


def jaccard_similarity(text_a: str, text_b: str) -> dict:
    """Compara conjuntos de términos: intersección dividida por unión."""
    terms_a, terms_b = set(tokenize(text_a)), set(tokenize(text_b))
    union = terms_a | terms_b
    intersection = terms_a & terms_b
    common_terms = [term for term in terms_a if term in terms_b]
    return {"score": 1.0 if not union else len(intersection) / len(union), "intersection": common_terms, "union_size": len(union)}


def build_tfidf_vectors(texts: list[str]) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Calcula TF-IDF manualmente para un corpus, sin vectorizadores externos."""
    token_lists = [tokenize(text) for text in texts]
    document_frequency: dict[str, int] = {}
    for tokens in token_lists:
        seen: set[str] = set()
        for term in tokens:
            if term not in seen:
                document_frequency[term] = document_frequency.get(term, 0) + 1
                seen.add(term)
    total_documents = len(texts)
    idf = {term: log((total_documents + 1) / (frequency + 1)) + 1 for term, frequency in document_frequency.items()}
    vectors: list[dict[str, float]] = []
    for tokens in token_lists:
        counts: dict[str, int] = {}
        for term in tokens:
            counts[term] = counts.get(term, 0) + 1
        size = len(tokens) or 1
        vector = {term: (count / size) * idf[term] for term, count in counts.items()}
        vectors.append(vector)
    return vectors, idf


def cosine_similarity_sparse(vector_a: dict[str, float], vector_b: dict[str, float]) -> float:
    """Calcula producto punto y normas con ciclos explícitos."""
    dot_product = 0.0
    for term, weight in vector_a.items():
        dot_product += weight * vector_b.get(term, 0.0)
    norm_a = sqrt(sum(weight * weight for weight in vector_a.values()))
    norm_b = sqrt(sum(weight * weight for weight in vector_b.values()))
    return 0.0 if norm_a == 0 or norm_b == 0 else dot_product / (norm_a * norm_b)


def tfidf_cosine_similarity(text_a: str, text_b: str, corpus_texts: list[str]) -> dict:
    """Calcula la similitud coseno usando los pesos TF-IDF del corpus completo."""
    vectors, idf = build_tfidf_vectors(corpus_texts)
    # Recalcula los dos vectores con el IDF del corpus, para que la comparación
    # use exactamente el mismo espacio vectorial que todos los abstracts.
    selected_vectors: list[dict[str, float]] = []
    for text in (text_a, text_b):
        tokens = tokenize(text)
        counts: dict[str, int] = {}
        for term in tokens:
            counts[term] = counts.get(term, 0) + 1
        size = len(tokens) or 1
        selected_vectors.append({term: (count / size) * idf.get(term, 0.0) for term, count in counts.items()})
    return {"score": cosine_similarity_sparse(selected_vectors[0], selected_vectors[1]), "vector_terms_a": len(selected_vectors[0]), "vector_terms_b": len(selected_vectors[1]), "idf_terms": len(idf), "corpus_vectors": len(vectors)}


def compare_classic_methods(text_a: str, text_b: str, corpus_texts: list[str]) -> dict[str, dict]:
    """Ejecuta los cuatro algoritmos clásicos sobre el mismo par de abstracts."""
    return {
        "levenshtein": levenshtein_similarity(text_a, text_b),
        "needleman_wunsch": needleman_wunsch_similarity(text_a, text_b),
        "jaccard": jaccard_similarity(text_a, text_b),
        "tfidf_cosine": tfidf_cosine_similarity(text_a, text_b, corpus_texts),
    }
