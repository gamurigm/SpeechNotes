# SpeechNotes
## Propuesta V1.2.52
Repositorio de trabajo para SpeechNotes — aplicación para captura, transcripción, edición y búsqueda semántica de notas de audio.

Este proyecto incluye: frontend web (Next.js), herramientas y demos Python para RAG/ búsqueda semántica, integración con clientes ASR (Riva), y un agente que combina indexación + generación con NVIDIA NIM.

---

## Estructura principal
- `web/` — frontend Next.js (React). Componentes: editor Markdown, panel de transcripción en tiempo real, grabador y reproductor.
- `src/` — lógica Python de la aplicación (agent, llm wrappers, audio helpers).
  - `src/agent/` — vector store, indexer, loader, nodes/graph para el agente RAG.
  - `src/llm/` — wrappers para llamadas a LLMs (NVIDIA NIM client).
- `python-clients/` — clientes y scripts para Riva (ASR) y utilidades relacionadas.
- `server/` — utilidades y demos ejecutables (RAG demo, agent demo, scripts de limpieza).
- `notas/` — transcripciones en Markdown (entrada para indexación).
- `docs/` — documentación y planes (semantic search plan, diseños, etc.).

---

## Qué contiene este repo (resumen)
- Demo RAG local: `server/rag_demo.py` (usa `sentence-transformers` + FAISS; opcional OpenAI para generación).
- Demo agent-RAG: `server/agent_rag_demo.py` (usa `src.agent.VectorStore` con embeddings NVIDIA y `NvidiaInferenceClient` para generación con NIM).
- Scripts ASR (Riva): `python-clients/scripts/asr/transcribe_file_offline.py` (soporta `--dry-run` para depuración de headers y conexión).
- Limpieza de transcripciones: `server/cleanup_transcriptions.py` (mueve o borra transcripciones inválidas en `notas/`).

---

## Requisitos (rápido)
- Python 3.10+ (recomendado) con un entorno virtual.
- Node.js 18+ para el frontend (Next 16 usa React 19).
- Paquetes Python necesarios para demos y agent (ejemplo):

```
pip install sentence-transformers faiss-cpu transformers openai python-dotenv
```

Nota: `faiss-cpu` puede requerir compilación en algunos sistemas; alternativamente usar `faiss` provisto por conda.

---

## Variables de entorno importantes
- `NVIDIA_EMBEDDING_API_KEY` — clave para embeddings NVIDIA (usada por `src.agent.VectorStore`).
- `NVIDIA_API_KEY` — clave para generación en NVIDIA NIM (usada por `src.llm.nvidia_client.NvidiaInferenceClient`).
- `OPENAI_API_KEY` — opcional: si está presente `server/rag_demo.py` usará OpenAI (`gpt-4o-mini`) para generar la respuesta final.

Export ejemplo (PowerShell):
```
$env:NVIDIA_EMBEDDING_API_KEY = 'tu_key'
$env:NVIDIA_API_KEY = 'tu_key'
$env:OPENAI_API_KEY = 'tu_key'  # opcional
```

---

## Comandos útiles
# SpeechNotes — Descripción del sistema

Este repositorio contiene el sistema SpeechNotes: una plataforma para capturar audio, generar transcripciones, almacenar y enriquecer notas en Markdown y habilitar búsqueda semántica y generación de respuestas (RAG). El objetivo es convertir grabaciones en notas útiles y consultables, permitiendo búsquedas por contenido, recuperación de fragmentos relevantes y generación de resúmenes o respuestas a preguntas basadas en las transcripciones.

Este README describe el propósito del sistema, su arquitectura lógica y los flujos principales —no se centra en una implementación concreta de frontend—, según la especificación en `docs/SpeechNotes.pdf`.

---

## Propósito del sistema
- Capturar y procesar audio (local o remoto) para producir transcripciones de alta calidad.
- Estandarizar y almacenar las transcripciones en Markdown enriquecido (metadatos, timestamps, temas).
- Indexar el contenido para búsqueda semántica eficiente (embeddings + vector DB local o remota).
- Permitir respuestas contextuales mediante RAG: recuperar fragmentos relevantes y generar texto (resúmenes, respuestas, exportación).

---

## Arquitectura lógica (visión general)

