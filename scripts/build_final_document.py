"""Construye el documento técnico final con resultados generados por el proyecto."""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "output" / "evidence"
FORMULAS = EVIDENCE / "formulas"
EVIDENCE_DATA = ROOT / "data" / "processed" / "final_evidence.json"
AUDIT_DATA = ROOT / "data" / "processed" / "corpus_audit.json"
TERM_RANKING_DATA = ROOT / "data" / "processed" / "term_ranking.json"
OUTPUT = ROOT / "output" / "Documento_Final_Analisis_Algoritmos_Actualizado.docx"


def set_font(run, size=11, bold=False, italic=False, color="000000"):
    run.font.name = "Arial"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def set_cell_shading(cell, fill="E7E6E6"):
    properties = cell._tc.get_or_add_tcPr()
    element = OxmlElement("w:shd")
    element.set(qn("w:fill"), fill)
    properties.append(element)


def set_cell_borders(cell):
    properties = cell._tc.get_or_add_tcPr()
    borders = properties.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        properties.append(borders)
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge = borders.find(qn("w:" + side))
        if edge is None:
            edge = OxmlElement("w:" + side)
            borders.append(edge)
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "4")
        edge.set(qn("w:color"), "BFBFBF")


def add_paragraph(document, content="", before=0, after=7, align=None):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = 1.15
    if align is not None:
        paragraph.alignment = align
    if content:
        set_font(paragraph.add_run(content))
    return paragraph


def add_heading(document, content, level=1):
    paragraph = document.add_heading(content, level=level)
    paragraph.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    paragraph.paragraph_format.space_after = Pt(6)
    for run in paragraph.runs:
        set_font(run, 14 if level == 1 else 12, bold=True)
    return paragraph


def add_formula(document, image_name, caption):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run().add_picture(str(FORMULAS / image_name), width=Inches(5.6))
    caption_paragraph = document.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.paragraph_format.space_after = Pt(8)
    set_font(caption_paragraph.add_run(caption), 9, italic=True)


def add_figure(document, image_name, caption, width=6.1):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run().add_picture(str(EVIDENCE / image_name), width=Inches(width))
    caption_paragraph = document.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.paragraph_format.space_after = Pt(8)
    set_font(caption_paragraph.add_run(caption), 9, italic=True)


def add_table(document, headers, rows, widths=None, font_size=9):
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        set_cell_shading(cell)
        set_cell_borders(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if widths:
            cell.width = Cm(widths[index])
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(paragraph.add_run(str(header)), font_size, bold=True)
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cell = cells[index]
            set_cell_borders(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if row_index % 2 == 1:
                set_cell_shading(cell, "F7F7F7")
            if widths:
                cell.width = Cm(widths[index])
            paragraph = cell.paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if index == 0 else WD_ALIGN_PARAGRAPH.LEFT
            set_font(paragraph.add_run(str(value)), font_size)
    document.add_paragraph().paragraph_format.space_after = Pt(3)


def add_page_number(section):
    paragraph = section.footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Página ")
    set_font(run, 9)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    paragraph._p.append(field)


def remove_paragraph_border(paragraph):
    """Evita la línea decorativa predeterminada del estilo Title de Word."""
    properties = paragraph._p.get_or_add_pPr()
    borders = properties.find(qn("w:pBdr"))
    if borders is not None:
        properties.remove(borders)


def add_bullet(document, content):
    paragraph = document.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(3)
    set_font(paragraph.add_run(content))


def add_code(document, content, caption):
    """Inserta un fragmento real de código en fuente monoespaciada."""
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.left_indent = Cm(0.35)
    properties = paragraph._p.get_or_add_pPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), "F2F2F2")
    properties.append(shading)
    run = paragraph.add_run(content)
    run.font.name = "Courier New"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Courier New")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Courier New")
    run.font.size = Pt(8)
    caption_paragraph = document.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.paragraph_format.space_after = Pt(7)
    set_font(caption_paragraph.add_run(caption), 9, italic=True)


def result_rows(case):
    labels = [
        ("Levenshtein", case["classic"]["levenshtein"]["score"], "Clásico"),
        ("Needleman-Wunsch", case["classic"]["needleman_wunsch"]["score"], "Clásico"),
        ("Jaccard", case["classic"]["jaccard"]["score"], "Clásico"),
        ("TF-IDF con coseno", case["classic"]["tfidf_cosine"]["score"], "Clásico"),
        ("Embedding MiniLM", case["embeddings"]["embedding_minilm"]["score"], "IA"),
        ("Embedding multilingüe", case["embeddings"]["embedding_multilingual"]["score"], "IA"),
    ]
    return [[name, f"{score:.6f}", kind] for name, score, kind in labels]


def format_clusters(clusters: list[list[int]]) -> str:
    """Convierte índices internos de clusters en etiquetas A1, A2, ... para el informe."""
    groups = []
    for cluster in clusters:
        labels = ", ".join(f"A{index + 1}" for index in sorted(cluster))
        groups.append("{" + labels + "}")
    return "; ".join(groups)


