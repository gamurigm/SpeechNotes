# 🎯 Formateador de Transcripciones con Minimax M2

Sistema completo para formatear transcripciones usando IA (Minimax M2) con arquitectura Backend (Python FastAPI) + Frontend (Next.js).

## 🏗️ Arquitectura

```
┌─────────────────────────────────────┐
│  Next.js Frontend (web/)            │
│  - UI para seleccionar archivos     │
│  - Visualización de progreso        │
│  - WebSocket para updates en vivo   │
└──────────────┬──────────────────────┘
               │ HTTP + WebSocket
               ↓
┌─────────────────────────────────────┐
│  FastAPI Backend (backend/)         │
│  - API REST: /api/format/*          │
│  - WebSocket: /api/format/ws/{id}   │
│  - FormatterAgent (durable)         │
│    ├── Read Step (con retry)        │
│    ├── Format Step (Minimax M2)     │
│    └── Save Step (con backup)       │
└─────────────────────────────────────┘
```

## 📦 Archivos Creados

### Backend (Python)
- `backend/services/formatter_agent.py` - Agente durable con retry logic
- `backend/routers/formatter.py` - API endpoints y WebSocket
- `backend/main.py` - Actualizado con ruta del formatter

### Frontend (Next.js)
- `web/app/formatter/page.tsx` - UI completa con selección y progreso

## 🚀 Instalación y Uso

### 1. Configurar Backend

```bash
# Navegar al directorio backend
cd backend

# Asegurar que .env tiene las credenciales de Minimax
# Ya están configuradas:
# MINIMAX_API_KEY=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
# MINIMAX_BASE_URL=https://integrate.api.nvidia.com/v1
# MINIMAX_MODEL_NAME=minimaxai/minimax-m2

# Iniciar servidor (si no está corriendo)
uvicorn main:socket_app --host 0.0.0.0 --port 8000 --reload
```

### 2. Configurar Frontend

```bash
# Navegar al directorio web
cd web

# Instalar dependencias si es necesario
npm install

# Iniciar servidor de desarrollo
npm run dev
```

### 3. Usar la Aplicación

1. **Abrir en el navegador**: http://localhost:3006/formatter

2. **Seleccionar archivos**:
   - Verás todos los archivos `.md` disponibles en `notas/`
   - Usa los checkboxes para seleccionar los que quieras formatear
   - O usa "Seleccionar todos"

3. **Iniciar formateo**:
   - Click en "✨ Formatear X archivo(s)"
   - El progreso se mostrará en tiempo real en el panel derecho

4. **Ver resultados**:
   - Los archivos formateados se guardan como `*_formatted.md` en `notas/`
   - Los originales se respaldan como `*.md.original`

## ✨ Características Implementadas

### Backend
- ✅ **Agente Durable**: Steps con retry automático (exponential backoff)
- ✅ **API REST**: Listar archivos, iniciar jobs, consultar estado
- ✅ **WebSocket Streaming**: Updates de progreso en tiempo real
- ✅ **Job Queue**: Manejo de múltiples formateos concurrentes
- ✅ **Error Handling**: Captura y reporte de errores por archivo

### Frontend
- ✅ **UI Moderna**: Diseño limpio con Tailwind CSS
- ✅ **Selección Múltiple**: Checkboxes para elegir archivos
- ✅ **Progreso en Vivo**: Conexión WebSocket para updates instantáneos
- ✅ **Estados Visuales**: Iconos y colores según el estado
- ✅ **Metadata Display**: Muestra fecha, palabras, tamaño de archivos
- ✅ **Resumen Final**: Contador de exitosos/fallidos

## 🔍 API Endpoints

### GET /api/format/files
Lista archivos disponibles para formatear
```json
[
  {
    "name": "transcripcion_20251117_101413.md",
    "path": "notas/transcripcion_20251117_101413.md",
    "size": 45678,
    "modified": "2024-12-07T10:30:00",
    "metadata": {
      "fecha": "2025-11-17",
      "palabras": "2,609"
    }
  }
]
```

### POST /api/format/start
Inicia un job de formateo
```json
{
  "files": ["notas/file1.md", "notas/file2.md"],
  "output_dir": "notas"
}
```

Respuesta:
```json
{
  "job_id": "uuid-here",
  "total_files": 2,
  "ws_url": "/ws/uuid-here"
}
```

### WebSocket /api/format/ws/{job_id}
Stream de progreso en tiempo real

Mensajes:
```json
{
  "job_id": "uuid",
  "current": 1,
  "total": 3,
  "file_name": "transcripcion.md",
  "status": "formatting",
  "timestamp": "2024-12-07T10:30:00"
}
```

Estados: `reading`, `formatting`, `saving`, `completed`, `error`

### GET /api/format/job/{job_id}
Consultar estado de un job

## 🛠️ Testing

### Test Manual

1. **Backend funcionando**: 
   ```bash
  curl http://localhost:8001/api/format/files
   ```

2. **Iniciar formateo manual**:
   ```bash
  curl -X POST http://localhost:8001/api/format/start \
     -H "Content-Type: application/json" \
     -d '{"files":["notas/transcripcion_20251117_101413.md"]}'
   ```

3. **Ver progreso** (requiere cliente WebSocket o usar la UI)

### Test desde UI

1. Abrir http://localhost:3006/formatter
2. Seleccionar 1-2 archivos
3. Click en "Formatear"
4. Verificar que aparezcan los updates en tiempo real
5. Verificar que se creen los archivos `*_formatted.md` en `notas/`

## 🐛 Troubleshooting

### Backend no lista archivos
- Verificar que el directorio `notas/` existe
- Verificar que hay archivos `.md` (no `_formatted.md` ni `.original.md`)

### WebSocket no conecta
- Verificar que el backend está corriendo en puerto 8000
- Verificar CORS configurado correctamente
- Revisar consola del navegador para errores

### Minimax devuelve error
- Verificar que `MINIMAX_API_KEY` está configurada
- Verificar que la key es válida (no expirada)
- Revisar límites de rate de la API

### Archivos no se guardan
- Verificar permisos de escritura en `notas/`
- Revisar logs del backend para errores específicos

## 📊 Observabilidad

El sistema incluye logging detallado:

**Backend**:
```python
print(f"📖 Reading: {file_name}")
print(f"🤖 Formatting with Minimax M2: {file_name}")  
print(f"💾 Saving: {file_name}")
```

**Frontend**: Consola del navegador muestra:
- Conexión/desconexión de WebSocket
- Mensajes recibidos
- Errores de red

## 🔐 Seguridad

⚠️ **IMPORTANTE**: 
- La API key de Minimax está en `.env` - NO commitear este archivo
- Rotar la key periódicamente
- Considerar autenticación para endpoints de formateo en producción

## 🚀 Próximos Pasos (Opcional)

- [ ] Autenticación JWT para API endpoints
- [ ] Persistencia de jobs en base de datos
- [ ] Dashboard de historial de formateos
- [ ] Soporte para formatear desde MongoDB directamente
- [ ] Export de logs de jobs
- [ ] Cancelación de jobs en progreso
- [ ] Preview del formato antes de guardar

## 📝 Notas

- Los archivos originales se respaldan automáticamente (`.md.original`)
- Los archivos formateados tienen sufijo `_formatted.md`
- El sistema maneja reintentos automáticos (3 intentos para format, 2 para read/save)
- El contenido se trunca a 15,000 caracteres para evitar límites de tokens