1. Captura de audio
  - Origenes: grabación en la app, carga de archivos, integración con clientes ASR (Riva).
  - Formatos soportados: WAV (mono/16-bit), FLAC, OPUS.

2. Transcripción (ASR)
  - Motor principal: Riva (scripts en `python-clients/`) o servicios locales/cloud alternativos.
  - Resultado: archivo `.md` por sesión con metadata (fecha, duración, idioma) y sección de transcripción completa.

3. Procesamiento y enriquecimiento
  - Post-procesado: limpieza, detección de tópicos, timestamps, formato profesional en Markdown (`src/agent/transcription_loader.py`).
  - Validación: heurística para detectar transcripciones ruidosas/invalidas y opciones para moverlas o eliminarlas (`server/cleanup_transcriptions.py`).

4. Indexación y vectorización
  - Embeddings: proveedor configurable (local con `sentence-transformers` o remoto con NVIDIA embeddings via `NVIDIA_EMBEDDING_API_KEY`).
  - Vector store: FAISS local o alternativa gestionada.
  - Indexer: extrae chunks temáticos y los añade al vector store (`src/agent/transcription_indexer.py`).

5. Recuperación y generación (RAG)
  - Recuperación: consulta semántica que devuelve fragmentos relevantes con metadata y score.
  - Generación: uso opcional de LLMs para construir respuestas (OpenAI si `OPENAI_API_KEY` presente, o NVIDIA NIM si `NVIDIA_API_KEY` está configurada). Implementaciones de demo en `server/rag_demo.py` y `server/agent_rag_demo.py`.

6. Interfaz y exportación
  - Notas en Markdown editables, exportación a formatos (Markdown/SRT), integración con UI para insertar fragmentos recuperados.

---

## Flujo de datos (ejemplo de uso)
1. Usuario graba audio en la aplicación o sube un archivo.
2. El sistema llama al motor ASR y genera una transcripción `.md` en `notas/`.
3. El indexer procesa la `.md`, crea chunks temáticos y solicita embeddings.
4. Embeddings se almacenan en FAISS (vector store) junto con metadata (archivo, timestamp, tópico).
5. Al realizar una búsqueda o pregunta, el sistema consulta la base vectorial, recupera los mejores fragmentos y, si está habilitado, pasa ese contexto a un LLM para generar la respuesta final.

---

## Componentes principales (lógica, no UI)
- Captura/ASR: `python-clients/` (scripts y helpers Riva).
- Ingestión y formateo: `src/agent/transcription_loader.py`.
- Indexación: `src/agent/transcription_indexer.py`, `src/agent/transcription_embedder.py`.
- Vector store: `src/agent/vector_store.py` (FAISS + proveedor de embeddings).
- Generación LLM: `src/llm/nvidia_client.py` (wrapper para NIM). Demos de RAG en `server/`.

---

## Requisitos mínimos y variables de entorno
- Python 3.10+ (entorno virtual recomendado).
- Dependencias para demos: `sentence-transformers`, `faiss-cpu`, `transformers`, `openai`, `python-dotenv`.
- Env vars claves:
  - `NVIDIA_EMBEDDING_API_KEY`: clave para embeddings NVIDIA (opcional, permite usar NIM embeddings).
  - `NVIDIA_API_KEY`: clave para llamadas a NVIDIA NIM (generación).
  - `OPENAI_API_KEY`: si existe, se puede usar OpenAI para generación en demos.

---

## Operaciones comunes (línea de comandos)
- Indexar todas las transcripciones (demo agent):
```
setx NVIDIA_EMBEDDING_API_KEY "<key>"      # Windows / PowerShell example
setx NVIDIA_API_KEY "<key>"
python server/agent_rag_demo.py --query "¿Cómo exporto una transcripción?"
```
- Ejecutar demo RAG local (sin NVIDIA):
```
python server/rag_demo.py --query "¿Cómo exporto una transcripción?"
```
- Probar transcripción Riva en modo diagnóstico (no envía audio):
```
python python-clients/scripts/asr/transcribe_file_offline.py --input-file "ruta/al/audio.wav" --server grpc.nvcf.nvidia.com:443 --use-ssl --metadata function-id "<id>" --metadata "authorization" "Bearer <token>" --language-code en-US --model-name pa_canary1b --dry-run
```

---

