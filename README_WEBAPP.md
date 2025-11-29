# SpeechNotes - Sistema de Transcripción en Tiempo Real

## Arquitectura

- **Backend**: FastAPI + Socket.IO (Python) - Puerto 8000
- **Frontend**: Next.js + React + TypeScript - Puerto 3000
- **Base de Datos**: MongoDB - Puerto 27017
- **Comunicación en Tiempo Real**: Socket.IO

## Instalación

### 1. Backend (Python)

```bash
# Instalar dependencias
pip install -r backend/requirements.txt

# Verificar que MongoDB esté corriendo
# El sistema usa MongoDB en localhost:27017
```

### 2. Frontend (Next.js)

```bash
cd web
npm install
```

## Ejecución

### Terminal 1: Backend

```bash
# Desde la raíz del proyecto
python backend/main.py
```

El backend estará disponible en `http://localhost:8000`

### Terminal 2: Frontend

```bash
cd web
npm run dev
```

El frontend estará disponible en `http://localhost:3000`

## Uso

1. Abre `http://localhost:3000/dashboard` en tu navegador
2. Haz clic en el botón azul de micrófono para comenzar a grabar
3. Habla y verás la transcripción aparecer en tiempo real en la barra lateral izquierda
4. Haz clic en el botón rojo para detener la grabación
5. El sistema procesará automáticamente la transcripción y la mostrará formateada en el panel principal
6. Puedes editar el contenido haciendo clic en "Editar"

## Estructura del Proyecto

```
.
├── backend/
│   ├── main.py                 # Servidor FastAPI + Socket.IO
│   ├── routers/
│   │   └── transcriptions.py   # API REST
│   └── services/
│       └── socket_handler.py   # Eventos Socket.IO
├── web/
│   ├── app/
│   │   └── dashboard/
│   │       ├── page.tsx        # Página principal
│   │       └── components/     # Componentes React
│   ├── hooks/
│   │   └── useRecording.ts     # Hook de grabación
│   └── utils/
│       ├── socket.ts           # Cliente Socket.IO
│       └── api-client.ts       # Cliente REST API
└── src/
    ├── database/
    │   └── mongo_manager.py    # Gestión MongoDB
    └── agent/
        ├── transcription_ingestor.py
        ├── transcription_analyzer.py
        └── document_generator.py
```

## Flujo de Datos

1. **Grabación**: El navegador captura audio del micrófono
2. **Streaming**: Audio se envía en chunks via Socket.IO al backend
3. **Transcripción**: Backend procesa y transcribe (placeholder por ahora)
4. **Tiempo Real**: Texto transcrito se envía de vuelta al navegador
5. **Almacenamiento**: Al detener, se guarda en MongoDB
6. **Procesamiento**: El sistema analiza y estructura el contenido
7. **Visualización**: Se muestra el Markdown formateado

## Próximos Pasos

- [ ] Integrar Whisper API real para transcripción
- [ ] Mejorar detección de temas con LLM
- [ ] Añadir exportación a PDF
- [ ] Implementar historial de sesiones
- [ ] Añadir autenticación

## Troubleshooting

### MongoDB no conecta
- Verifica que MongoDB esté corriendo: `mongod --version`
- Revisa el puerto en `.env`: `MONGO_URI=mongodb://localhost:27017/`

### Socket.IO no conecta
- Verifica que el backend esté corriendo en puerto 8000
- Revisa la consola del navegador para errores de CORS

### Micrófono no funciona
- Asegúrate de dar permisos al navegador
- Usa HTTPS o localhost (requerido por navegadores modernos)
