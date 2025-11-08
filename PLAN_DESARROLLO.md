# 📝 Plan de Desarrollo: App de Notas con STT + RAG

## Fase 1: Validación de STT (Whisper) ✅
- [x] Configurar Whisper API
- [x] Probar transcripción en español
- [x] Crear helper script para transcripciones
- [ ] Crear test de transcripción para verificar calidad

## Fase 2: Backend Core (Próximos pasos)
### 2.1 Setup de Base de Datos
- [ ] Configurar PostgreSQL (local o cloud)
- [ ] Diseñar schema para notas (id, titulo, fecha, usuario, tags, estado)
- [ ] Crear migraciones iniciales

### 2.2 Storage para Audio y Markdown
- [ ] Configurar S3 o almacenamiento local
- [ ] Crear estructura de carpetas (audio/, notas/)
- [ ] Implementar upload de archivos

### 2.3 Vector Database (Pinecone)
- [ ] Crear cuenta en Pinecone (free tier)
- [ ] Configurar índice para embeddings
- [ ] Implementar generación de embeddings
- [ ] Implementar búsqueda semántica

## Fase 3: RAG Pipeline
### 3.1 Generación de Embeddings
- [ ] Integrar modelo de embeddings (OpenAI o alternativa)
- [ ] Procesar transcripciones para crear embeddings
- [ ] Guardar en Vector DB

### 3.2 Generación de Notas
- [ ] Configurar GPT-4 o Claude API
- [ ] Crear prompts para generar notas estructuradas
- [ ] Pipeline: transcripción → contexto (RAG) → nota markdown

### 3.3 Búsqueda Contextual
- [ ] Implementar búsqueda semántica
- [ ] Ranking por similitud
- [ ] Filtros (fecha, tags, usuario)

## Fase 4: API Backend (FastAPI/Flask)
- [ ] Crear endpoints:
  - POST /audio/upload
  - GET /notes/{id}
  - GET /notes/search?q=...
  - POST /notes/generate
- [ ] Autenticación básica
- [ ] Rate limiting

## Fase 5: Frontend (Opcional - según tu curso)
- [ ] Interfaz de grabación de audio
- [ ] Lista de notas
- [ ] Búsqueda con autocompletado
- [ ] Visualización de nota individual

---

## 🎯 Paso Inmediato: ¿Qué hacemos ahora?

Propongo empezar con **Fase 2.1 (Base de Datos)** o **Fase 2.2 (Storage local)** 
para tener donde guardar las transcripciones.

**Opción rápida (sin dependencias externas):**
1. Crear un backend simple con FastAPI
2. Usar SQLite local para metadata
3. Guardar archivos en disco local
4. Probar todo el flujo sin RAG primero

**¿Qué prefieres?**
- A) Empezar con backend básico (FastAPI + SQLite local)
- B) Configurar PostgreSQL y servicios cloud primero
- C) Implementar RAG pipeline directamente
- D) Otro enfoque

Dime qué te parece y arrancamos 🚀
