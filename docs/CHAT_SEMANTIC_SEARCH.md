# Sistema de Chat con Búsqueda Semántica - SpeechNotes

## 🎯 Descripción

Sistema de chat RAG (Retrieval-Augmented Generation) que permite hacer preguntas sobre tus transcripciones de clases usando búsqueda semántica y NVIDIA NIM.

## 🚀 Características

- ✅ **Búsqueda semántica** con ChromaDB y NVIDIA Embeddings
- ✅ **Chat streaming** compatible con Vercel AI SDK
- ✅ **Respuestas contextuales** sobre tus documentos
- ✅ **Información temporal**: Pregunta cuándo se grabó una clase
- ✅ **UI moderna** con streaming de respuestas

## 📋 Requisitos Previos

1. **Variables de entorno** en `.env`:
   ```bash
   # Para embeddings y generación
   NVIDIA_EMBEDDING_API_KEY=nvapi-xxxxx
   NVIDIA_API_KEY=nvapi-xxxxx
   NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
   MODEL_NAME=deepseek-ai/deepseek-v3.1-terminus
   
   # MongoDB
   MONGO_URI=mongodb://localhost:27017/
   MONGO_DB_NAME=agent_knowledge_base
   ```

2. **Dependencias instaladas**:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend (ya instaladas)
   cd web
   pnpm install
   ```

## 🔧 Configuración Inicial

### 1. Indexar tus documentos

Antes de usar el chat, necesitas indexar tus transcripciones de MongoDB a ChromaDB:

```bash
# Desde la raíz del proyecto
python scripts/index_documents.py
```

Este script:
- Lee todas las transcripciones procesadas de MongoDB
- Genera embeddings con NVIDIA API
- Los almacena en ChromaDB (carpeta `knowledge_base/chroma_db/`)

### 2. Iniciar el backend

```bash
cd backend
python -m uvicorn main:socket_app --host 0.0.0.0 --port 8001 --reload
```

El endpoint de chat estará en: `http://localhost:8001/api/chat/stream`

### 3. Iniciar el frontend

```bash
cd web
pnpm dev
```

La interfaz estará en: `http://localhost:3006/dashboard/chat`

## 💬 Uso del Chat

### Preguntas de Ejemplo

1. **Búsqueda de contenido**:
   - "¿De qué trata la clase de análisis y diseño?"
   - "Resume los puntos principales sobre patrones de diseño"

2. **Información temporal**:
   - "¿Cuándo se grabó la clase sobre singleton?"
   - "¿Qué fecha tiene el documento sobre factory method?"

3. **Búsqueda específica**:
   - "¿Qué dice el documento sobre SOLID?"
   - "Explícame el patrón observer según mis notas"

## 🏗️ Arquitectura

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Next.js    │─────▶│   FastAPI    │─────▶│   MongoDB   │
│  Frontend   │      │   Backend    │      │  (docs)     │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  ChromaDB    │
                     │ (embeddings) │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  NVIDIA NIM  │
                     │  (LLM + EMB) │
                     └──────────────┘
```

### Flujo de Datos

1. **Usuario envía pregunta** → Next.js (`/api/chat`)
2. **Next.js proxea** → FastAPI (`/api/chat/stream`)
3. **FastAPI busca contexto**:
   - Genera embedding de la pregunta (NVIDIA Embeddings)
   - Busca documentos similares (ChromaDB)
4. **FastAPI genera respuesta**:
   - Construye prompt con contexto
   - Llama a NVIDIA NIM para generar respuesta
   - Stream de chunks al frontend
5. **Frontend renderiza** respuesta en tiempo real

## 📁 Archivos Clave

### Backend

- `backend/routers/chat.py`: Endpoint de chat con streaming
- `backend/services/rag_service.py`: Lógica RAG (búsqueda + generación)
- `src/database/vector_store.py`: Wrapper de ChromaDB
- `src/llm/nvidia_client.py`: Cliente NVIDIA NIM

### Frontend

- `web/app/api/chat/route.ts`: Proxy Next.js al backend
- `web/app/dashboard/chat/page.tsx`: UI del chat
- `web/hooks/useRecording.ts`: Hook para grabación (reutilizado)

### Scripts

- `scripts/index_documents.py`: Indexa documentos MongoDB → ChromaDB
- `scripts/regenerate_from_mongo.py`: Regenera markdowns desde MongoDB

## 🔍 Cómo Funciona la Búsqueda Semántica

### 1. Indexación (Offline)

```python
# Para cada documento en MongoDB:
documento = db.transcriptions.find_one({"processed": True})
contenido = documento["markdown_content"]

