# 🎙️ SpeechNotes

Propuesta V1.2.52 — Aplicación para captura, transcripción, edición y búsqueda semántica de notas de audio.

---

## 📚 Índice
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
- [Notas de desarrollo / fixes recientes](#notas-de-desarrollo--fixes-recientes)
- [Tareas (TAREAS.md)](#tareas-tareasmd)
- [Contribución](#contribución)
- [Licencia y contacto](#licencia-y-contacto)

---

## ✨ Resumen
SpeechNotes convierte grabaciones en notas útiles: captura audio, genera transcripciones en Markdown enriquecido, permite edición y exportación, y habilita búsqueda semántica y RAG (recuperación + generación). Soporta integraciones ASR (Riva) y generación/embeddings (NVIDIA NIM, OpenAI opcional).

---

## 📈 Estado y alcance
**Versión:** V1.2.52 — en desarrollo.

Incluye:
- Frontend (Next.js) con panel de grabación, editor Markdown y UI de transcripción.
- Herramientas Python para indexación (FAISS), generación RAG y demos.
- Integraciones experimentales con Riva y NVIDIA.

---

## 🗂️ Estructura del repositorio
- `web/` — Frontend Next.js (React, Tailwind, HeroUI).
- `src/` — Lógica Python (agent, indexer, loaders, wrappers LLM).
- `python-clients/` — clientes y scripts ASR (Riva).
- `server/` — demos ejecutables (RAG demo, agent demo).
- `notas/` — transcripciones (.md).
- `docs/` — diseño y documentación.

---

## 🛠️ Requisitos
- Node.js 18+ (recomendado)
- Python 3.10+
- Ejemplo de paquetes Python:
```bash
pip install sentence-transformers faiss-cpu transformers openai python-dotenv
```

---

## 🔐 Variables de entorno importantes
- `NVIDIA_EMBEDDING_API_KEY`
- `NVIDIA_API_KEY`
- `OPENAI_API_KEY` (opcional)

Ejemplo (PowerShell):
```powershell
$env:NVIDIA_EMBEDDING_API_KEY = 'tu_key'
$env:NVIDIA_API_KEY = 'tu_key'
$env:OPENAI_API_KEY = 'tu_key'
```

> Nota rápida (PowerShell): para evitar `ModuleNotFoundError: No module named 'src'` al correr scripts desde `server/`, exporta `PYTHONPATH` antes de ejecutar.

```powershell
cd server
$env:PYTHONPATH = '..'
python agent_rag_demo.py --index-new-only
python agent_rag_demo.py --query "¿Cómo exporto una transcripción?" --topk 5
```

---

## 🚀 Inicio rápido

### Frontend (Next.js)
1. Entrar a `web/`:
```bash
pnpm install
pnpm dev
```
2. Abrir: http://localhost:3000

Notas:
- Frontend usa Tailwind + HeroUI (config en `web/hero.ts`).
- Si aparece warning ESM: añade `"type": "module"` en `web/package.json`.

### Demos / Scripts Python
- Demo RAG:
```bash
python server/rag_demo.py --query "¿Cómo exporto una transcripción?"
```
- Indexar todas las transcripciones:
```bash
python server/agent_rag_demo.py --index-all
```

---

## 🔁 Flujo de datos (alto nivel)
1. Usuario graba/sube audio → ASR genera `.md` en `notas/`.
2. Indexer crea chunks → solicita embeddings.
3. Embeddings guardados en FAISS.
4. Consultas recuperan fragmentos; LLM opcional para respuestas/sumarizados.

---

## 🧩 Componentes principales
- Captura/ASR: `python-clients/`
- Formateo/ingestión: `src/agent/transcription_loader.py`
- Indexación/embeddings: `src/agent/transcription_indexer.py`
- Vector store: `src/agent/vector_store.py` (FAISS)
- Generación: `src/llm/nvidia_client.py`
- Frontend: `web/app/` — grabador, Markdown viewer/editor

---

## ⚙️ Operaciones comunes
- Ejecutar frontend:
```bash
cd web
pnpm dev
```
- Ejecutar demo RAG:
```bash
python server/rag_demo.py --query "¿Dónde está el capítulo sobre X?"
```

---

## 🛠️ Notas de desarrollo / fixes recientes
- Integración inicial con HeroUI y ajustes de Tailwind.
- Migración parcial a React 18.
- Fix: renderizado de chat adaptado a `message.content`.
- Fix: corrección de un parse error en JSX.
- Mejora de MarkdownViewer (clases `prose`) para headings, listas y código.
- Añadido `"type": "module"` en `web/package.json` para resolver warnings ESM.
- Chat/UI depende de que el índice FAISS esté cargado en la sesión; reindexa tras reiniciar backend (`python agent_rag_demo.py --index-new-only`).

---

## ✅ Tareas (revisar `TAREAS.md`)
- [x] actualizar la ui para usar componentes de HeroUI (Next.js) — estudiada e integrada.
  - Detalles: configuración `hero.ts`, `providers.tsx`, uso de componentes HeroUI en Navbar, Buttons, Cards.
- (Ver `TAREAS.md` para historial completo y nuevas tareas.)

---

## 🤝 Contribución
1. Leer `TAREAS.md` antes de trabajar.
2. Abrir PR con descripción y pasos para reproducir.
3. Commits atómicos; mensajes claros (ej. `chore/ui: ...`, `fix(chat): ...`).

---

## 📄 Licencia y contacto
- Proyecto interno / académico. Añadir licencia si se publica.
- Para dudas: abrir un issue en el repositorio.

---

