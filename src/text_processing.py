"""Preprocesamiento transparente de abstracts para los algoritmos clásicos."""

from __future__ import annotations

import re
import unicodedata


# Lista local, visible y revisable. Incluye artículos, pronombres, auxiliares y
# conectores frecuentes en abstracts en inglés y español. Se conserva fuera de
# bibliotecas externas para que el criterio de limpieza sea auditable.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it",
    "of", "on", "or", "that", "the", "this", "to", "with", "y", "de", "del", "la", "las",
    "el", "los", "en", "un", "una", "para", "por", "con", "que", "se", "su", "sus", "al",
    "about", "after", "all", "also", "am", "among", "any", "been", "before", "between",
    "both", "but", "can", "could", "did", "do", "does", "during", "each", "further",
    "had", "has", "have", "he", "her", "here", "hers", "him", "his", "how", "i", "if",
    "into", "its", "itself", "may", "might", "more", "most", "much", "my", "no", "not",
    "our", "ours", "out", "over", "same", "she", "should", "so", "some", "such", "than",
    "their", "theirs", "them", "then", "there", "these", "they", "those", "through", "too",
    "under", "until", "up", "upon", "us", "use", "used", "using", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "whose", "will", "with",
    "would", "you", "your", "yours", "ya", "como", "cuando", "cual", "cuales", "desde",
    "donde", "dos", "esta", "este", "estos", "estas", "fue", "han", "hasta", "hay", "lo",
    "mas", "mi", "mis", "mucho", "muy", "no", "nos", "o", "otra", "otro", "otros", "pero",
    "puede", "pueden", "que", "quien", "se", "segun", "si", "sin", "sobre", "son", "tambien",
    "tiene", "tienen", "todo", "todos", "tras", "uno", "unos", "una", "unas", "y", "ya",
}


def normalise_text(text: str) -> str:
    """Normaliza texto y repara cortes de palabra introducidos por PDFs.

    Un PDF puede extraer ``cur-\n rent`` o incluir el guion suave invisible.
    Esos casos se unen antes de tokenizar para no producir términos falsos como
    ``cur`` y ``rent``. El guion normal entre dos palabras de una misma línea
    se conserva como separador y la expresión regular posterior las tokeniza.
    """
    repaired = text.replace("\u00ad", "")
    repaired = re.sub(r"(?<=\w)[-–—]\s+(?=\w)", "", repaired)
    decomposed = unicodedata.normalize("NFKD", repaired.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    """Tokeniza con una expresión regular y filtros explícitos."""
    words = re.findall(r"[a-z]+", normalise_text(text))
    if not remove_stopwords:
        return words
    return [word for word in words if word not in STOPWORDS]