# Generar embedding
embedding = nvidia_embeddings_api.embed(contenido)

# Guardar en ChromaDB
chroma.add(
    id=str(documento["_id"]),
    embedding=embedding,
    metadata={
        "filename": documento["filename"],
        "created_at": documento["created_at"],
        "duration": documento["duration"]
    }
)
```

### 2. Búsqueda (Online)

```python
# Cuando el usuario pregunta:
query = "¿Cuándo se grabó la clase sobre patrones?"

# 1. Generar embedding de la pregunta
query_embedding = nvidia_embeddings_api.embed(query)

# 2. Buscar documentos similares
results = chroma.query(
    query_embedding=query_embedding,
    n_results=3  # Top 3 documentos más relevantes
)

# 3. Construir contexto con metadatos
context = f"""
Documento: {results[0]["metadata"]["filename"]}
Fecha: {results[0]["metadata"]["created_at"]}
Contenido: {results[0]["document"]}
"""

# 4. Generar respuesta con LLM
respuesta = nvidia_nim.generate(
    prompt=f"Contexto: {context}\n\nPregunta: {query}"
)
```

## 🎨 Personalización

### Cambiar modelo de embeddings

En `backend/services/rag_service.py`:

```python
self.embedding_model = "nvidia/nv-embedqa-e5-v5"  # Cambiar aquí
```

### Ajustar número de documentos recuperados

En `backend/services/rag_service.py`:

```python
def chat(self, query: str, k: int = 3):  # Cambiar k=3 a k=5
```

### Modificar system prompt

En `backend/services/rag_service.py`, busca `system_prompt` y personaliza las instrucciones.

## 🐛 Troubleshooting

### Error: "RAG Service not available"

- Verifica que `NVIDIA_EMBEDDING_API_KEY` esté configurada
- Revisa logs del backend para más detalles

### No encuentra documentos

1. Verifica que hay transcripciones en MongoDB:
   ```bash
   python scripts/test_mongo.py
   ```

2. Re-indexa los documentos:
   ```bash
   python scripts/index_documents.py
   ```

### Respuestas lentas

- El modelo `deepseek-v3.1-terminus` es grande y potente
- Considera usar un modelo más pequeño en `.env`:
  ```bash
  MODEL_NAME=meta/llama-3.1-8b-instruct
  ```

## 📊 Monitoring

### Ver documentos indexados

```python
from src.database.vector_store import VectorStore

vs = VectorStore()
count = len(vs.collection.get()['ids'])
print(f"Documentos indexados: {count}")
```

### Probar búsqueda directamente

```python
from backend.services.rag_service import RagService

service = RagService()
results = service.chat("¿De qué trata mi última clase?")
print(results["answer"])
```

## 🚀 Próximas Mejoras

- [ ] Historial de conversación persistente
- [ ] Citación automática de fuentes
- [ ] Búsqueda con filtros (fecha, duración, tema)
- [ ] Exportar conversaciones a markdown
- [ ] Modo "experto" con ajuste de parámetros

## 📚 Referencias

- [Vercel AI SDK](https://sdk.vercel.ai/)
- [NVIDIA NIM](https://build.nvidia.com/)
- [ChromaDB](https://www.trychroma.com/)
- [FastAPI Streaming](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)

---

¿Dudas? Revisa los logs del backend (`uvicorn`) y frontend (`pnpm dev`).