def main():
    data = json.loads(EVIDENCE_DATA.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_DATA.read_text(encoding="utf-8"))
    ranking_data = json.loads(TERM_RANKING_DATA.read_text(encoding="utf-8"))
    case = data["case_study"]
    clustering = data["clustering"]
    article_a = f"A{case['article_a']['id']}"
    article_b = f"A{case['article_b']['id']}"
    classic = case["classic"]
    levenshtein = classic["levenshtein"]
    needleman = classic["needleman_wunsch"]
    jaccard = classic["jaccard"]
    tfidf = classic["tfidf_cosine"]
    embedding_one = case["embeddings"]["embedding_minilm"]["score"]
    embedding_two = case["embeddings"]["embedding_multilingual"]["score"]
    methods = clustering["methods"]
    single_score = methods["single_linkage"]["silhouette"]
    complete_score = methods["complete_linkage"]["silhouette"]
    average_score = methods["average_linkage"]["silhouette"]
    single_clusters = format_clusters(methods["single_linkage"]["clusters"])
    complete_clusters = format_clusters(methods["complete_linkage"]["clusters"])
    average_clusters = format_clusters(methods["average_linkage"]["clusters"])
    ranking_methods = ranking_data["methods"]
    counting_metrics = ranking_methods["counting_sort"]
    radix_metrics = ranking_methods["radix_sort"]
    bucket_metrics = ranking_methods["bucket_sort"]
    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    add_page_number(section)
    styles = document.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"]._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    styles["Normal"].font.size = Pt(11)

    title = document.add_paragraph(style="Title")
    remove_paragraph_border(title)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(65)
    title.paragraph_format.space_after = Pt(16)
    set_font(title.add_run("Análisis computacional de abstracts científicos mediante algoritmos clásicos e inteligencia artificial"), 18, bold=True)
    for line in [
        "Proyecto final de Análisis de Algoritmos",
        "Universidad del Quindío",
        "Programa de Ingeniería de Sistemas y Computación",
        "Estudiante: José Vanegas",
        "Octubre de 2026",
    ]:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(8)
        set_font(paragraph.add_run(line), 12 if "Proyecto" in line else 11)
    document.add_page_break()

    add_heading(document, "Contenido")
    for item in [
        "1 Introducción", "2 Estructura del proyecto y herramientas utilizadas", "3 Requerimientos e implementación",
        "4 Resultados y análisis crítico", "5 Validación y pruebas", "6 Declaración de uso de inteligencia artificial generativa", "7 Conclusiones", "Referencias", "Anexos",
    ]:
        add_paragraph(document, item, after=3)
    document.add_page_break()

    add_heading(document, "1 Introducción")
    add_paragraph(document, "Este proyecto implementa una aplicación para analizar abstracts de un corpus controlado de 20 artículos científicos relacionados con inteligencia artificial y educación. El problema se aborda desde dos perspectivas: la similitud textual entre documentos y el agrupamiento jerárquico de todo el corpus. La aplicación conserva los resultados procesados para que el análisis pueda repetirse incluso cuando los PDF originales no estén disponibles.")
    add_paragraph(document, "El objetivo es demostrar el funcionamiento interno de los algoritmos mediante estructuras básicas del lenguaje: listas, diccionarios, matrices y ciclos. Para ello se comparan cuatro técnicas clásicas de similitud, dos modelos de embeddings permitidos por el enunciado y tres criterios de clustering jerárquico. El documento presenta sus fórmulas, implementación, resultados reales y validaciones.")

    add_heading(document, "2 Estructura del proyecto y herramientas utilizadas")
    add_heading(document, "2.1 Herramientas y tecnología", 2)
    add_table(document, ["Herramienta", "Uso en el proyecto", "No reemplaza"], [
        ["Python", "Lenguaje para los algoritmos y procesamiento de datos", "El diseño algorítmico"],
        ["PyMuPDF", "Lectura del texto de cada PDF", "La detección explícita del abstract"],
        ["Streamlit", "Interfaz para seleccionar artículos y presentar resultados", "Los cálculos de similitud o clustering"],
        ["Matplotlib", "Dibujo de dendrogramas a partir de fusiones ya calculadas", "El algoritmo de clustering"],
        ["Sentence Transformers", "Generación de embeddings preentrenados permitidos", "El cálculo manual de similitud coseno"],
        ["JSON", "Persistencia de abstracts, resultados y evidencias", "Los algoritmos"],
        ["GitHub", "Versionamiento y distribución del código", "La ejecución local"],
    ], [3.2, 7.3, 5.0])
    add_paragraph(document, "No se utiliza Scikit-learn, SciPy, difflib ni una biblioteca que resuelva directamente los algoritmos solicitados. Las bibliotecas se limitan a lectura de PDF, generación permitida de embeddings, interfaz y visualización.")

    add_heading(document, "2.2 Estructura del proyecto carpeta por carpeta", 2)
    add_table(document, ["Ruta", "Responsabilidad"], [
        ["app.py", "Menú Streamlit con corpus, similitud, clustering y ranking."],
        ["data/pdfs", "Ubicación local esperada para los 20 PDF del corpus."],
        ["data/processed", "Abstracts y resultados serializados en JSON."],
        ["src/abstract_extractor.py", "Lectura y extracción explícita de abstracts."],
        ["src/text_processing.py", "Normalización, tokenización y stopwords locales."],
        ["src/classic_similarity.py", "Levenshtein, Needleman-Wunsch, Jaccard y TF-IDF con coseno."],
        ["src/embedding_similarity.py", "Dos embeddings preentrenados y coseno manual."],
        ["src/hierarchical_clustering.py", "Single, Complete y Average Linkage."],
        ["src/clustering_evaluation.py", "Coeficiente Silhouette implementado manualmente."],
        ["src/requirement_one.py y requirement_two.py", "Coordinación reproducible de los requisitos funcionales."],
        ["tests", "Pruebas automatizadas de casos pequeños y validaciones."],
    ], [6.0, 10.0], 8.5)

    add_heading(document, "2.3 Arquitectura y flujo de procesamiento", 2)
    add_paragraph(document, "El flujo inicia con los PDF y finaliza en resultados reproducibles. Primero se extraen el título, los autores y el abstract. Luego el texto se normaliza a minúsculas, se eliminan tildes, signos y palabras vacías locales. A partir de los tokens se construyen las representaciones requeridas por cada algoritmo: secuencias, conjuntos, vectores TF-IDF, embeddings y matriz de distancias.")
    add_table(document, ["Etapa", "Entrada", "Salida"], [
        ["Extracción", "20 PDF", "Abstracts y metadatos en JSON"],
        ["Preprocesamiento", "Abstracts", "Tokens normalizados"],
        ["Similitud", "Dos o más abstracts", "Puntajes por método"],
        ["Clustering", "20 vectores TF-IDF", "Historia de fusiones y dendrogramas"],
        ["Evaluación", "Clusters y matriz de distancia", "Coeficiente Silhouette"],
    ], [3.0, 6.0, 7.0])

    add_heading(document, "3 Requerimientos e implementación")
    add_heading(document, "3.1 Requerimiento 1 Análisis de similitud textual", 2)
    add_paragraph(document, f"La aplicación permite seleccionar dinámicamente dos o más artículos. Si se seleccionan más de dos, se comparan todos los pares posibles. Para el caso de estudio del documento se escogieron {article_a} y {article_b}, recuperados del mismo corpus procesado. Ambos se analizan con idéntica limpieza y con todas las métricas, de modo que la comparación sea reproducible.")
    add_table(document, ["Abstract", "Título del artículo"], [
        [article_a, case["article_a"]["title"]],
        [article_b, case["article_b"]["title"]],
    ], [2.0, 14.0])

    add_heading(document, "3.1.1 Selección y preprocesamiento de abstracts", 3)
    add_paragraph(document, "La tokenización transforma el texto en una secuencia de palabras. El proceso pasa todo a minúsculas, normaliza caracteres Unicode, repara palabras partidas por saltos de línea, elimina tildes y signos de puntuación y descarta una lista local, visible y ampliable de stopwords en inglés y español. Las secuencias resultantes se usan directamente en Levenshtein y Needleman-Wunsch; los conjuntos en Jaccard; y las frecuencias de documentos en TF-IDF.")
    add_paragraph(document, f"Antes del análisis se ejecutó una auditoría del corpus: {audit['valid_records']} de {audit['total_records']} abstracts quedaron válidos y {audit['records_to_review']} quedaron marcados para revisión. La auditoría detecta abstracts ausentes o demasiado cortos, encabezados editoriales que se filtren al contenido y palabras partidas por la extracción del PDF. Así se evita que una mala extracción, como un abstract truncado o unas palabras clave mezcladas, altere el ranking, las similitudes o los clusters.")
    add_paragraph(document, "Este paso no intenta cambiar el significado de los textos: solamente busca que una misma palabra escrita con mayúscula, tilde o puntuación diferente no sea tratada como tres palabras distintas. Por ejemplo, «Artificial», «artificial» y «artificial,» terminan representadas por el token «artificial». Al eliminar palabras funcionales como «de», «la» o «y», el análisis da más peso a términos del tema, tales como «assessment», «generative» o «education».")
    add_table(document, ["Representación", "Qué conserva", "Qué deja de mirar", "Métodos que la usan"], [
        ["Secuencia de tokens", "Palabras y su orden", "Sinónimos y significado implícito", "Levenshtein, Needleman-Wunsch"],
        ["Conjunto", "Qué términos aparecen al menos una vez", "Orden y repeticiones", "Jaccard"],
        ["Vector TF-IDF", "Frecuencia y relevancia de cada término", "Relaciones semánticas no escritas", "TF-IDF con coseno, clustering"],
        ["Embedding", "Patrones semánticos aprendidos por el modelo", "Trazabilidad palabra a palabra", "Modelos de IA"],
    ], [3.2, 4.5, 4.6, 3.2], 8.2)
    add_paragraph(document, "La tabla anterior es importante para interpretar los resultados: dos algoritmos no responden exactamente la misma pregunta. Una similitud baja en Levenshtein no contradice una similitud alta en embeddings; el primero pregunta si las secuencias se parecen literalmente y el segundo estima si las ideas expresadas están relacionadas.")
    add_paragraph(document, f"Recorrido de ejecución: al escoger {article_a} y {article_b} en la interfaz, el programa recupera sus abstracts desde el archivo JSON procesado. Luego llama a la misma función de tokenización para ambos. A partir de allí no existe un único objeto universal: se construye una lista ordenada cuando importa la posición, un conjunto cuando importa únicamente la presencia de términos y un diccionario cuando se requiere asociar a cada término un peso numérico. Esta decisión explícita evita ocultar el comportamiento de los algoritmos detrás de una biblioteca.")
    add_code(document, "tokens_a = tokenize(abstract_a)\ntokens_b = tokenize(abstract_b)\n\n# La misma entrada limpia alimenta cada representación posterior.\nconjunto_a = set(tokens_a)\nfrecuencias_a = {termino: tokens_a.count(termino) for termino in conjunto_a}", "Fragmento 1. Idea de conversión desde el abstract a estructuras básicas; la implementación real usa ciclos para contar frecuencias.")

    add_heading(document, "3.1.2 Algoritmos clásicos implementados", 3)
    add_paragraph(document, "Levenshtein calcula el número mínimo de inserciones, eliminaciones o sustituciones para transformar una secuencia de tokens en otra. La implementación crea una matriz, inicializa la primera fila y la primera columna, y llena cada posición a partir de tres vecinos.")
    add_formula(document, "levenshtein.png", "Ecuación 1. Recurrencia usada en la matriz de Levenshtein.")
    add_figure(document, "matriz_levenshtein_parcial.png", "Figura 1. Fragmento real de la matriz de Levenshtein para los primeros tokens del caso de estudio.", 6.2)
    add_paragraph(document, f"Cómo se lee la Figura 1: cada fila representa un prefijo de {article_a} y cada columna uno de {article_b}. El número de una celda es el costo mínimo acumulado para transformar el prefijo de la fila en el prefijo de la columna. La primera fila y la primera columna aumentan de uno en uno porque, al comparar con una secuencia vacía, solo es posible insertar o eliminar. En las demás celdas se elige el menor costo de sustituir, insertar o eliminar. La última celda de la matriz completa dio distancia {levenshtein['distance']} para secuencias de {levenshtein['tokens_a']} y {levenshtein['tokens_b']} tokens; al normalizarla se obtiene similitud {levenshtein['score']:.6f}. El valor bajo indica que el orden y la redacción literal de ambos abstracts son muy diferentes.")
    add_code(document, "replacement = matrix[row - 1][column - 1] + (tokens_a[row - 1] != tokens_b[column - 1])\ninsertion = matrix[row][column - 1] + 1\ndeletion = matrix[row - 1][column] + 1\nmatrix[row][column] = min(replacement, insertion, deletion)", "Fragmento 2. Núcleo de levenshtein_distance: cada celda evalúa las tres operaciones permitidas.")
    add_paragraph(document, "En el Fragmento 2, la expresión booleana vale 0 si los tokens coinciden y 1 si son distintos. Por ello, la diagonal representa mantener o sustituir una palabra; la celda de la izquierda representa insertar un token y la celda superior representa eliminarlo. El mínimo guarda la mejor decisión conocida para ese par de prefijos. Al terminar los ciclos, la esquina inferior derecha resume el costo óptimo para las dos secuencias completas. No se usa difflib ni un calculador externo de distancias.")
    add_paragraph(document, "Needleman-Wunsch también usa programación dinámica, pero busca el mejor alineamiento global. La puntuación empleada asigna 1 a una coincidencia, -1 a una sustitución y -1 a una brecha. Cada celda conserva el máximo de las tres alternativas posibles.")
    add_formula(document, "needleman.png", "Ecuación 2. Recurrencia usada por Needleman-Wunsch.")
    add_paragraph(document, f"A diferencia de Levenshtein, este método no cuenta solo ediciones: construye una puntuación de alineamiento. Una coincidencia de tokens aumenta la puntuación; una sustitución o una brecha la disminuye. La última celda produjo una puntuación de alineamiento de {needleman['alignment_score']}, que el programa lleva a una escala de similitud de 0 a 1: {needleman['score']:.6f}. Este resultado es parecido al de Levenshtein porque los abstracts comparten pocas palabras en posiciones equivalentes. Sirve para mostrar que tener el mismo tema no garantiza que dos textos estén redactados con el mismo recorrido de palabras.")
    add_paragraph(document, "Su diferencia conceptual con Levenshtein es útil para la sustentación. Levenshtein minimiza un costo: menor distancia es mejor. Needleman-Wunsch maximiza una recompensa de alineamiento: mayor puntuación es mejor. Después de calcularla, el programa normaliza el resultado a 0–1 para poder exhibirlo junto a las demás similitudes. Ambos llenan matrices de tamaño (m + 1) × (n + 1), por eso los dos tienen tiempo y memoria O(mn).")
    add_paragraph(document, "Jaccard ignora el orden y compara los conjuntos de términos únicos. Un valor cercano a uno indica una gran proporción de vocabulario compartido.")
    add_formula(document, "jaccard.png", "Ecuación 3. Coeficiente de Jaccard.")
    add_paragraph(document, f"En {article_a} y {article_b} aparecieron {len(jaccard['intersection'])} términos compartidos dentro de una unión de {jaccard['union_size']} términos distintos; por eso Jaccard dio {len(jaccard['intersection'])}/{jaccard['union_size']} = {jaccard['score']:.6f}. La intersección puede revisarse directamente en el archivo de evidencia. Aun así, la unión es amplia, por lo que el resultado sigue siendo bajo. Jaccard responde: «¿qué proporción del vocabulario total se comparte?», no «¿cuántas veces se repite una palabra?» ni «¿las frases tienen el mismo orden?».")
    add_code(document, "terms_a, terms_b = set(tokenize(text_a)), set(tokenize(text_b))\nunion = terms_a | terms_b\nintersection = terms_a & terms_b\nscore = len(intersection) / len(union)", "Fragmento 3. Cálculo explícito del coeficiente de Jaccard con conjuntos nativos.")
    add_paragraph(document, "La operación de unión conserva cada palabra una sola vez, incluso si aparece repetida. Esa es una ventaja cuando se quiere evitar que un abstract largo domine por repetir un término, pero también es una limitación: repetir «assessment» diez veces pesa igual que mencionarlo una vez. Esta limitación explica por qué se complementa con TF-IDF.")
    add_paragraph(document, "TF-IDF asigna un peso a cada término según su frecuencia dentro del abstract y su rareza dentro del corpus. El proyecto calcula manualmente la frecuencia del término, la frecuencia documental y cada peso. Luego calcula el producto punto y las normas para obtener la similitud coseno.")
    add_formula(document, "tfidf.png", "Ecuación 4. Peso TF-IDF usado en el proyecto.")
    add_formula(document, "cosine.png", "Ecuación 5. Similitud coseno entre dos vectores.")
    add_figure(document, "tabla_tfidf_caso_estudio.png", f"Figura 2. Pesos reales de términos compartidos entre {article_a} y {article_b}.", 6.1)
    add_paragraph(document, f"La Figura 2 no es una lista de las palabras más repetidas sin más. Cada valor combina dos ideas: TF aumenta si el término aparece varias veces en el abstract e IDF aumenta si el término es poco común dentro de los 20 documentos. Por ello, una palabra muy frecuente en casi todos los abstracts aporta menos información que una palabra específica. Los productos de pesos de términos coincidentes forman el producto punto; después se divide entre las longitudes de los dos vectores. El coseno TF-IDF de {tfidf['score']:.6f} es mayor que Jaccard porque reconoce que algunos términos compartidos aportan más evidencia temática que otros.")
    add_code(document, "for term in tokens:\n    counts[term] = counts.get(term, 0) + 1\n\nvector = {term: (count / size) * idf[term]\n          for term, count in counts.items()}\n\nfor term, weight in vector_a.items():\n    dot_product += weight * vector_b.get(term, 0.0)", "Fragmento 4. Conteo, construcción de pesos TF-IDF y producto punto sin vectorizadores externos.")
    add_paragraph(document, "El primer ciclo del Fragmento 4 crea el diccionario de frecuencias. El tamaño del abstract convierte el conteo absoluto en frecuencia relativa; después se multiplica por IDF. El último ciclo solo suma productos cuando el término aparece en ambos vectores, porque get devuelve 0 para un término ausente. Finalmente se calculan dos normas y se divide el producto punto por su multiplicación. Así se puede seguir cada término que aportó a la similitud.")

    add_heading(document, "3.1.3 Modelos de inteligencia artificial basados en embeddings", 3)
    add_paragraph(document, "Se emplearon dos modelos preentrenados permitidos para convertir cada abstract en un vector denso: all-MiniLM-L6-v2 y paraphrase-multilingual-MiniLM-L12-v2. Cada vector tiene 384 dimensiones. El modelo se limita a producir la representación; el producto punto, las normas y el coseno se calculan explícitamente en el código mediante un ciclo sobre las dimensiones.")
    add_paragraph(document, "Después de descargar los modelos una primera vez, el programa prioriza la copia local para evitar depender de Internet cada vez que se ejecuta una comparación.")
    add_paragraph(document, "Un embedding no es una lista de palabras del abstract. Es una lista de 384 números que resume patrones aprendidos durante el entrenamiento del modelo. Dos textos pueden usar palabras diferentes y quedar cerca en ese espacio si expresan una idea relacionada. El código no delega el cálculo final a una función externa: recorre las 384 posiciones, acumula el producto punto y las sumas de cuadrados, calcula las dos raíces y aplica la fórmula del coseno. Lo que sí se usa del modelo preentrenado es la conversión del texto a los 384 números, como autoriza el enunciado.")
    add_code(document, "dot_product = 0.0\nlength_a = 0.0\nlength_b = 0.0\nfor value_a, value_b in zip(vector_a, vector_b):\n    dot_product += value_a * value_b\n    length_a += value_a * value_a\n    length_b += value_b * value_b\nreturn dot_product / (sqrt(length_a) * sqrt(length_b))", "Fragmento 5. Similitud coseno de embeddings recorrida dimensión por dimensión.")
    add_paragraph(document, "El modelo no devuelve directamente un porcentaje de similitud. Devuelve dos vectores de 384 posiciones. El Fragmento 5 toma esos vectores y aplica exactamente la misma idea geométrica usada con TF-IDF: producto punto dividido entre las magnitudes. La diferencia está en qué significa cada posición: en TF-IDF una posición corresponde a una palabra del vocabulario; en el embedding una posición es una característica numérica aprendida y no tiene una traducción individual simple. Por esa razón los embeddings son potentes para significado, pero menos transparentes en el nivel de una palabra específica.")

    add_heading(document, "3.1.4 Detalle matemático y algorítmico de cada método", 3)
    add_table(document, ["Método", "Estructura usada", "Complejidad principal"], [
        ["Levenshtein", "Matriz de programación dinámica de m por n", "O(mn)"],
        ["Needleman-Wunsch", "Matriz de programación dinámica de m por n", "O(mn)"],
        ["Jaccard", "Dos conjuntos de términos", "O(m+n) esperado"],
        ["TF-IDF y coseno", "Diccionarios dispersos y vocabulario", "O(V) por comparación"],
        ["Embeddings y coseno", "Dos vectores densos de dimensión d", "O(d)"],
    ], [4.0, 7.5, 4.5])
    add_paragraph(document, "En Levenshtein y Needleman-Wunsch, m y n son las cantidades de tokens de los dos abstracts. En TF-IDF, V representa los términos con peso; en embeddings, d representa la dimensión del vector. El uso de matrices y ciclos permite examinar las decisiones internas en cada algoritmo.")
    add_paragraph(document, "La complejidad no es únicamente una etiqueta teórica. Si se duplicara el tamaño de los dos textos, los métodos con matriz pueden requerir aproximadamente cuatro veces más celdas, porque dependen de m × n. En cambio, el coseno de embeddings siempre recorre 384 posiciones por par con estos modelos. Esta diferencia explica por qué los métodos clásicos de alineamiento son muy ilustrativos para sustentar, pero pueden ser más costosos para documentos mucho más extensos.")

    add_heading(document, "3.1.5 Caso de estudio y resultados comparativos", 3)
    add_table(document, ["Método", "Similitud", "Tipo"], result_rows(case), [6.5, 4.0, 3.5])
    add_figure(document, "comparacion_similitudes.png", f"Figura 3. Similitudes obtenidas en el caso de estudio {article_a} y {article_b}.", 6.2)
    add_paragraph(document, f"Lectura de la tabla: todos los valores están en el intervalo de 0 a 1; 0 significa que el método no encontró semejanza según su propia representación y 1 equivaldría a coincidencia máxima. Levenshtein ({levenshtein['score']:.6f}) y Needleman-Wunsch ({needleman['score']:.6f}) son bajos porque comparan secuencias. Jaccard ({jaccard['score']:.6f}) sube ligeramente al olvidar el orden. TF-IDF ({tfidf['score']:.6f}) es el mayor de los clásicos porque distingue la relevancia de los términos compartidos. Los dos embeddings dan {embedding_one:.6f} y {embedding_two:.6f}; ambos reconocen una cercanía semántica que no aparece por completo en las coincidencias literales.")
    add_paragraph(document, f"Los resultados no se deben comparar como si fueran notas de un mismo examen. Cada número nace de una representación distinta. La conclusión defendible es que {article_a} y {article_b} son poco parecidos en la forma de escribir, pero considerablemente cercanos en significado. Esto no significa que un método sea siempre superior: los clásicos son transparentes y útiles para explicar coincidencia textual; los embeddings son útiles cuando interesa la cercanía de significado.")
    add_table(document, ["Hallazgo", "Evidencia numérica", "Interpretación correcta"], [
        ["Forma literal diferente", f"Levenshtein = {levenshtein['score']:.6f}; Needleman-Wunsch = {needleman['score']:.6f}", "Los tokens no siguen una redacción ni un orden parecido."],
        ["Vocabulario compartido limitado", f"Jaccard = {jaccard['score']:.6f}; {len(jaccard['intersection'])} términos compartidos de {jaccard['union_size']}", "Comparten algunos términos, pero también vocabulario distinto."],
        ["Señal temática literal", f"TF-IDF coseno = {tfidf['score']:.6f}", "Los términos comunes relevantes elevan la cercanía sin convertirla en alta."],
        ["Cercanía semántica", f"MiniLM = {embedding_one:.6f}; multilingüe = {embedding_two:.6f}", "Los embeddings capturan una cercanía semántica mayor que las coincidencias literales."],
    ], [4.0, 4.5, 6.7], 8.3)
    add_paragraph(document, f"Esta tabla es la respuesta sintética al caso de estudio. No se afirma que {article_a} y {article_b} sean copias ni que hablen exactamente de lo mismo. Se afirma algo más preciso: las representaciones semánticas los acercan más que las representaciones basadas exclusivamente en vocabulario exacto. La interpretación siempre debe leerse junto con los títulos y el contenido de ambos abstracts.")

    add_heading(document, "3.2 Requerimiento 2 Agrupamiento jerárquico", 2)
    add_paragraph(document, "Para agrupar los 20 abstracts se construye un vector TF-IDF por artículo. A partir de estos vectores se genera una matriz simétrica de distancia. El proceso comienza con 20 clusters individuales y, en cada iteración, fusiona el par de clusters más cercano según el criterio de linkage seleccionado. Cada método realiza 19 fusiones hasta formar un único árbol.")
    add_formula(document, "distance.png", "Ecuación 6. Distancia usada entre abstracts a partir del coseno TF-IDF.")
    add_paragraph(document, "El clustering jerárquico no recibe etiquetas temáticas creadas por una persona. Su entrada es solamente la matriz de distancias. Antes de la primera fusión hay 20 grupos: {A1}, {A2}, …, {A20}. En la primera vuelta se inspeccionan todos los pares posibles y se unen los dos que tengan menor distancia bajo el criterio seleccionado. Tras la fusión quedan 19 grupos; el proceso continúa hasta que existe un solo grupo. La lista de las 19 fusiones, con distancia y tamaño, es la materia prima del dendrograma.")

    add_heading(document, "3.2.1 Matriz de distancia y representación de abstracts", 3)
    add_paragraph(document, f"El vocabulario TF-IDF del corpus contiene {clustering['vector_terms']} términos. La distancia vale cero cuando dos vectores son idénticos y se incrementa cuando su similitud coseno disminuye. La misma matriz de distancias se entregó a los tres algoritmos, por lo que la comparación entre linkages es justa.")
    add_paragraph(document, "La matriz tiene 20 filas y 20 columnas. La posición (i, j) guarda qué tan lejos está el abstract i del abstract j. Es simétrica: la distancia de A1 a A2 es exactamente la misma que de A2 a A1; su diagonal es cero porque un documento no está lejos de sí mismo. No se agrupa directamente por títulos ni por una decisión manual del estudiante: las 190 comparaciones entre pares se derivan de los vectores TF-IDF.")
    add_paragraph(document, "La transformación distancia = 1 − coseno conserva el sentido intuitivo para clustering: valores pequeños indican abstracts cercanos y valores altos indican abstracts más distintos. Por ejemplo, un coseno de 1 genera distancia 0; un coseno de 0 genera distancia 1. La matriz completa se calcula una vez y se reutiliza sin cambios en Single, Complete y Average. De esta forma, si los dendrogramas difieren, la causa es el criterio de enlace y no una diferencia en los datos de entrada.")

    add_heading(document, "3.2.2 Detalle matemático y algorítmico de cada método", 3)
    add_paragraph(document, "Single Linkage toma la menor distancia entre un elemento de un cluster y un elemento del otro. Puede formar cadenas de documentos conectados por similitudes locales.")
    add_formula(document, "single.png", "Ecuación 7. Distancia entre clusters para Single Linkage.")
    add_paragraph(document, "Complete Linkage toma la mayor distancia. Por ello exige que todos los elementos de los grupos fusionados se mantengan relativamente cercanos y suele producir clusters más compactos.")
    add_formula(document, "complete.png", "Ecuación 8. Distancia entre clusters para Complete Linkage.")
    add_paragraph(document, "Average Linkage calcula el promedio de todas las distancias cruzadas. Representa un equilibrio entre la sensibilidad de Single y la exigencia de Complete.")
    add_formula(document, "average.png", "Ecuación 9. Distancia entre clusters para Average Linkage.")
    add_paragraph(document, "La implementación conserva una lista de clusters activos. Para cada par activo calcula la distancia con ciclos anidados, localiza el menor valor, fusiona las listas de índices y guarda la historia de la fusión. La visualización usa esa historia; no se emplea una biblioteca de clustering para construir el árbol.")
    add_code(document, "values = []\nfor left in first:\n    for right in second:\n        values.append(distances[left][right])\n\nif method == 'single':\n    return min(values)\nif method == 'complete':\n    return max(values)\nreturn sum(values) / len(values)", "Fragmento 6. Distancia entre dos clusters recorrida explícitamente para los tres linkages.")
    add_paragraph(document, "El Fragmento 6 muestra la parte que diferencia los tres algoritmos. Cuando cada cluster tiene un solo abstract, values contiene una distancia. Después de una fusión puede contener varias: si un cluster tiene dos artículos y otro tres, se recorren 2 × 3 = 6 distancias. Single escoge la menor, Complete la mayor y Average calcula su promedio. Esta es la razón matemática de que los tres árboles puedan cambiar después de las primeras uniones.")
    add_table(document, ["Criterio", "Pregunta que responde antes de fusionar A y B", "Efecto esperado"], [
        ["Single", "¿Existe al menos un par muy cercano entre A y B?", "Puede unir grupos extensos mediante una cadena de vecinos."],
        ["Complete", "¿Cuál es el par más lejano si uno A y B?", "Retrasa fusiones cuando hay un elemento distante; forma grupos compactos."],
        ["Average", "¿Cuál es la distancia promedio entre todos los pares cruzados?", "Evita que un solo par cercano o lejano domine la decisión."],
    ], [3.0, 7.0, 5.0], 8.3)
    add_paragraph(document, "Los tres métodos comienzan exactamente igual, con 20 clusters de un elemento. Su diferencia aparece al calcular la distancia después de la primera fusión. Por eso los dendrogramas pueden tener primeras fusiones similares y, aun así, terminar con estructuras distintas.")
    add_code(document, "while len(active) > 1:\n    # se busca el par activo con menor distancia\n    for left_position in range(len(active)):\n        for right_position in range(left_position + 1, len(active)):\n            distance = _cluster_distance(...)\n            if distance < best_distance:\n                best_left, best_right = left, right\n    merged = clusters[best_left] + clusters[best_right]\n    history.append(MergeStep(...))", "Fragmento 7. Esquema del ciclo de fusión aglomerativa implementado en el proyecto.")
    add_paragraph(document, "La variable active contiene únicamente los identificadores de grupos que aún se pueden fusionar. Cuando se encuentra la mejor pareja, sus listas de índices se concatenan en merged; los dos identificadores antiguos se retiran de active y se agrega un identificador nuevo. history conserva la evidencia de esa decisión: grupos izquierdo y derecho, distancia, tamaño del nuevo grupo. Por tanto, el dendrograma puede reconstruirse y explicarse paso por paso.")

    add_heading(document, "3.2.3 Dendrogramas y formación de grupos", 3)
    add_figure(document, "dendrograma_single.png", "Figura 4. Dendrograma generado por Single Linkage.", 6.2)
    add_paragraph(document, "Cómo leer un dendrograma: cada etiqueta A1 a A20 es un abstract. Las ramas se unen de abajo hacia arriba; la altura de una unión es la distancia a la que el algoritmo decidió fusionar los grupos. Una unión baja representa mayor cercanía relativa que una unión alta. El lector puede imaginar una línea horizontal: todo lo que quede conectado debajo de esa línea forma un cluster. No se debe interpretar la posición horizontal como distancia, pues se usa principalmente para separar visualmente las hojas.")
    add_paragraph(document, f"En Single Linkage se aprecia el efecto de encadenamiento: una sucesión de cercanías locales puede incorporar abstracts progresivamente a un grupo grande. Al cortar el árbol en tres grupos, el resultado verificable es: {single_clusters}. No significa que un grupo grande contenga documentos idénticos; indica que, con el criterio del vecino más cercano, existe una ruta de similitudes locales que los conecta. Este es el comportamiento característico de Single.")
    add_figure(document, "dendrograma_complete.png", "Figura 5. Dendrograma generado por Complete Linkage.", 6.2)
    add_paragraph(document, f"En Complete Linkage las uniones finales aparecen a alturas más altas porque el método vigila el par más lejano entre dos grupos. Con tres grupos, el corte verificable es: {complete_clusters}. Este criterio conserva separado un subconjunto hasta que sus elementos pueden integrarse sin introducir una distancia máxima demasiado alta. Es una separación más estricta, no necesariamente una separación mejor.")
    add_figure(document, "dendrograma_average.png", "Figura 6. Dendrograma generado por Average Linkage.", 6.2)
    add_paragraph(document, f"Average Linkage ofrece una lectura intermedia. A tres grupos, el corte verificable es: {average_clusters}. Sin embargo, las alturas de algunas fusiones no son las mismas que en los otros métodos: aquí se decide con el promedio de todas las distancias cruzadas, de modo que una pareja excepcionalmente cercana no puede arrastrar por sí sola todo el grupo. Su dendrograma es útil cuando se desea una decisión menos extrema que las de Single y Complete.")
    add_paragraph(document, "Los tres gráficos no son tres maneras de dibujar el mismo resultado: representan tres definiciones matemáticas diferentes de distancia entre grupos. Por eso deben explicarse junto con el criterio de enlace y con Silhouette. En este corpus, los grupos no quedan fuertemente separados; los dendrogramas sirven para observar el proceso de unión y proponer cortes, no para afirmar categorías temáticas absolutas sin revisar los abstracts que contiene cada grupo.")
    add_table(document, ["Dendrograma", "Corte en 3 grupos", "Qué enseña el corte"], [
        ["Single", single_clusters, "La regla del vecino más cercano puede encadenar gran parte del corpus."],
        ["Complete", complete_clusters, "La regla del par más lejano favorece grupos compactos."],
        ["Average", average_clusters, "El promedio equilibra las distancias cruzadas."],
    ], [3.0, 5.5, 6.7], 8.3)
    add_paragraph(document, "La tabla anterior no asigna nombres temáticos inventados a los grupos. Solo reporta el resultado verificable de cortar cada árbol en tres partes. Para poner un nombre temático a un grupo se debería abrir sus abstracts, revisar sus términos de mayor peso y justificar esa etiqueta. El proyecto evita esa sobreinterpretación: distingue entre un grupo matemático obtenido por distancia y una categoría académica que requeriría análisis cualitativo adicional.")

    add_heading(document, "3.2.4 Evaluación interna con Silhouette", 3)
    add_paragraph(document, "Para evaluar los grupos se usa el coeficiente Silhouette. Para cada artículo, a(i) es la distancia media a su propio cluster y b(i) es la menor distancia media a otro cluster. El resultado individual varía entre -1 y 1; un valor mayor indica una mejor separación relativa.")
    add_formula(document, "silhouette.png", "Ecuación 10. Coeficiente Silhouette por artículo.")
    add_figure(document, "silhouette.png", "Figura 7. Coeficiente Silhouette promedio para tres grupos.", 5.4)
    add_table(document, ["Método de enlace", "Silhouette promedio", "Lectura"], [
        ["Single Linkage", f"{single_score:.6f}", "Separación débil; el valor se interpreta junto con su dendrograma."],
        ["Complete Linkage", f"{complete_score:.6f}", "Separación débil; conserva grupos más compactos."],
        ["Average Linkage", f"{average_score:.6f}", "Separación débil; promedia todas las distancias cruzadas."],
    ], [4.2, 4.0, 7.0], 8.5)
    add_paragraph(document, f"Cómo leer la figura y la tabla implícita: Silhouette se acerca a 1 cuando un documento está mucho más cerca de su propio grupo que de los demás; cerca de 0 indica que está en una zona de frontera; valores negativos sugieren una posible asignación inadecuada. En esta ejecución, Single obtuvo {single_score:.6f}, Complete {complete_score:.6f} y Average {average_score:.6f}. Los tres valores están cerca de cero.")
    add_paragraph(document, "La puntuación baja no es un error de cálculo ni una razón para ocultar los dendrogramas. Es evidencia de que, al pedir tres grupos, los abstracts no quedan naturalmente separados con fuerza. Todos se relacionan con inteligencia artificial y educación, por lo que comparten vocabulario. Para una sustentación, la conclusión correcta es: el clustering revela cercanías y posibles subconjuntos, pero el corpus es homogéneo y no respalda una segmentación temática tajante en tres grupos.")
    add_code(document, "intra = promedio_de_distancias_al_propio_cluster\nnearest = menor_promedio_hacia_otro_cluster\nscale = max(intra, nearest)\nsilhouette = 0.0 if scale == 0 else (nearest - intra) / scale", "Fragmento 8. Cálculo de la silueta individual; el programa repite este proceso para los 20 abstracts y promedia.")
    add_paragraph(document, "Para un abstract bien ubicado se espera intra pequeño y nearest grande; entonces la resta es positiva y la silueta se acerca a 1. Si las dos distancias son similares, la resta se aproxima a 0: el abstract está cerca de una frontera entre grupos. Este último caso domina en el corpus. Además, los grupos individuales reciben silueta 0 en la implementación, porque no existe otro elemento de su propio grupo con el cual calcular la distancia intra. Esto ayuda a entender por qué los cortes de Single y Average, que dejan dos elementos solos, no obtienen una silueta alta.")

    add_heading(document, "3.3 Análisis de desempeño de ordenamientos no comparativos", 2)
    add_paragraph(document, "Además de los requisitos de similitud y agrupamiento, se analiza el ranking de términos del corpus mediante Counting Sort, Radix Sort y una variante de Bucket Sort por frecuencia discreta. Los tres reciben exactamente la misma lista de pares (término, frecuencia), formada únicamente con los abstracts ya auditados. En esta ejecución la entrada contiene n = " + str(ranking_data["unique_terms"]) + " términos únicos, " + str(ranking_data["total_tokens"]) + " tokens procesados y una frecuencia máxima k = " + str(max(item["frequency"] for item in counting_metrics["full_ranking"])) + ".")
    add_heading(document, "3.3.1 Por qué estos algoritmos pueden evitar la cota de comparación", 3)
    add_paragraph(document, "La cota Ω(n log n) no es una ley para todo algoritmo de ordenamiento: aplica a los algoritmos que obtienen información exclusivamente al comparar dos claves, por ejemplo al preguntar si un elemento es mayor que otro. En ese modelo existen n! órdenes posibles para n elementos. Un árbol de decisiones binario con altura h distingue como máximo 2^h resultados; por tanto, para distinguir n! permutaciones debe cumplirse 2^h ≥ n!, es decir, h ≥ log₂(n!). Por la aproximación de Stirling, log₂(n!) pertenece a Ω(n log n).")
    add_paragraph(document, "Counting Sort, Radix Sort y la variante por cubetas no construyen ese árbol de comparaciones. Counting usa la frecuencia como índice directo de un arreglo; Radix extrae un dígito decimal y usa ese dígito como índice entre 0 y 9; y Bucket por frecuencia usa la frecuencia como índice de una lista-cubeta. Por eso la barrera anterior no les aplica. Esto no significa que sean lineales en cualquier caso: sus costos dependen del rango k, de la base b y del número de dígitos d. Son convenientes cuando esos parámetros son acotados o pequeños frente a n, como sucede con las frecuencias de este corpus.")
    add_table(document, ["Algoritmo", "Operación dominante", "Tiempo", "Espacio", "Condición para comportamiento lineal"], [
        ["Counting Sort", "Contar n elementos y recorrer las k + 1 frecuencias.", "O(n + k)", "O(n + k)", "k debe ser razonable respecto de n."],
        ["Radix Sort", "Aplicar una pasada estable por cada dígito; base b = 10.", "O(d(n + b))", "O(n + b)", "b y d deben permanecer acotados."],
        ["Bucket por frecuencia", "Distribuir n pares y concatenar k + 1 cubetas.", "O(n + k)", "O(n + k)", "Las claves son enteras y el rango 0..k es manejable."],
    ], [2.8, 4.5, 2.4, 2.4, 5.0], 7.8)
    add_heading(document, "3.3.2 Implementación y análisis de cada algoritmo", 3)
    add_paragraph(document, "Counting Sort identifica primero la mayor frecuencia k. Luego crea counts[0..k], incrementa counts[f] por cada término con frecuencia f y calcula la posición inicial de cada grupo recorriendo f desde k hasta 0. Finalmente ubica cada par en la salida. La fase de conteo visita n elementos; el cálculo de posiciones visita k + 1 índices; y la salida visita de nuevo n elementos. De allí se obtiene T(n, k) = cn + c₁(k + 1) + c₂n, que se resume en O(n + k). Al avanzar la posición de cada grupo después de insertar, conserva el orden de primera aparición cuando hay empates.")
    add_paragraph(document, "Radix Sort trabaja desde el dígito menos significativo. Para cada divisor 1, 10, 100, ... realiza un Counting Sort estable sobre el dígito correspondiente de la frecuencia. En cada pasada cuenta n elementos, recorre los 10 dígitos posibles y escribe n elementos; por tanto una pasada cuesta O(n + 10). Tras d pasadas el costo es O(d(n + 10)). El recorrido 9, 8, ..., 0 de las posiciones produce el orden descendente directamente; no se invierte la lista al final. La estabilidad es indispensable: conserva la información del dígito menos significativo mientras se ordenan los dígitos siguientes.")
    add_paragraph(document, "La implementación llamada Bucket Sort debe describirse con precisión. Es una variante de cubetas por frecuencia discreta, también interpretable como direccionamiento directo con listas: crea k + 1 cubetas y coloca cada par (término, frecuencia) en buckets[frecuencia]. No necesita ordenar dentro de una cubeta porque todos sus elementos tienen la misma clave de ordenamiento: la frecuencia. Después concatena buckets[k], buckets[k−1], ..., buckets[0]. Distribuir los pares cuesta O(n); recorrer las k + 1 cubetas y copiar sus contenidos cuesta O(k + n); en conjunto T(n, k) = O(n + k). Se parece a Counting Sort porque ambos direccionan por frecuencia, pero aquí cada casillero conserva explícitamente la lista de términos empatados, en vez de guardar solo un conteo y posiciones de salida.")
    add_code(document, "# Radix: las posiciones de 9 a 0 producen descenso sin invertir.\nfor digit in range(9, -1, -1):\n    positions[digit] = next_position\n    next_position += counts[digit]\n\n# Bucket por frecuencia: no ordena dentro de una cubeta.\nfor item in items:\n    buckets[item[1]].append(item)\nfor frequency in range(maximum, -1, -1):\n    ordered.extend(buckets[frequency])", "Fragmento 9. Núcleo explícito del orden descendente de Radix y de las cubetas por frecuencia.")
    add_heading(document, "3.3.3 Medición empírica e interpretación", 3)
    add_paragraph(document, f"Cada algoritmo se ejecutó {ranking_data['repetitions']} veces sobre la misma lista de {ranking_data['unique_terms']} pares. Se usó perf_counter_ns y se guardaron promedio, mínimo y máximo en milisegundos. Los tiempos dependen de este computador, Python y el tamaño de la entrada; por eso sirven como evidencia experimental, no como sustituto de la complejidad asintótica.")
    add_table(document, ["Algoritmo", "Promedio ms", "Mínimo ms", "Máximo ms", "Lectura de la implementación"], [
        ["Counting Sort", f"{counting_metrics['average_execution_ms']:.6f}", f"{counting_metrics['minimum_execution_ms']:.6f}", f"{counting_metrics['maximum_execution_ms']:.6f}", "Cuenta, calcula posiciones y llena una salida."],
        ["Radix Sort", f"{radix_metrics['average_execution_ms']:.6f}", f"{radix_metrics['minimum_execution_ms']:.6f}", f"{radix_metrics['maximum_execution_ms']:.6f}", "Repite la pasada estable por cada dígito de la frecuencia."],
        ["Bucket por frecuencia", f"{bucket_metrics['average_execution_ms']:.6f}", f"{bucket_metrics['minimum_execution_ms']:.6f}", f"{bucket_metrics['maximum_execution_ms']:.6f}", "Distribuye en listas y concatena, sin salida indexada."],
    ], [3.0, 2.7, 2.7, 2.7, 6.0], 8.0)
    radix_vs_counting = radix_metrics['average_execution_ms'] / counting_metrics['average_execution_ms'] if counting_metrics['average_execution_ms'] else 0.0
    add_paragraph(document, f"Bucket por frecuencia fue el menor promedio en esta ejecución y Radix tardó {radix_vs_counting:.2f} veces el promedio de Counting Sort. La explicación está en los recorridos reales, no en una afirmación vaga de que la diferencia es normal. Counting realiza un ciclo de conteo, un ciclo sobre el rango y una escritura de salida. Bucket distribuye cada par a una lista y luego concatena las listas; para este k pequeño evita el arreglo de posiciones y la escritura indexada. Radix, en cambio, repite conteo, posiciones y salida por cada dígito. Como la frecuencia máxima tiene dos dígitos, ejecuta dos pasadas completas. Aunque los tres tienen comportamiento lineal bajo sus supuestos, sus constantes de trabajo son diferentes y se notan en una entrada de 1.050 elementos.")
    add_heading(document, "3.3.4 Validación verificable del ranking", 3)
    add_paragraph(document, "La validación no compara solamente los 15 primeros elementos. El programa primero verifica mediante un recorrido que ninguna frecuencia aumente; después compara el ranking completo de Radix y Bucket contra el ranking completo de Counting Sort. La tabla presenta los 15 primeros puestos para que el profesor pueda comprobar visualmente término por término. Los empates mantienen el orden de primera aparición en el corpus.")
    top_rows = []
    for position in range(15):
        row = [str(position + 1)]
        for method_name in ("counting_sort", "radix_sort", "bucket_sort"):
            item = ranking_methods[method_name]["top_terms"][position]
            row.append(f"{item['term']} ({item['frequency']})")
        top_rows.append(row)
    add_table(document, ["Puesto", "Counting Sort", "Radix Sort", "Bucket por frecuencia"], top_rows, [1.4, 4.8, 4.8, 4.8], 8.0)
    add_paragraph(document, "Resultado de la validación: los tres rankings completos coinciden exactamente y son descendentes. Esta igualdad no depende de ordenar después con una función de biblioteca: procede de las tres implementaciones explícitas y de la comparación programada entre sus salidas.")

    add_heading(document, "3.4 Requerimiento 6 Despliegue y soporte técnico", 2)
    add_paragraph(document, "La aplicación se ejecuta localmente mediante el archivo iniciar_app.bat. El menú permite preparar el corpus, seleccionar abstracts, calcular similitudes, construir los dendrogramas y consultar el ranking. Las dependencias se registran en requirements.txt y el código se entrega mediante un repositorio público de GitHub. Los PDF originales no se publican por permisos; el proyecto conserva los abstracts procesados para revisar los resultados.")
    add_table(document, ["Paso", "Acción"], [
        ["1", "Crear el entorno virtual e instalar requirements.txt."],
        ["2", "Ubicar los PDF autorizados en data/pdfs si se desea repetir la extracción."],
        ["3", "Ejecutar iniciar_app.bat."],
        ["4", "Usar la interfaz o ejecutar las pruebas con unittest."],
    ], [2.0, 14.0])
    add_paragraph(document, "La reproducibilidad no depende de copiar números manualmente al informe. El archivo de preparación vuelve a leer los PDF autorizados, genera abstracts.json y ejecuta la auditoría; los módulos de requerimientos consumen ese mismo archivo procesado. La evidencia del caso de estudio, los dendrogramas y las tablas se generan desde los resultados serializados. Si cambia un PDF, se debe repetir la preparación del corpus, revisar la auditoría y regenerar los resultados antes de defender cifras nuevas.")
    add_paragraph(document, "Para una sustentación, el orden recomendado es: primero mostrar que los 20 abstracts pasan la auditoría; después seleccionar dos artículos en la interfaz y explicar las cuatro similitudes clásicas y los embeddings; por último generar los tres dendrogramas con exactamente la misma matriz de distancias. De esta forma el profesor puede seguir el recorrido desde la fuente hasta cada resultado, sin asumir que una librería decidió el algoritmo por el estudiante.")

    add_heading(document, "4 Resultados y análisis crítico")
    add_paragraph(document, f"La comparación del caso de estudio evidencia dos comportamientos. Los métodos basados en coincidencia literal de tokens reportaron valores entre {levenshtein['score']:.6f} y {tfidf['score']:.6f}. En contraste, los embeddings reportaron {embedding_one:.6f} para MiniLM y {embedding_two:.6f} para el modelo multilingüe. El contraste es coherente con el propósito de los enfoques: TF-IDF y Jaccard dependen de términos compartidos, mientras que los embeddings capturan asociaciones semánticas aprendidas en el preentrenamiento.")
    add_paragraph(document, "Esta diferencia enseña una idea central del proyecto: el resultado de un algoritmo depende de qué información decide conservar. Si el objetivo fuera detectar plagio o una reformulación casi literal, las coincidencias token por token serían muy valiosas. Si el objetivo es encontrar artículos que hablen de un mismo problema con estilos de redacción distintos, los embeddings aportan una señal más apropiada. Por eso la interfaz presenta todos los métodos juntos y no reemplaza los clásicos por IA.")
    add_paragraph(document, "En clustering no se observó una separación fuerte entre tres grupos. Esto es esperable en un corpus homogéneo, compuesto casi por completo por revisiones y estudios sobre inteligencia artificial en educación. La métrica no se oculta: el informe reporta los tres valores y explica la limitación. Esta lectura crítica es preferible a afirmar que un dendrograma es mejor sin evidencia matemática.")
    add_paragraph(document, "Una limitación adicional es que el agrupamiento usa únicamente el abstract y la representación TF-IDF. El título, los autores, el año y las palabras clave no intervienen en la distancia. Esta decisión mantiene el experimento controlado: cada método recibe los mismos datos textuales. En un trabajo posterior se podría contrastar este resultado con embeddings para clustering o probar distintas cantidades de grupos, pero esas variantes deben reportarse como nuevos experimentos y no mezclarse con los resultados de este documento.")

    add_heading(document, "5 Validación y pruebas")
    add_paragraph(document, "El proyecto cuenta con 26 pruebas automatizadas aprobadas. Las pruebas verifican extracción de abstracts, auditoría de calidad del corpus, conteo de términos, ordenamientos, medición de promedio-mínimo-máximo, similitud clásica, coseno de vectores densos, selección dinámica de varios artículos, fusiones jerárquicas y Silhouette. Además, se validó una ejecución real sobre el corpus: cada método jerárquico generó 19 fusiones para los 20 abstracts.")
    add_table(document, ["Componente", "Validación aplicada"], [
        ["Extractor", "Marcadores de abstract, palabras clave, introducción y casos sin abstract."],
        ["Ordenamientos", "Mismo ranking, orden descendente y métricas de tiempo coherentes."],
        ["Similitud clásica", "Matrices pequeñas, Jaccard, TF-IDF y coseno conocido."],
        ["Embeddings", "Coseno manual de vectores densos."],
        ["Clustering", "Primer par más cercano, cantidad de fusiones y corte en tres grupos."],
        ["Evaluación", "Silueta alta en un ejemplo de dos grupos bien separados."],
        ["Interfaz", "Pantallas de similitud y clustering ejecutadas sin excepciones."],
    ], [4.2, 11.8])

    add_heading(document, "6 Declaración de uso de inteligencia artificial generativa")
    add_paragraph(document, "Para cumplir el principio de transparencia académica, se declara de manera explícita el uso de herramientas de inteligencia artificial durante el proyecto. La IA se utilizó como apoyo para revisar, explicar y documentar; no reemplazó la responsabilidad del estudiante sobre el diseño, la lectura del código, la ejecución de las pruebas ni la interpretación de los resultados. Toda cifra del informe se obtiene al ejecutar el programa sobre los archivos procesados, no de una respuesta generada por IA.")
    add_heading(document, "6.1 Herramientas utilizadas y alcance", 2)
    add_table(document, ["Herramienta", "Uso concreto", "Límite aplicado"], [
        ["ChatGPT Codex", "Apoyo para revisar la estructura del proyecto, proponer casos de prueba, identificar riesgos de extracción de PDF y mejorar la redacción técnica del informe.", "Las propuestas se revisaron, se adaptaron al código y se comprobaron mediante ejecución y pruebas automatizadas."],
        ["Sentence Transformers", "Generación de representaciones numéricas preentrenadas con all-MiniLM-L6-v2 y paraphrase-multilingual-MiniLM-L12-v2.", "Solo genera los vectores densos permitidos por el enunciado. El coseno se calcula explícitamente con un ciclo propio; no se delega la comparación final."],
    ], [3.7, 7.3, 5.0], 8.3)
    add_heading(document, "6.2 Consultas representativas realizadas", 2)
    add_paragraph(document, "A continuación se presentan consultas representativas del uso real de la herramienta. Se incluyen para mostrar el tipo de apoyo solicitado, sin convertir la declaración en una transcripción completa de conversaciones de trabajo.")
    add_code(document, "Revisa el documento del proyecto de Análisis de Algoritmos y verifica que las implementaciones usen listas, diccionarios, matrices y ciclos explícitos, sin delegar los algoritmos académicos a bibliotecas de alto nivel.", "Prompt representativo 1. Revisión de transparencia algorítmica.")
    add_code(document, "Explica la recurrencia de Levenshtein y el cálculo manual de similitud coseno para documentarlos en un proyecto académico. La explicación debe permitir sustentar cada paso del código.", "Prompt representativo 2. Apoyo para explicación matemática y sustentación.")
    add_code(document, "Propón casos de prueba para comprobar que el extractor no corte un abstract por una línea vacía, no mezcle Keywords con el contenido y repare palabras partidas por la extracción de PDF.", "Prompt representativo 3. Diseño de pruebas para calidad del corpus.")
    add_heading(document, "6.3 Verificación y trabajo realizado por el estudiante", 2)
    add_paragraph(document, "Las sugerencias obtenidas se trataron como hipótesis de trabajo, no como resultados finales. El estudiante inspeccionó los módulos, decidió qué cambios tenían sentido para el enunciado y comprobó su funcionamiento. En particular, revisó que Levenshtein y Needleman-Wunsch construyen matrices propias; que Jaccard usa conjuntos; que TF-IDF cuenta frecuencias e IDF con diccionarios; que el coseno recorre sus vectores; y que Single, Complete y Average Linkage calculan las fusiones con ciclos explícitos.")
    add_paragraph(document, "La verificación incluyó las 26 pruebas automatizadas, una auditoría de los 20 abstracts y ejecuciones reales sobre el corpus. Cuando se corrigió la extracción, no se conservaron las cifras antiguas: se regeneraron abstracts, evidencia, ranking, dendrogramas y tablas. Este procedimiento es el respaldo de que los resultados mostrados son reproducibles y atribuibles al programa entregado.")
    add_heading(document, "6.4 Usos que no se realizaron", 2)
    add_paragraph(document, "No se pidió a una IA que resolviera directamente los algoritmos requeridos mediante una caja negra, que clasificara manualmente los artículos, que inventara resultados experimentales ni que sustituyera el análisis crítico de las métricas. Tampoco se usaron Scikit-learn, SciPy, difflib ni herramientas equivalentes para ejecutar Levenshtein, clustering jerárquico, Silhouette o el coseno solicitado. Las únicas representaciones externas permitidas son los embeddings preentrenados, claramente diferenciados de los algoritmos implementados por el estudiante.")

    add_heading(document, "7 Conclusiones")
    add_paragraph(document, "El proyecto demuestra que es posible analizar un corpus documental combinando algoritmos clásicos transparentes y representaciones modernas basadas en embeddings. La comparación evidencia que las medidas basadas en tokens responden a coincidencias observables de palabras y orden, mientras los embeddings pueden mostrar cercanía semántica cuando dos textos utilizan redacciones distintas. Esa diferencia no convierte automáticamente a un enfoque en mejor: cada uno conserva información distinta y debe elegirse de acuerdo con la pregunta de análisis.")
    add_paragraph(document, "La calidad de la entrada condiciona cualquier resultado posterior. Por ello, la extracción no se trató como un paso invisible: el proyecto repara cortes de palabras, distingue encabezados editoriales de menciones normales dentro del texto, filtra palabras clave y audita cada abstract antes de usarlo. Con los 20 registros validados, las similitudes, el ranking complementario y los dendrogramas se apoyan en el mismo corpus controlado.")
    add_paragraph(document, "El análisis de ordenamientos confirma que la eficiencia no se resume en una etiqueta Big O. Counting Sort y la variante de cubetas por frecuencia tienen costo O(n + k), mientras Radix Sort tiene O(d(n + b)); evitan la cota de los algoritmos por comparación al usar direccionamiento directo, no comparaciones entre pares de términos. La medición experimental muestra que las constantes y el número de pasadas importan: Radix recorre la entrada por cada dígito, mientras la variante de cubetas agrupa y concatena directamente. La tabla de top 15 y la comparación del ranking completo validan que las tres salidas son iguales.")
    add_paragraph(document, "Los tres criterios jerárquicos se implementaron desde cero y se evaluaron con la misma matriz de distancia. Los valores de Silhouette cercanos a cero no se ocultan ni se presentan como un éxito artificial: indican que el corpus es relativamente homogéneo bajo el corte de tres grupos. Los dendrogramas son útiles para observar cómo cambian las fusiones con cada criterio, pero no autorizan por sí solos a imponer etiquetas temáticas definitivas a los artículos.")
    add_paragraph(document, "Finalmente, la aplicación, las pruebas, los archivos de evidencia y la declaración de uso de IA permiten reconstruir el trabajo paso a paso. El valor del proyecto no está solamente en mostrar una cifra de similitud o un gráfico, sino en poder explicar de dónde sale cada dato, qué estructura se recorrió, qué supuesto se aplicó y qué limitación conserva el resultado.")

    add_heading(document, "Referencias")
    add_paragraph(document, "Universidad del Quindío. Proyecto Análisis de Algoritmos. Documento de especificación entregado por el docente.")
    add_paragraph(document, "Manning, C. D., Raghavan, P., y Schütze, H. Introduction to Information Retrieval. Cambridge University Press.")
    add_paragraph(document, "Kaufman, L., y Rousseeuw, P. J. Finding Groups in Data. Wiley.")

    document.add_page_break()
    add_heading(document, "Anexos")
    add_heading(document, "Anexo A Ranking de términos", 2)
    add_paragraph(document, "La fundamentación, las mediciones y la tabla verificable del ranking se presentan en la Sección 3.3. Este anexo recuerda que los archivos JSON conservan el ranking completo de los tres métodos, no únicamente los 15 términos mostrados en el documento.")
    add_heading(document, "Anexo B Repositorio y ejecución", 2)
    add_paragraph(document, "Repositorio público: https://github.com/JoseVanegas190/analisis-algoritmos-python")
    add_paragraph(document, "Para ejecutar localmente: instalar las dependencias registradas, ubicar los PDF autorizados en data/pdfs si se requiere una nueva extracción y ejecutar iniciar_app.bat.")

    OUTPUT.parent.mkdir(exist_ok=True)
    document.save(OUTPUT)
    print(f"Documento generado: {OUTPUT}")


if __name__ == "__main__":
    main()
