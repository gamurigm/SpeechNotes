# 📝 TAREAS SpeechNotes

Este documento centraliza el progreso y las tareas pendientes del proyecto.

---

## ✅ Completado

### 🛠️ Infraestructura y Monitoreo
- [x] **Integración de Logfire** (Instrumentación de Pydantic AI y FastAPI) - **Hecho [2026-01-28]**
- [x] **Configuración de Entorno de Trazado** (SDK, Auth and Initialization) - **Hecho [2026-01-28]**

### 🎙️ Reconocimiento de Voz (ASR)
- [x] **Investigación de Riva / Canary-1b-asr** - **Hecho [2026-01-28]**
- [x] **Instalación y Prueba de NVIDIA Riva Client** - **Hecho [2026-01-28]**
- [x] **Clonación y Configuración de Clientes Python (NVIDIA)** - **Hecho [2026-01-28]**

### 🎨 UI / UX (Mejoras Visuales)
- [x] **Corrección de Contraste en Temas Claros** (Pure Light) - **Hecho [2026-01-28]**
- [x] **Mejora de Glassmorphism** (Bordes dinámicos y sombras) - **Hecho [2026-01-28]**
- [x] **Eliminación de Degradados Oscuros Forzados** - **Hecho [2026-01-28]**
- [x] **Refinamiento de Layout del Dashboard** (Contenedores flotantes) - **Hecho [2026-01-28]**
- [x] **Rediseño de Sidebar Toggle** (Efecto fantasma y hover) - **Hecho [2026-01-28]**
- [x] **Rediseño de Herramienta de Tipografía** (Ubicación en header e indicador pulsante) - **Hecho [2026-01-28]**

---

## 📋 Notas de Referencia (ASR Offline)

### Comando para Transcripción (Riva)
```bash
python python-clients/scripts/asr/transcribe_file_offline.py \
    --server grpc.nvcf.nvidia.com:443 --use-ssl \
    --metadata function-id "b0e8b4a5-217c-40b7-9b96-17d84e666317" \
    --metadata "authorization" "Bearer [API_KEY]" \
    --language-code en-US \
    --input-file <audio_file>
```