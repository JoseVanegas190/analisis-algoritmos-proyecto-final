"""Regenera la evidencia reproducible usada por las figuras y el informe final."""

from __future__ import annotations

import json
import argparse
from pathlib import Path

from src.requirement_one import compare_articles
from src.requirement_two import run_hierarchical_clustering


ROOT = Path(__file__).parents[1]
ABSTRACTS = ROOT / "data" / "processed" / "abstracts.json"
OUTPUT = ROOT / "data" / "processed" / "final_evidence.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenera la evidencia del proyecto final.")
    parser.add_argument(
        "--without-embeddings",
        action="store_true",
        help="Actualiza las métricas clásicas y clustering, conservando los embeddings ya medidos.",
    )
    arguments = parser.parse_args()

    previous_evidence = {}
    if OUTPUT.exists():
        previous_evidence = json.loads(OUTPUT.read_text(encoding="utf-8"))

    case_study = compare_articles(ABSTRACTS, "2", "7", include_embeddings=not arguments.without_embeddings)
    if arguments.without_embeddings:
        previous_embeddings = previous_evidence.get("case_study", {}).get("embeddings")
        if previous_embeddings is None:
            raise RuntimeError("No existe evidencia previa de embeddings para conservar.")
        case_study["embeddings"] = previous_embeddings
    clustering = run_hierarchical_clustering(ABSTRACTS, cluster_count=3)
    evidence = {
        "case_study": case_study,
        "clustering": clustering,
        "distance_definition": clustering["distance_definition"],
        "embeddings_regenerated": not arguments.without_embeddings,
    }
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Evidencia actualizada: {OUTPUT}")


if __name__ == "__main__":
    main()
