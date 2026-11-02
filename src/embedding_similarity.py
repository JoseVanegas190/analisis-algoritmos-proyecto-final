"""Comparación con embeddings preentrenados y métrica coseno propia."""

from __future__ import annotations

from math import sqrt

MODEL_ONE = "all-MiniLM-L6-v2"
MODEL_TWO = "paraphrase-multilingual-MiniLM-L12-v2"


def cosine_similarity_dense(vector_a: list[float], vector_b: list[float]) -> float:
    """Calcula manualmente el coseno de dos vectores densos."""
    if len(vector_a) != len(vector_b):
        raise ValueError("Los vectores deben tener la misma dimensión")
    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for index in range(len(vector_a)):
        dot_product += vector_a[index] * vector_b[index]
        norm_a += vector_a[index] * vector_a[index]
        norm_b += vector_b[index] * vector_b[index]
    return 0.0 if norm_a == 0 or norm_b == 0 else dot_product / (sqrt(norm_a) * sqrt(norm_b))


def embedding_similarity(text_a: str, text_b: str, model_name: str) -> dict:
    """Genera embeddings con un modelo permitido y calcula el coseno explícitamente."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        raise RuntimeError("Falta sentence-transformers. Instala las dependencias del proyecto.") from error
    # Tras la primera descarga, se usa la copia local. Solo si no existe se
    # intenta descargar el modelo, evitando consultas de red en cada análisis.
    try:
        model = SentenceTransformer(model_name, local_files_only=True)
    except OSError:
        model = SentenceTransformer(model_name)
    vectors = model.encode([text_a, text_b], convert_to_numpy=False, show_progress_bar=False)
    vector_a = [float(value) for value in vectors[0]]
    vector_b = [float(value) for value in vectors[1]]
    return {"score": cosine_similarity_dense(vector_a, vector_b), "model": model_name, "dimensions": len(vector_a)}


def compare_embedding_methods(text_a: str, text_b: str) -> dict[str, dict]:
    """Ejecuta dos modelos preentrenados distintos sobre el mismo par."""
    return {
        "embedding_minilm": embedding_similarity(text_a, text_b, MODEL_ONE),
        "embedding_multilingual": embedding_similarity(text_a, text_b, MODEL_TWO),
    }
