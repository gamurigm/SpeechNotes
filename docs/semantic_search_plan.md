# Plan de Búsqueda Semántica — SpeechNotes

Fecha: 2025-11-28

## Objetivo

Proveer una búsqueda semántica sobre las transcripciones y notas del proyecto `SpeechNotes` que permita consultar por significado (no sólo por palabras clave) y devolver fragmentos relevantes con timestamps y enlace al archivo `.md` correspondiente.

## Resumen rápido

- Indexar todos los `.md` en `data/` y `notas/` en fragmentos (chunks).
- Obtener embeddings para cada chunk (modelo local `sentence-transformers/all-MiniLM-L6-v2` por defecto).
- Guardar vectores en un índice `FAISS` en disco y metadatos en una base ligera (SQLite o JSONL).
- Exponer una API `FastAPI` con endpoint `/search` para realizar consultas semánticas.
- Añadir una UI `SearchBar` / `SearchResults` en `web/` que consume la API y permite insertar fragmentos en el editor.

## Arquitectura recomendada

- Frontend: `Next.js` (reutiliza `web/` existente). Componentes `SearchBar` y `SearchResults`.
- Backend: `FastAPI` para endpoints HTTP/WS y control de indexación.
- Vector store: `faiss` (local, en disco). Alternativa escalable: `Milvus` o `Weaviate`.
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (local, rápido). Alternativa remota: `OpenAI embeddings`.
- Metadatos: SQLite (`data/index_meta.db`) o `data/index_meta.jsonl`.

## Pipeline (detallado)

1. Lectura de archivos
   - Buscar recursivamente archivos `*.md` en `data/` y `notas/`.
2. Preprocesamiento
   - Limpiar Markdown (eliminar codeblocks pesados, imágenes, enlaces manteniendo texto visible).
   - Extraer metadatos si existen (timestamps, speaker tags) y conservarlos.
3. Chunking
   - Dividir por frases o por tamaño aproximado (ej.: 150–400 tokens / ~800–1200 caracteres) con solapamiento (overlap) de 20–50 tokens.
   - Guardar por chunk: `note_id` (slug/filename), `file_path`, `chunk_index`, `start_time`, `end_time` (si están disponibles), `snippet` (texto plano del chunk).
4. Embeddings
   - Calcular embedding por chunk con `sentence-transformers`.
   - Normalizar vectores (si se usa similitud coseno con FAISS IndexFlatIP se normalizan con `faiss.normalize_L2`).
5. Almacenamiento
   - Guardar vectores en FAISS (`data/faiss_index.bin`) y metadatos en SQLite (`data/index_meta.db`) o JSONL.
6. Consulta
   - Para cada query: obtener embedding de la query, buscar top-K en FAISS, opcionalmente rerankear (cross-encoder o similitud exacta) y devolver snippets con metadatos.

## Esquema de metadatos (por chunk)

- id (int, vector id)
- note_id (string)
- file_path (string)
- chunk_index (int)
- snippet (string)
- start_time (float|null)
- end_time (float|null)

## API (FastAPI) — endpoints sugeridos

- `POST /index/rebuild` — Regenerar índice desde los `.md` (protección admin o auth simple).
- `POST /search` — Body: `{ "q": "texto de búsqueda", "top_k": 8 }`. Devuelve: lista de `{score, snippet, file_path, start_time, end_time, chunk_index}`.
- `GET /note/{note_id}` — Devuelve el contenido o ruta del `.md`.

## Ejemplo de mensajes de respuesta `/search`

```json
{
  "results": [
    {"id": 123, "score": 0.87, "snippet": "...", "file_path": "notas/transcripcion_20251108.md", "start_time": 12.3, "end_time": 17.9, "chunk_index": 4},
    ...
  ]
}
```

## Reranking y contexto

- Recuperar top-N (ej. 50) desde FAISS y rerankear top-K (ej. 10) usando:
  - Recomputar similitud coseno exacta entre embeddings (barato), o
  - (Opcional) usar un cross-encoder para mejor ranking (más costoso).
- Incluir chunks vecinos (+/- 1) para contexto cuando se muestre el resultado al usuario.

## Frontend — integración (Next.js)

- Componentes:
  - `components/SearchBar.tsx` — input y envío de consulta.
  - `components/SearchResults.tsx` — lista de resultados con snippets, timestamps y botón `Insertar en nota`.
  - `pages/search.tsx` o integrar el `SearchBar` en la `TopBar` existente.
- Comportamiento:
  - Llamar a `POST http://localhost:8000/search` o a la ruta proxy en Next (`/api/search`) y mostrar resultados.
  - Al hacer click en un resultado: mostrar contexto (chunks adyacentes) y permitir insertar el texto en el editor Markdown activo.

## Scripts sugeridos (archivos)

- `server/indexer.py` — Script que realiza todo el pipeline: lee `.md`, chunkea, embeddiza y guarda FAISS + metadata.
- `server/search_api.py` — FastAPI que carga `faiss` y `sentence-transformers` y expone `/search` y `/index/rebuild`.
- `web/components/SearchBar.tsx`, `web/pages/search.tsx` — pequeños componentes React para consulta y resultado.

## Dependencias (Python)

- `sentence-transformers`
- `faiss-cpu` (o `faiss` según plataforma)
- `fastapi`, `uvicorn`
- `sqlite3` (stdlib) o `sqlite-utils`
- `tqdm` (opcional, para indexación)

Instalación rápida (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install sentence-transformers faiss-cpu fastapi uvicorn sqlite-utils tqdm
```

## Comandos de ejemplo

- Indexar (local):

```powershell
python server/indexer.py
```

- Ejecutar API:

```powershell
uvicorn server.search_api:app --host 0.0.0.0 --port 8000 --reload
```

- Ejecutar frontend (si Next.js):

```powershell
cd web
npm install
npm run dev
```

## Consideraciones prácticas

- FAISS en Windows: los wheels `faiss-cpu` normalmente funcionan, pero si hay problemas se puede usar `annoy` o `hnswlib` como alternativa.
- Guardar periódicamente el índice y proporcionar `POST /index/rebuild` para actualizar cuando se agreguen/editen notas.
- Para uso multiusuario o a escala: migrar a `Milvus`/`Weaviate` y usar embeddings gestionados (OpenAI) si conviene.

## Siguientes pasos sugeridos

1. Confirmas si quieres `FAISS + sentence-transformers` (por defecto) o `OpenAI embeddings`.
2. Si confirmas, creo los archivos en el repo: `server/indexer.py`, `server/search_api.py`, y los componentes mínimos en `web/` para probar la integración.
3. Ejecución local y validación con un conjunto pequeño de `.md` (yo puedo scaffoldear y ejecutar pruebas básicas).

---

Archivo generado automáticamente por el plan de diseño de búsqueda semántica.
