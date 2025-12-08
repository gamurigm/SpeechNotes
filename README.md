# SpeechNotes

Propuesta V1.2.52 — Aplicación para captura, transcripción, edición y búsqueda semántica de notas de audio.

---

## Índice
- [Resumen](#resumen)
- [Estado y alcance](#estado-y-alcance)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Requisitos](#requisitos)
- [Variables de entorno](#variables-de-entorno)
- [Inicio rápido](#inicio-rápido)
  - [Frontend (Next.js)](#frontend-nextjs)
  - [Demos / Scripts Python](#demos--scripts-python)
- [Flujo de datos (alto nivel)](#flujo-de-datos-alto-nivel)
- [Componentes principales](#componentes-principales)
- [Operaciones comunes](#operaciones-comunes)
- [Notas de desarrollo](#notas-de-desarrollo)
- [Contacto / Contribución](#contacto--contribución)

---

## Resumen
SpeechNotes convierte grabaciones en notas útiles: captura audio, genera transcripciones en Markdown enriquecido, permite edición y exportación, y habilita búsqueda semántica y RAG (recuperación + generación). Soporta integración con clientes ASR (Riva) y generación con proveedores (NVIDIA NIM, OpenAI opcional).

---

## Estado y alcance
Versión: V1.2.52 — proyecto en desarrollo. Contiene:
- Frontend (Next.js) con panel de grabación, editor Markdown y UI de transcripción.
- Herramientas Python para indexación (FAISS), generación RAG y demos.
- Integraciones experimentales con Riva (ASR) y NVIDIA (embeddings + generación).

---

## Estructura del repositorio
- `web/` — Frontend Next.js (React). Componentes: grabador, transcripción en vivo, Markdown editor/viewer.
- `src/` — Lógica Python principal (agent, indexer, loaders, wrappers LLM).
  - `src/agent/` — indexer, loader y vector store.
  - `src/llm/` — wrappers para NIM / otros LLMs.
- `python-clients/` — clientes y scripts para Riva (ASR) y utilidades.
- `server/` — demos ejecutables (RAG demo, agent demo, cleaning scripts).
- `notas/` — transcripciones y notas en formato Markdown.
- `docs/` — diseños, planes y documentación de alto nivel.

---

## Requisitos
- Node.js 18+ (recomendado) — ejecutar frontend (Next.js).
- Python 3.10+ — para demos y herramientas (virtualenv recomendado).
- Paquetes Python (ejemplo):
  ```
  pip install sentence-transformers faiss-cpu transformers openai python-dotenv
  ```
  Nota: `faiss-cpu` puede requerir conda o compilación en algunos sistemas.

---

## Variables de entorno importantes
- `NVIDIA_EMBEDDING_API_KEY` — embeddings NVIDIA (opcional).
- `NVIDIA_API_KEY` — generación con NVIDIA NIM (opcional).
- `OPENAI_API_KEY` — usar OpenAI para generación si está disponible.
Export ejemplo (PowerShell):
```powershell
$env:NVIDIA_EMBEDDING_API_KEY = 'tu_key'
$env:NVIDIA_API_KEY = 'tu_key'
$env:OPENAI_API_KEY = 'tu_key'  # opcional
```

---

## Inicio rápido

### Frontend (Next.js)
1. En la carpeta `web/`:
```bash
pnpm install      # o npm/yarn según tu setup
pnpm dev
```
2. Visitar `http://localhost:3000` (o puerto que indique la app).

Notas:
- El frontend usa Tailwind + HeroUI (config en `web/hero.ts`).
- Si ves warnings ESM por archivos `.ts`, añadir `"type": "module"` en `web/package.json` puede resolverlos.

### Demos / Scripts Python
- Demo RAG local:
```bash
python server/rag_demo.py --query "¿Cómo exporto una transcripción?"
```
- Demo agent-RAG (usa `src.agent.VectorStore`):
```bash
python server/agent_rag_demo.py --query "Resumen de la última clase"
```
- Prueba ASR (modo diagnóstico):
```bash
python python-clients/scripts/asr/transcribe_file_offline.py --input-file "audio.wav" --dry-run
```

---

## Flujo de datos (resumen)
1. Usuario graba o sube audio.
2. Sistema llama al motor ASR → genera `.md` en `notas/` con metadata.
3. Indexer procesa `.md`, crea chunks y solicita embeddings.
4. Embeddings almacenados en FAISS (vector store).
5. Consultas recuperan fragmentos relevantes; opcionalmente se pasan a un LLM para generar respuestas/sumarizados.

---

## Componentes principales (funcionales)
- Captura/ASR: `python-clients/` (Riva helpers).
- Formateo/ingestión: `src/agent/transcription_loader.py`.
- Indexación/embeddings: `src/agent/transcription_indexer.py`, `src/agent/transcription_embedder.py`.
- Vector store: `src/agent/vector_store.py` (FAISS).
- Generación: `src/llm/nvidia_client.py`.
- Frontend: `web/app/` — grabador, Markdown viewer/editor, panel de transcripción.

---

## Operaciones comunes
- Indexar todas las transcripciones:
```bash
python server/agent_rag_demo.py --index-all
```
- Ejecutar demo RAG:
```bash
python server/rag_demo.py --query "¿Dónde está el capítulo sobre X?"
```
- Ejecutar frontend:
```bash
cd web
pnpm dev
```

---

## Notas de desarrollo / fixes recientes
- Integración inicial con HeroUI y ajustes de Tailwind.
- Adaptación del frontend a React 18 donde fue necesario.
- Fix: renderizado de chat adaptado a `message.content` (antes `message.parts`).
- Fix: corrección de un parse error en JSX (duplicación en clase).
- Mejora del MarkdownViewer para que `#` y otros elementos se muestren con estilos `prose`.

---

## Contribución
1. Leer `TAREAS.md` y el checklist de tareas antes de comenzar cambios.
2. Abrir PR por cada feature/bugfix con descripción clara y pasos para reproducir.
3. Mantener commits atómicos y mensajes claros (ej. `chore/ui: ...`, `fix(chat): ...`).

---

## Licencia y contacto
- Proyecto interno / académico. Agregar licencia explícita si se publica.
- Para dudas y coordinar cambios: abrir un issue en este repositorio.

---

