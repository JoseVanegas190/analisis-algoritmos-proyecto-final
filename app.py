"""Interfaz final del proyecto de análisis de algoritmos."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

from src.abstract_extractor import extract_directory, save_results
from src.corpus_audit import audit_records
from src.requirement_one import compare_selected_articles, load_articles
from src.requirement_three import run_term_ranking
from src.requirement_two import run_hierarchical_clustering

ROOT = Path(__file__).parent
ABSTRACTS_PATH = ROOT / "data" / "processed" / "abstracts.json"
RANKING_PATH = ROOT / "data" / "processed" / "term_ranking.json"
CLUSTERING_PATH = ROOT / "data" / "processed" / "clustering.json"
AUDIT_PATH = ROOT / "data" / "processed" / "corpus_audit.json"


def inject_style() -> None:
    st.markdown("""<style>
    .block-container {max-width:1180px;padding-top:2.2rem;padding-bottom:3rem}
    .hero {background:linear-gradient(115deg,#18334A,#24516B 58%,#C65D46 160%);color:#fff;border-radius:22px;padding:2.1rem 2.3rem;margin-bottom:1.5rem;box-shadow:0 14px 30px rgba(24,51,74,.16)}
    .hero h1 {font-size:2.15rem;margin:0 0 .55rem;color:#fff}.hero p{font-size:1.02rem;margin:0;color:#EAF1F4;max-width:760px}
    .hero-kicker,.section-label{font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;font-weight:800}.hero-kicker{color:#F4D8A2;margin-bottom:.45rem}.section-label{color:#C65D46}
    .tag{display:inline-block;margin-top:1rem;margin-right:.4rem;padding:.32rem .66rem;border-radius:999px;background:rgba(255,255,255,.14);font-size:.82rem}
    [data-testid="stMetric"]{background:#fff;border:1px solid #E6DDD0;padding:.8rem 1rem;border-radius:14px;box-shadow:0 5px 14px rgba(45,52,54,.05)}
    [data-testid="stDataFrame"]{border-radius:14px;overflow:hidden;border:1px solid #E6DDD0}.stButton>button{border-radius:10px;font-weight:700;padding:.58rem 1.05rem}
    </style>""", unsafe_allow_html=True)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (OSError, json.JSONDecodeError):
        return None


def download(path: Path, label: str, key: str) -> None:
    if path.exists():
        st.download_button(label, path.read_bytes(), file_name=path.name, key=key)


def hero() -> None:
    st.markdown("""<div class="hero"><div class="hero-kicker">Análisis de Algoritmos · Proyecto final</div>
    <h1>Del abstract a la evidencia</h1><p>Compara artículos con algoritmos clásicos e IA, construye agrupamientos jerárquicos y conserva el ranking de términos como evidencia complementaria.</p>
    <span class="tag">Similitud clásica</span><span class="tag">Embeddings IA</span><span class="tag">Clustering explícito</span></div>""", unsafe_allow_html=True)


def overview() -> None:
    abstracts = load_json(ABSTRACTS_PATH) or []
    ranking = load_json(RANKING_PATH)
    a, b, c = st.columns(3)
    a.metric("Abstracts disponibles", sum(1 for item in abstracts if item.get("abstract")), "corpus controlado")
    b.metric("Métodos de similitud", 6, "4 clásicos y 2 de IA")
    c.metric("Linkages implementados", 3, "Single · Complete · Average")
    if ranking:
        st.caption(f"Evidencia adicional disponible: {ranking.get('unique_terms', 0)} términos distintos en el ranking.")


def prepare_page() -> None:
    st.markdown('<div class="section-label">Corpus</div>', unsafe_allow_html=True)
    st.header("Preparar abstracts")
    st.write("Lee los PDF locales y guarda título, autores y abstract para los demás módulos.")
    if st.button("Extraer abstracts", type="primary"):
        with st.spinner("Leyendo PDF y localizando abstracts..."):
            results = extract_directory(ROOT / "data" / "pdfs")
            save_results(results, ABSTRACTS_PATH)
            audit = audit_records([result.__dict__ for result in results])
            AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        found = sum(result.status == "found" for result in results)
        st.success(f"Corpus preparado: {found} abstracts encontrados de {len(results)} PDF.")
    records = load_json(ABSTRACTS_PATH)
    if records:
        st.dataframe([{"Artículo": item["file_name"], "Título": item.get("title", ""), "Estado": item["status"]} for item in records], hide_index=True, width="stretch")
        audit = audit_records(records)
        if audit["records_to_review"]:
            st.warning(f"Auditoría: {audit['records_to_review']} abstracts requieren revisión antes del análisis.")
            st.dataframe(
                [item for item in audit["details"] if item["issues"]],
                hide_index=True,
                width="stretch",
            )
        else:
            st.success(f"Auditoría aprobada: {audit['valid_records']} abstracts con longitud y marcadores válidos.")
    download(ABSTRACTS_PATH, "Descargar abstracts procesados", "download_abstracts")
    download(AUDIT_PATH, "Descargar auditoría del corpus", "download_audit")


def article_label(article: dict[str, str]) -> str:
    return f"{int(article['id']) + 1}. {article['title'].replace(chr(10), ' ')[:95]}"


def similarity_table(result: dict) -> list[dict[str, str | float]]:
    labels = {"levenshtein": "Levenshtein", "needleman_wunsch": "Needleman-Wunsch", "jaccard": "Jaccard", "tfidf_cosine": "TF-IDF + Coseno", "embedding_minilm": "Embedding MiniLM", "embedding_multilingual": "Embedding multilingüe"}
    rows = []
    for group in ("classic", "embeddings"):
        for key, details in result.get(group, {}).items():
            rows.append({"Método": labels[key], "Similitud": round(details["score"], 6), "Tipo": "Clásico" if group == "classic" else "IA"})
    return rows


def similarity_page() -> None:
    st.markdown('<div class="section-label">Requerimiento 1</div>', unsafe_allow_html=True)
    st.header("Similitud textual")
    if not ABSTRACTS_PATH.exists():
        st.warning("Primero prepara el corpus.")
        return
    articles = load_articles(ABSTRACTS_PATH)
    if len(articles) < 2:
        st.warning("Se necesitan al menos dos abstracts válidos.")
        return
    selected = st.multiselect(
        "Artículos para comparar", articles, default=articles[:2], format_func=article_label,
        help="Con dos artículos se produce un caso de estudio; con más, se comparan todos los pares posibles.",
    )
    include_ai = st.checkbox("Incluir los dos modelos de embeddings de IA", value=False, help="La primera ejecución descarga modelos preentrenados.")
    if st.button("Comparar abstracts", type="primary"):
        with st.spinner("Calculando similitudes..."):
            try:
                selected_ids = [article["id"] for article in selected]
                st.session_state["similarity"] = compare_selected_articles(ABSTRACTS_PATH, selected_ids, include_ai)
            except RuntimeError as error:
                st.error(str(error))
    results = st.session_state.get("similarity")
    if results:
        st.subheader("Resultado comparativo")
        all_rows = []
        for result in results:
            pair = f"{result['article_a']['title'][:35]} / {result['article_b']['title'][:35]}"
            for row in similarity_table(result):
                row["Par comparado"] = pair
                all_rows.append(row)
        st.dataframe(all_rows, hide_index=True, width="stretch")
        result = results[0]
        classic = result["classic"]
        with st.expander("Ver la evidencia interna de los algoritmos clásicos"):
            st.caption("Caso de estudio detallado: primer par seleccionado.")
            st.write(f"Levenshtein: distancia {classic['levenshtein']['distance']} sobre {classic['levenshtein']['tokens_a']} y {classic['levenshtein']['tokens_b']} tokens.")
            st.write(f"Jaccard: {len(classic['jaccard']['intersection'])} términos compartidos de una unión de {classic['jaccard']['union_size']}.")
            st.write(f"TF-IDF: {classic['tfidf_cosine']['idf_terms']} términos en el vocabulario del corpus.")
            st.caption("Primeras posiciones de la matriz de Levenshtein:")
            st.dataframe([row[:10] for row in classic['levenshtein']['matrix'][:10]], width="stretch")


def dendrogram(history: list[dict], labels: list[str], title: str):
    figure, axis = plt.subplots(figsize=(11, 4.6))
    positions = {index: float(index) for index in range(len(labels))}
    heights = {index: 0.0 for index in range(len(labels))}
    for step in history:
        left, right, node, height = step["left"], step["right"], step["new_cluster"], step["distance"]
        axis.plot([positions[left], positions[left]], [heights[left], height], color="#24516B")
        axis.plot([positions[right], positions[right]], [heights[right], height], color="#24516B")
        axis.plot([positions[left], positions[right]], [height, height], color="#C65D46")
        positions[node], heights[node] = (positions[left] + positions[right]) / 2, height
    axis.set_xticks(range(len(labels)), labels, rotation=65, ha="right", fontsize=7)
    axis.set_ylabel("Distancia coseno")
    axis.set_title(title)
    axis.grid(axis="y", alpha=.2)
    figure.tight_layout()
    return figure


def clustering_page() -> None:
    st.markdown('<div class="section-label">Requerimiento 2</div>', unsafe_allow_html=True)
    st.header("Agrupamiento jerárquico")
    if not ABSTRACTS_PATH.exists():
        st.warning("Primero prepara el corpus.")
        return
    cluster_count = st.slider("Cantidad de grupos para evaluar", 2, 8, 3)
    if st.button("Construir los tres agrupamientos", type="primary"):
        with st.spinner("Calculando TF-IDF, distancias y fusiones de clusters..."):
            result = run_hierarchical_clustering(ABSTRACTS_PATH, cluster_count)
            CLUSTERING_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            st.session_state["clustering"] = result
    result = st.session_state.get("clustering") or load_json(CLUSTERING_PATH)
    if result:
        st.caption(f"Matriz usada: {result['distance_definition']}. Vocabulario TF-IDF: {result['vector_terms']} términos.")
        rows = [{"Método": name.replace("_", " ").title(), "Silueta": data["silhouette"]} for name, data in result["methods"].items()]
        st.dataframe(rows, hide_index=True, width="stretch")
        labels = [f"A{int(article['id']) + 1}" for article in result["articles"]]
        for name, data in result["methods"].items():
            st.pyplot(dendrogram(data["history"], labels, name.replace("_", " ").title()))
            st.dataframe([{"Grupo": index, "Artículos": ", ".join(f"A{item + 1}" for item in group)} for index, group in enumerate(data["clusters"], start=1)], hide_index=True, width="stretch")
    download(CLUSTERING_PATH, "Descargar resultado de clustering", "download_clustering")


def ranking_page() -> None:
    st.markdown('<div class="section-label">Evidencia complementaria</div>', unsafe_allow_html=True)
    st.header("Ranking de términos")
    if not ABSTRACTS_PATH.exists():
        st.warning("Primero prepara el corpus.")
        return
    repetitions = st.slider("Repeticiones para promediar el tiempo", 1, 200, 30)
    if st.button("Generar ranking", type="primary"):
        result = run_term_ranking(ABSTRACTS_PATH, 15, repetitions)
        RANKING_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        st.session_state["ranking"] = result
    result = st.session_state.get("ranking") or load_json(RANKING_PATH)
    if result:
        st.dataframe([{"Algoritmo": name.replace("_", " ").title(), "Tiempo promedio (ms)": data["average_execution_ms"]} for name, data in result["methods"].items()], hide_index=True, width="stretch")
    download(RANKING_PATH, "Descargar ranking", "download_ranking")


st.set_page_config(page_title="Análisis de Algoritmos", page_icon="📊", layout="wide")
inject_style()
with st.sidebar:
    st.markdown("## 📊 Laboratorio de abstracts")
    st.caption("Proyecto final")
    page = st.radio("Navegación", ("Preparar corpus", "Similitud textual", "Clustering jerárquico", "Ranking de términos"), label_visibility="collapsed")
    st.divider()
    st.caption("Algoritmos transparentes")
    st.write("4 clásicos\n\n2 embeddings IA\n\n3 linkages jerárquicos")
hero()
overview()
st.divider()
if page == "Preparar corpus":
    prepare_page()
elif page == "Similitud textual":
    similarity_page()
elif page == "Clustering jerárquico":
    clustering_page()
else:
    ranking_page()
