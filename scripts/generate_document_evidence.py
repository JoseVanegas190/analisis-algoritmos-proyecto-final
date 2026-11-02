"""Genera figuras reales para el informe final a partir del corpus procesado."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

from src.classic_similarity import build_tfidf_vectors, levenshtein_similarity, tokenize
from src.requirement_one import load_articles


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "output" / "evidence"
DATA = ROOT / "data" / "processed" / "final_evidence.json"


def save_similarity_chart(data: dict) -> None:
    case = data["case_study"]
    labels = ["Levenshtein", "Needleman-Wunsch", "Jaccard", "TF-IDF coseno", "MiniLM", "Multilingüe"]
    values = [
        case["classic"]["levenshtein"]["score"], case["classic"]["needleman_wunsch"]["score"],
        case["classic"]["jaccard"]["score"], case["classic"]["tfidf_cosine"]["score"],
        case["embeddings"]["embedding_minilm"]["score"], case["embeddings"]["embedding_multilingual"]["score"],
    ]
    figure, axis = plt.subplots(figsize=(9, 4.8))
    bars = axis.bar(labels, values, color=["#5B7C99"] * 4 + ["#B96545", "#B96545"])
    axis.set_ylim(0, 1)
    axis.set_ylabel("Similitud")
    axis.set_title("Similitud del caso de estudio entre Abstract 3 y Abstract 8")
    axis.tick_params(axis="x", rotation=25)
    for bar, value in zip(bars, values):
        axis.text(bar.get_x() + bar.get_width() / 2, value + .02, f"{value:.3f}", ha="center", fontsize=9)
    figure.tight_layout()
    figure.savefig(EVIDENCE / "comparacion_similitudes.png", dpi=200)
    plt.close(figure)


def save_matrix_and_tfidf(data: dict) -> None:
    articles = load_articles(ROOT / "data" / "processed" / "abstracts.json")
    first, second = articles[2], articles[7]
    result = levenshtein_similarity(first["abstract"], second["abstract"])
    tokens_a, tokens_b = tokenize(first["abstract"])[:9], tokenize(second["abstract"])[:9]
    matrix = [row[:10] for row in result["matrix"][:10]]
    figure, axis = plt.subplots(figsize=(10, 5.5))
    axis.axis("off")
    table = axis.table(cellText=matrix, colLabels=["∅"] + tokens_b, rowLabels=["∅"] + tokens_a, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.45)
    axis.set_title("Fragmento de la matriz de programación dinámica de Levenshtein", pad=16)
    figure.tight_layout()
    figure.savefig(EVIDENCE / "matriz_levenshtein_parcial.png", dpi=200)
    plt.close(figure)

    vectors, idf = build_tfidf_vectors([article["abstract"] for article in articles])
    vector_a, vector_b = vectors[2], vectors[7]
    candidates = []
    for term in vector_a:
        if term in vector_b:
            candidates.append((term, vector_a[term], vector_b[term], idf[term]))
    candidates = candidates[:12]
    rows = [[term, f"{weight_a:.4f}", f"{weight_b:.4f}", f"{term_idf:.4f}"] for term, weight_a, weight_b, term_idf in candidates]
    figure, axis = plt.subplots(figsize=(9, 4.8))
    axis.axis("off")
    table = axis.table(cellText=rows, colLabels=["Término", "TF-IDF A3", "TF-IDF A8", "IDF"], loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    axis.set_title("Pesos TF-IDF de términos compartidos en el caso de estudio", pad=16)
    figure.tight_layout()
    figure.savefig(EVIDENCE / "tabla_tfidf_caso_estudio.png", dpi=200)
    plt.close(figure)


def save_dendrogram(history: list[dict], labels: list[str], title: str, file_name: str) -> None:
    figure, axis = plt.subplots(figsize=(10, 4.8))
    positions = {index: float(index) for index in range(len(labels))}
    heights = {index: 0.0 for index in range(len(labels))}
    for step in history:
        left, right, new, distance = step["left"], step["right"], step["new_cluster"], step["distance"]
        axis.plot([positions[left], positions[left]], [heights[left], distance], color="#2E5873")
        axis.plot([positions[right], positions[right]], [heights[right], distance], color="#2E5873")
        axis.plot([positions[left], positions[right]], [distance, distance], color="#A8513D")
        positions[new] = (positions[left] + positions[right]) / 2
        heights[new] = distance
    axis.set_xticks(range(len(labels)), labels, rotation=55, ha="right", fontsize=8)
    axis.set_ylabel("Distancia coseno")
    axis.set_title(title)
    axis.grid(axis="y", alpha=.2)
    figure.tight_layout()
    figure.savefig(EVIDENCE / file_name, dpi=200)
    plt.close(figure)


def save_clustering_figures(data: dict) -> None:
    clustering = data["clustering"]
    labels = [f"A{int(article['id']) + 1}" for article in clustering["articles"]]
    files = {"single_linkage": "dendrograma_single.png", "complete_linkage": "dendrograma_complete.png", "average_linkage": "dendrograma_average.png"}
    for method, output in files.items():
        save_dendrogram(clustering["methods"][method]["history"], labels, method.replace("_", " ").title(), output)
    rows = [[name.replace("_", " ").title(), f"{item['silhouette']:.6f}"] for name, item in clustering["methods"].items()]
    figure, axis = plt.subplots(figsize=(7, 2.5))
    axis.axis("off")
    table = axis.table(cellText=rows, colLabels=["Método", "Coeficiente Silhouette"], loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)
    axis.set_title("Evaluación interna de los tres agrupamientos", pad=14)
    figure.tight_layout()
    figure.savefig(EVIDENCE / "silhouette.png", dpi=200)
    plt.close(figure)


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    save_similarity_chart(data)
    save_matrix_and_tfidf(data)
    save_clustering_figures(data)
    print(f"Evidencias generadas en {EVIDENCE}")


if __name__ == "__main__":
    main()
