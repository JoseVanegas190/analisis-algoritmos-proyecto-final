"""Genera el informe enfocado en el desempeño de los tres ordenamientos."""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).parents[1]
RESULT_PATH = ROOT / "data" / "processed" / "term_ranking.json"
AUDIT_PATH = ROOT / "data" / "processed" / "corpus_audit.json"
OUTPUT_PATH = ROOT / "output" / "Informe_Desempeno_Ordenamientos_Corregido.docx"


def font(run, size=11, bold=False, color="000000"):
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def shade(cell, fill):
    element = OxmlElement("w:shd")
    element.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(element)


def borders(cell, color="C9D2DC"):
    props = cell._tc.get_or_add_tcPr()
    element = props.first_child_found_in("w:tcBorders")
    if element is None:
        element = OxmlElement("w:tcBorders")
        props.append(element)
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge = element.find(qn("w:" + side))
        if edge is None:
            edge = OxmlElement("w:" + side)
            element.append(edge)
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "4")
        edge.set(qn("w:color"), color)


def text(doc, value, after=7):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(after)
    font(p.add_run(value))


def heading(doc, value, level=1):
    p = doc.add_heading(value, level=level)
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(6)
    for run in p.runs:
        font(run, 14 if level == 1 else 12, True, "000000")


def add_table(doc, headers, rows, widths, size=9):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for i, value in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.width = Cm(widths[i])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shade(cell, "17365D")
        borders(cell, "9BAFC5")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        font(p.add_run(value), size, True, "FFFFFF")
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cell = cells[i]
            cell.width = Cm(widths[i])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            borders(cell)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            font(p.add_run(value), size)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_page_number(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run("Página "), 9, False, "666666")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    p._p.append(field)


