# Arquitectura del Sistema de Chat Semántico

## Diagrama de Componentes

```mermaid
graph TB
    subgraph "Frontend - Next.js"
        UI[Chat UI<br/>dashboard/chat/page.tsx]
        API[API Route<br/>app/api/chat/route.ts]
    end
    
    subgraph "Backend - FastAPI"
        Router[Chat Router<br/>routers/chat.py]
        RAG[RAG Service<br/>services/rag_service.py]
        VectorDB[(ChromaDB<br/>Vector Store)]
    end
    
    subgraph "External Services"
        NVIDIA_EMB[NVIDIA Embeddings<br/>nv-embedqa-e5-v5]
        NVIDIA_LLM[NVIDIA NIM<br/>deepseek-v3.1]
        MongoDB[(MongoDB<br/>Transcriptions)]
    end
    
    UI -->|POST /api/chat| API
    API -->|POST /api/chat/stream| Router
    Router -->|chat_stream| RAG
    
    RAG -->|query_embedding| NVIDIA_EMB
    RAG -->|search| VectorDB
    RAG -->|generate| NVIDIA_LLM
    
    MongoDB -.->|index_documents| VectorDB
    
    style UI fill:#3b82f6
    style API fill:#60a5fa
    style Router fill:#f59e0b
    style RAG fill:#f97316
    style VectorDB fill:#10b981
    style NVIDIA_EMB fill:#8b5cf6
    style NVIDIA_LLM fill:#ec4899
    style MongoDB fill:#06b6d4
```

## Flujo de Datos: Pregunta del Usuario

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant BE as Backend
    participant VS as Vector Store
    participant NV as NVIDIA API
    participant LLM as NVIDIA NIM

    U->>FE: "¿Cuándo fue la clase X?"
    FE->>BE: POST /api/chat/stream
    BE->>NV: Embed query
    NV-->>BE: query_embedding
    BE->>VS: Search similar docs
    VS-->>BE: Top 3 documents + metadata
    BE->>BE: Build context with dates
    BE->>LLM: Generate(context + query)
    loop Streaming
        LLM-->>BE: chunk
        BE-->>FE: SSE: chunk
        FE-->>U: Render chunk
    end
    LLM-->>BE: Done
    BE-->>FE: SSE: done
```

## Flujo de Indexación

```mermaid
sequenceDiagram
    participant S as Script
    participant M as MongoDB
    participant R as RAG Service
    participant NV as NVIDIA Embeddings
    participant VS as ChromaDB

    S->>M: Find processed docs
    M-->>S: List of transcriptions
    
    loop For each doc
        S->>R: index_documents_from_mongo()
        R->>M: Get doc content
        M-->>R: Full markdown + metadata
        R->>NV: Generate embedding
        NV-->>R: embedding vector
        R->>VS: Store(id, embedding, metadata)
        VS-->>R: Success
    end
    
    S-->>S: Print summary
```

## Estructura de Datos

### Documento en MongoDB

```json
{
  "_id": ObjectId("..."),
  "filename": "transcripcion_20251207_143022.md",
  "processed": true,
  "created_at": "2025-12-07T14:30:22",
  "duration": 1234.5,
  "markdown_content": "# Clase de Análisis...",
  "ingested_at": "2025-12-07T14:35:00"
}
```

### Embedding en ChromaDB

```json
{
  "id": "675a1b2c3d4e5f6g7h8i9j0",
  "embedding": [0.123, -0.456, 0.789, ...],  // 1024 dimensions
  "metadata": {
    "filename": "transcripcion_20251207_143022.md",
    "created_at": "2025-12-07T14:30:22",
    "duration": 1234.5,
    "source": "mongodb",
    "fecha_formateada": "07 de Diciembre de 2025, 14:30:22"
  },
  "document": "# Clase de Análisis...\n\n..."  // Full content
}
```

### Mensaje de Chat (Frontend)

```typescript
{
  id: "msg_123",
  role: "user" | "assistant",
  parts: [
    { type: "text", text: "¿Cuándo fue la clase X?" }
  ]
}
```

### Request al Backend

```json
{
  "messages": [
    { "role": "user", "content": "¿Cuándo fue la clase X?" }
  ]
}
```

### Response (SSE Stream)

```
data: {"content": "La", "done": false}

data: {"content": " clase", "done": false}

data: {"content": " fue el", "done": false}

data: {"content": " 7 de diciembre", "done": false}

data: {"done": true}

```

## Componentes Clave

### RAG Service Pipeline

```python
def chat_stream(query):
    # 1. Retrieve
    query_emb = get_embedding(query, type="query")
    results = vector_store.search(query_emb, k=3)
    
    # 2. Augment
    context = build_context(results)  # Include dates!
    
    # 3. Generate
    prompt = f"Context: {context}\nQ: {query}\nA:"
    for chunk in llm.stream_generate(prompt):
        yield chunk
```

### Context Building

```python
def _prepare_context_and_sources(query, k=3):
    results = vector_store.query_similar(query_embedding, n_results=k)
    
    context_parts = []
    for doc, meta in results:
        # Format with emojis for better UX
        info = f"""
📄 Documento: {meta['filename']}
📅 Fecha: {format_date(meta['created_at'])}
⏱️ Duración: {meta['duration']}s

Contenido:
{doc}
"""
        context_parts.append(info)
    
    return "\n\n---\n\n".join(context_parts)
```

## Tecnologías Utilizadas

| Componente | Tecnología | Propósito |
|------------|-----------|-----------|
| Frontend UI | Next.js 16 + React 19 | Interfaz moderna |
| Chat Hook | Vercel AI SDK | Manejo de streaming |
| Backend API | FastAPI | REST + SSE |
| Vector DB | ChromaDB | Almacén de embeddings |
| Embeddings | NVIDIA nv-embedqa-e5-v5 | Vectorización semántica |
| LLM | NVIDIA DeepSeek-V3.1 | Generación de texto |
| Document Store | MongoDB | Persistencia de docs |

## Métricas de Performance

| Operación | Tiempo Promedio |
|-----------|-----------------|
| Embedding query | ~200ms |
| Vector search (k=3) | ~50ms |
| LLM first token | ~500ms |
| LLM full response | ~2-5s |
| **Total (perceived)** | **~1s** (streaming) |

## Escalabilidad

### Límites Actuales
- **Documentos**: ~1000 docs (ChromaDB local)
- **Consultas simultáneas**: ~10 usuarios
- **Tamaño de contexto**: 3 documentos × ~2KB = ~6KB

### Para Escalar
- [ ] ChromaDB → Pinecone/Weaviate (cloud)
- [ ] FastAPI → Multiple workers (Gunicorn)
- [ ] Redis cache para embeddings frecuentes
- [ ] CDN para frontend
