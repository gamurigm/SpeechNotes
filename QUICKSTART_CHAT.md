# 🚀 Inicio Rápido - Chat Semántico

## ⚡ Pasos para empezar

### 1️⃣ Configurar variables de entorno

Verifica que tu `.env` tenga:

```bash
NVIDIA_EMBEDDING_API_KEY=nvapi-xxxxx  # Para embeddings
NVIDIA_API_KEY=nvapi-xxxxx             # Para generación
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=agent_knowledge_base
```

### 2️⃣ Indexar documentos (solo primera vez)

```bash
# Desde la raíz del proyecto
python scripts/index_documents.py
```

**Salida esperada:**
```
============================================================
Indexando documentos de MongoDB a ChromaDB
============================================================

🔧 Inicializando RAG Service...
📚 Indexando documentos de MongoDB...

✅ ¡Éxito! Se indexaron 5 documentos nuevos
📊 Total de documentos en vector store: 5
```

### 3️⃣ Iniciar servicios

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:socket_app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd web
pnpm dev
```

### 4️⃣ Usar el chat

Abre: **http://localhost:3006/dashboard/chat**

## 💬 Preguntas de prueba

1. "¿De qué trata la clase de análisis y diseño?"
2. "¿Cuándo se grabó la última clase?"
3. "Resume los patrones de diseño que expliqué"

## 🔄 Re-indexar después de nuevas grabaciones

Cada vez que grabes nuevas clases:

```bash
python scripts/index_documents.py
```

Solo indexará los documentos nuevos (no duplica).

## 🐛 Si algo falla

### Backend no inicia
```bash
# Verifica dependencias
cd backend
pip install -r requirements.txt

# Verifica MongoDB
python scripts/test_mongo.py
```

### Frontend no carga el chat
```bash
# Reinstala dependencias
cd web
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### "No encontré información relevante"

1. Verifica que hay docs indexados:
   ```bash
   python -c "from src.database.vector_store import VectorStore; vs = VectorStore(); print(f'Docs: {len(vs.collection.get()[\"ids\"])}')"
   ```

2. Si retorna 0, re-indexa:
   ```bash
   python scripts/index_documents.py
   ```

---

📚 **Documentación completa:** `docs/CHAT_SEMANTIC_SEARCH.md`