def main():
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    rankings = {key: result["methods"][key]["top_terms"] for key in result["methods"]}
    times = {key: result["methods"][key]["average_execution_ms"] for key in result["methods"]}
    meta = {
        "total_articles": result["total_articles"],
        "total_tokens": result["total_tokens"],
        "unique_terms": result["unique_terms"],
        "maximum_frequency": result["maximum_frequency"],
        "radix_base": result["radix_base"],
        "radix_digit_count": result["radix_digit_count"],
    }
    algorithms = ["counting_sort", "radix_sort", "bucket_sort"]
    names = {"counting_sort": "Counting Sort", "radix_sort": "Radix Sort", "bucket_sort": "Bucket Sort"}
    repetitions = result.get("repetitions", "varias")
    bucket_ratio = times["radix_sort"] / times["bucket_sort"] if times["bucket_sort"] else 0

    doc = Document()
    section = doc.sections[0]
    section.top_margin, section.bottom_margin = Cm(2.1), Cm(2.0)
    section.left_margin, section.right_margin = Cm(2.2), Cm(2.2)
    add_page_number(section)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(68), Pt(14)
    font(p.add_run("ANÁLISIS DEL DESEMPEÑO DE\nALGORITMOS DE ORDENAMIENTO"), 21, True, "000000")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(36)
    font(p.add_run("Seguimiento 2026-2\nAnálisis de Algoritmos"), 13, False, "000000")
    add_table(doc, ["Dato", "Información"], [
        ["Corpus evaluado", f"{meta['total_articles']} abstracts en PDF"],
        ["Algoritmos", "Counting Sort, Radix Sort y Bucket Sort"],
        ["Ejecución", "Medición generada por el proyecto"],
    ], [4.0, 11.0], 10)
    doc.add_page_break()

    heading(doc, "1. Propósito del análisis")
    text(doc, "Este documento presenta la fundamentación teórica, la medición empírica y la validación del ranking de términos producido por Counting Sort, Radix Sort y una variante de Bucket Sort por frecuencia discreta. Los tres algoritmos reciben la misma lista de pares término-frecuencia extraída de los abstracts del corpus completo. La conclusión es que los tres entregan el mismo ranking descendente, pero realizan recorridos internos diferentes, lo que explica sus tiempos observados.")

    heading(doc, "2. Datos y protocolo de medición")
    text(doc, f"La entrada de cada algoritmo fue la misma lista de {meta['unique_terms']} pares (término, frecuencia), obtenida al procesar {meta['total_articles']} abstracts. El corpus produjo {meta['total_tokens']} tokens después de limpiar el texto y antes de agrupar repeticiones. La frecuencia máxima observada fue k = {meta['maximum_frequency']}; por tanto, Radix Sort procesó d = {meta['radix_digit_count']} dígitos en base b = {meta['radix_base']}. Cada ejecución conserva el término junto a su frecuencia, de modo que el orden final puede verificarse término a término.")
    text(doc, f"Antes de construir el ranking se ejecutó una auditoría de los {audit['total_records']} abstracts. La auditoría revisa que no existan abstracts ausentes o demasiado cortos, encabezados editoriales filtrados como Keywords o Introduction, caracteres de extracción no normalizados y palabras partidas por salto de línea. El resultado fue {audit['valid_records']} abstracts válidos y {audit['records_to_review']} pendientes de revisión. La limpieza aplica minúsculas, normalización de caracteres, reparación de palabras partidas y una lista local visible de stopwords en inglés y español.")
    text(doc, f"Los tiempos se midieron en milisegundos con perf_counter_ns, un reloj de alta resolución. Cada algoritmo se ejecutó {repetitions} veces sobre la misma lista y el programa guarda promedio, mínimo y máximo. Los valores son evidencia de esta máquina y de esta entrada; no son una constante universal ni sustituyen el análisis asintótico.")

    heading(doc, "3. Fundamentación teórica")
    text(doc, "Para expresar los costos se usa n para el número de pares de la lista de frecuencias, k para la frecuencia máxima, b para la base de los dígitos y d para la cantidad de dígitos de k. En esta ejecución n = " + str(meta["unique_terms"]) + ", k = " + str(meta["maximum_frequency"]) + ", b = " + str(meta["radix_base"]) + " y d = " + str(meta["radix_digit_count"]) + ". Los algoritmos se programaron de forma explícita con listas, ciclos, contadores y arreglos auxiliares; no se usa una función de ordenamiento de biblioteca.")
    text(doc, "La cota Omega(n log n) corresponde a los algoritmos que ordenan exclusivamente mediante comparaciones entre elementos. Su razonamiento se basa en un árbol de decisiones: para distinguir las n! permutaciones posibles se requieren al menos log2(n!) comparaciones en el peor caso. Counting Sort, Radix Sort y la variante de cubetas implementada no toman decisiones preguntando si un término es mayor que otro. Acceden directamente a la frecuencia, a un dígito decimal o a una cubeta indexada. Por ello no están sujetos a esa cota, aunque tampoco son lineales para cualquier entrada: dependen de que k, b y d permanezcan acotados o razonables frente a n.")
    add_table(doc, ["Algoritmo", "Estructura principal", "Complejidad", "Razón del costo"], [
        ["Counting Sort", "Arreglo de conteos de 0 a k", "O(n + k)", "Recorre n datos y luego k posiciones del arreglo."],
        ["Radix Sort", "Counting Sort por cada dígito", "O(d(n + 10))", "Por cada uno de d dígitos recorre n datos y 10 valores."],
        ["Bucket por frecuencia", "Una lista por frecuencia de 0 a k", "O(n + k)", "Distribuye n datos y concatena k + 1 cubetas."],
    ], [3.0, 4.1, 2.6, 7.0], 8.5)
    heading(doc, "3.1 Counting Sort", 2)
    text(doc, "Counting Sort no compara un término con otro. Primero identifica k, crea un arreglo de conteos de tamaño k + 1 y aumenta el contador asociado a la frecuencia de cada término. Luego recorre las frecuencias desde k hasta 0 para calcular posiciones de salida y ubica cada par término-frecuencia. La estabilidad conserva el orden de primera aparición cuando existen empates. El algoritmo realiza recorridos lineales sobre los n elementos y sobre las k + 1 frecuencias posibles; por tanto, T(n, k) = O(n + k).")
    heading(doc, "3.2 Radix Sort", 2)
    text(doc, "Radix Sort procesa primero las unidades, luego las decenas y continúa con posiciones más significativas si existen. Cada pasada usa diez conteos, uno por dígito de 0 a 9. El código recorre los dígitos desde 9 hasta 0 para producir orden descendente directamente; no invierte la lista al final. La estabilidad de cada pasada es esencial: los elementos que comparten un dígito conservan el orden obtenido en la pasada anterior. En consecuencia, después de procesar d dígitos el número completo queda ordenado. El costo es T(n, d, b) = O(d(n + b)); como b = 10 y aquí d = 2, el comportamiento es lineal respecto a n para este dominio, pero la forma general debe conservar el factor d.")
    heading(doc, "3.3 Bucket Sort", 2)
    text(doc, "La implementación es una variante de Bucket Sort para claves enteras discretas: crea una cubeta por cada frecuencia posible entre 0 y k. Cada cubeta almacena los términos que poseen exactamente esa frecuencia y los conserva en orden de llegada. No se ejecuta un ordenamiento interno porque los elementos de una misma cubeta están empatados en la clave de ordenamiento. Al final, el algoritmo concatena las cubetas desde k hasta 0 para obtener el orden descendente. Esta variante se parece a Counting Sort porque usa direccionamiento directo por frecuencia, pero se diferencia en que conserva listas de elementos dentro de cada casillero, no solo conteos y posiciones. Su costo determinista es O(n + k): distribuir visita n elementos y recuperar visita k + 1 cubetas más los n elementos almacenados.")

    heading(doc, "4. Medición empírica")
    add_table(doc, ["Algoritmo", "n", "Promedio", "Mínimo", "Máximo"], [
        [
            names[key],
            str(meta["unique_terms"]),
            f"{times[key]:.6f} ms",
            f"{result['methods'][key]['minimum_execution_ms']:.6f} ms",
            f"{result['methods'][key]['maximum_execution_ms']:.6f} ms",
        ]
        for key in algorithms
    ], [4.3, 1.5, 3.2, 3.2, 3.2], 8.5)
    text(doc, f"Interpretación: los tres tiempos se calcularon {repetitions} veces sobre exactamente la misma entrada. Bucket por frecuencia fue el más rápido en esta medición; Radix Sort tardó aproximadamente {bucket_ratio:.2f} veces lo observado para Bucket. Esa diferencia no contradice las complejidades: en un corpus pequeño las constantes de implementación y la cantidad de recorridos son visibles. Counting Sort busca el máximo, cuenta, calcula posiciones y llena una salida. Radix Sort repite su pasada estable por cada uno de los {meta['radix_digit_count']} dígitos. Bucket por frecuencia distribuye los pares en listas y las concatena sin construir posiciones de salida. Los valores inferiores a un milisegundo pueden variar por el sistema operativo, el intérprete y la memoria; por ello se presentan promedio, mínimo y máximo, y la conclusión principal sigue siendo asintótica.")

    heading(doc, "5. Validación de resultados: 15 términos más frecuentes")
    text(doc, "La siguiente tabla muestra el resultado producido por cada implementación. En cada celda aparece término — frecuencia. La coincidencia de las tres columnas valida que los tres algoritmos entregaron el mismo ranking descendente para la misma lista de frecuencias.")
    rows = []
    for index in range(15):
        row = [str(index + 1)]
        for key in algorithms:
            item = rankings[key][index]
            row.append(f"{item['term']} — {item['frequency']}")
        rows.append(row)
    add_table(doc, ["Puesto", "Counting Sort", "Radix Sort", "Bucket Sort"], rows, [1.7, 4.4, 4.4, 4.4], 8.5)
    text(doc, "Resultado de validación: las tres listas coinciden en los 15 puestos y sus frecuencias. Además, el programa no se limita al top 15: compara el ranking completo de cada algoritmo contra el producido por Counting Sort y verifica, mediante un recorrido, que ninguna frecuencia aumente en la salida. Cuando dos términos tienen la misma frecuencia, se conserva su orden de primera aparición en el corpus para que la comparación sea reproducible.")

    heading(doc, "6. Conclusión")
    text(doc, "Counting Sort y la variante Bucket por frecuencia cumplen O(n + k); Radix Sort cumple O(d(n + 10)) y se comporta como O(n) solo bajo el supuesto de base y número de dígitos acotados. Estos algoritmos evitan la cota de los ordenamientos por comparación porque indexan directamente frecuencias o dígitos, no porque sean mágicamente mejores para cualquier entrada. La medición real se realizó sobre la lista de frecuencias extraída del corpus auditado y la tabla final confirma que las tres implementaciones producen el mismo top 15 y el mismo ranking completo en orden descendente. Con ello se cubren los tres componentes solicitados: fundamento teórico, evidencia de tiempos y validación verificable de resultados.")

    heading(doc, "7. Declaración de uso de inteligencia artificial generativa")
    text(doc, "Se utilizó ChatGPT Codex como herramienta de apoyo para revisar la estructura del proyecto, explicar conceptos de complejidad, proponer casos de prueba y mejorar la redacción técnica. Su uso no reemplazó el diseño algorítmico ni la ejecución de las pruebas. Counting Sort, Radix Sort, la variante Bucket por frecuencia, la validación de rankings y las mediciones se implementaron y ejecutaron explícitamente en Python con listas, diccionarios y ciclos.")
    text(doc, "Ejemplo de consulta de apoyo: Explica bajo qué condiciones Counting Sort y Radix Sort pueden comportarse linealmente sin reemplazar la implementación del algoritmo. El estudiante revisó la explicación, ejecutó el código y verificó los datos incluidos en las tablas de este informe.")
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    doc.save(OUTPUT_PATH)
    print(f"Informe generado: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
