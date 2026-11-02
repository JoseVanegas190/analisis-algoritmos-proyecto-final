"""Controles explícitos de calidad para los abstracts extraídos del corpus."""

from __future__ import annotations

import re

from .text_processing import tokenize


MINIMUM_ABSTRACT_CHARACTERS = 400
LEAK_MARKERS = ("Keywords", "Key words", "Palabras clave", "Introduction", "Introducción")


def audit_abstract(abstract: str | None) -> list[str]:
    """Devuelve alertas legibles, sin modificar silenciosamente el texto."""
    issues: list[str] = []
    if not abstract:
        return ["abstract ausente"]
    if len(abstract) < MINIMUM_ABSTRACT_CHARACTERS:
        issues.append(f"abstract corto: {len(abstract)} caracteres")
    compact = " ".join(abstract.split())
    for marker in LEAK_MARKERS:
        # Solo se marca un encabezado editorial. Una frase normal que mencione
        # "keywords" en minúscula no es una fuga de contenido.
        if re.search(rf"(?:^|[.!?]\s){re.escape(marker)}\b", compact):
            issues.append(f"posible marcador filtrado: {marker}")
            break
    if "\u00ad" in abstract or "\ufffd" in abstract:
        issues.append("carácter de extracción no normalizado")
    if re.search(r"\b[a-z]{2,}-\s+[a-z]{2,}\b", abstract.casefold()):
        issues.append("posible palabra partida por salto de línea")
    return issues


def audit_records(records: list[dict]) -> dict:
    """Audita los registros y resume los resultados para la interfaz y JSON."""
    details: list[dict] = []
    valid_count = 0
    for index, record in enumerate(records, start=1):
        abstract = record.get("abstract")
        issues = audit_abstract(abstract)
        if not issues:
            valid_count += 1
        details.append({
            "article": index,
            "file_name": record.get("file_name", f"Artículo {index}"),
            "characters": len(abstract or ""),
            "tokens": len(tokenize(abstract or "", remove_stopwords=False)),
            "issues": issues,
            "status": "correcto" if not issues else "revisar",
        })
    return {
        "total_records": len(records),
        "valid_records": valid_count,
        "records_to_review": len(records) - valid_count,
        "minimum_abstract_characters": MINIMUM_ABSTRACT_CHARACTERS,
        "details": details,
    }
