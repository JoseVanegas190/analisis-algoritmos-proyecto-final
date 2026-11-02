# Proyecto final de Análisis de Algoritmos

Aplicación local para analizar los abstracts del corpus de 20 artículos sobre inteligencia artificial generativa. Los algoritmos solicitados se implementan de forma explícita con listas, diccionarios, matrices y ciclos.

## Funcionalidades

- Extracción de abstracts, títulos y autores desde `data/pdfs`.
- Similitud clásica: Levenshtein, Needleman-Wunsch, Jaccard y TF-IDF con coseno.
- Similitud con dos modelos de embeddings preentrenados. Los modelos generan vectores; el coseno se calcula en el proyecto.
- Clustering jerárquico: Single Linkage, Complete Linkage y Average Linkage.
- Dendrogramas construidos a partir de la historia de fusiones propia.
- Evaluación interna mediante coeficiente Silhouette implementado manualmente.
- Ranking complementario con Counting Sort, Radix Sort y Bucket Sort.

No se usa una biblioteca de alto nivel para resolver los algoritmos clásicos, el clustering ni el ordenamiento.

## Ejecutar

1. Instala las dependencias:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Haz doble clic en `iniciar_app.bat`.

3. En el menú:

   - **Preparar corpus:** extrae los abstracts de `data/pdfs`.
   - **Similitud textual:** selecciona dos o más artículos y compara todos sus pares.
   - **Clustering jerárquico:** crea los tres dendrogramas y compara su silueta.
   - **Ranking de términos:** genera la evidencia complementaria de ordenamiento.

Los modelos de embeddings se descargan en la primera ejecución y requieren conexión a Internet. Si los PDF no están disponibles, la aplicación puede trabajar con `data/processed/abstracts.json`.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `src/classic_similarity.py` | Cuatro algoritmos clásicos explícitos. |
| `src/embedding_similarity.py` | Dos embeddings y coseno manual. |
| `src/hierarchical_clustering.py` | Tres criterios de clustering jerárquico. |
| `src/clustering_evaluation.py` | Coeficiente Silhouette manual. |
| `src/requirement_one.py` | Coordinación de comparaciones por pares. |
| `src/requirement_two.py` | TF-IDF, distancias y clustering del corpus. |
