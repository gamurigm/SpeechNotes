# 🎙️ SpeechNotes — AI-Powered Real-Time Transcription System

![Dashboard](./docs/assets/screenshots/appCap-ultimate1.png)

**SpeechNotes** es un sistema de transcripción de voz en tiempo real, escalable y modular, que captura, procesa y almacena audio desde navegadores web, integrando motores de reconocimiento de voz avanzados y formateo inteligente con IA.

---

## 📁 Estructura del Proyecto

```
SpeechNotes/
├── backend/                    # API REST (FastAPI) + Socket.IO
│   ├── main.py                 # Entry point del servidor
│   ├── routers/                # Endpoints REST
│   ├── services/               # Lógica de negocio (audio, VAD, socket)
│   └── repositories/           # Capa de persistencia (MongoDB)
│
├── web/                        # Frontend (Next.js 14 + React 18)
│   ├── app/                    # App Router de Next.js
│   ├── components/             # Componentes React reutilizables
│   └── services/               # Servicios cliente (ApiClient, etc.)
│
├── src/                        # Core compartido
│   ├── core/                   # Factories, configuración
│   └── transcription/          # Formatters, motores de transcripción
│
├── config/                     # Archivos de configuración del sistema
├── scripts/                    # Scripts de utilidad y automatización
├── legacy/                     # Código legacy (referencia)
├── knowledge_base/             # Base de conocimiento extraída
│
├── docs/                       # Documentación del proyecto
│   ├── informe_arquitectura.pdf  # 📄 Informe final (22 páginas)
│   ├── patrones_diseno.md        # Documentación de patrones GoF
│   ├── diagramas/                # Diagramas UML (PNG generados)
│   └── assets/                   # Screenshots y recursos visuales
│
├── docker-compose.yml          # Orquestación de contenedores
├── .env.example                # Variables de entorno de ejemplo
├── run_all.ps1                 # Script de inicio rápido (Windows)
└── README.md                   # Este archivo
```

---

## ⚡ Funcionalidades Principales

| Funcionalidad | Descripción |
|---|---|
| 🎤 **Transcripción en Tiempo Real** | NVIDIA Riva + VAD con latencia mínima vía WebSockets |
| 🧠 **IA Dual** | Kimi K2 (razonamiento profundo) + Minimax (formateo) |
| 🔎 **Búsqueda Semántica** | Motor Llama 3.2 Nemoretriever para búsqueda por significado |
| 🎛️ **Procesamiento de Audio** | Normalización, eliminación de silencios, aceleración |
| 🎨 **UI Glassmorphism** | Interfaz premium con modo oscuro/claro y micro-animaciones |

---

## 🚀 Inicio Rápido

### Requisitos Previos
- Python 3.10+
- Node.js 18+ / pnpm
- MongoDB
- NVIDIA API Key (para Riva STT)

### Configuración

1. **Copiar variables de entorno:**
   ```bash
   cp .env.example .env
   # Editar .env con: NVIDIA_API_KEY, MONGO_URI
   ```

2. **Iniciar los servicios:**
   ```bash
   # Terminal 1: Backend
   python backend/main.py

   # Terminal 2: Frontend
   cd web && pnpm install && pnpm dev
   ```

3. **Abrir el navegador** en `http://localhost:3000` y presionar el micrófono 🎤

---

## 🏗️ Arquitectura y Patrones de Diseño

El proyecto implementa una **arquitectura por capas** (Clean Architecture) con los siguientes patrones GoF:

### Patrones Creacionales
| Patrón | Componente | Archivo |
|---|---|---|
| **Singleton** | `ApiClient` | `web/services/ApiClient.ts` |
| **Factory Method** | `FormatterFactory` | `src/transcription/formatters.py` |
| **Abstract Factory** | `TranscriptionEnvironmentFactory` | `src/core/environment_factory.py` |

### Patrones Estructurales
| Patrón | Componente | Archivo |
|---|---|---|
| **Adapter** | `AudioProcessorPort` | `backend/services/audio_service.py` |
| **Facade** | `register_socket_events` / `ApiClient` | `backend/services/socket_handler.py` |
| **Repository** | `TranscriptionRepository` | `backend/repositories/` |

### Patrones Comportamentales
| Patrón | Componente | Archivo |
|---|---|---|
| **Strategy** | `VADStrategy` | `backend/services/vad_service.py` |
| **State** | `VADState` (Máquina de Estados) | `backend/services/vad_service.py` |
| **Observer** | Socket.IO Events | `backend/services/socket_handler.py` |

📄 **Documentación completa:** [`docs/informe_arquitectura.pdf`](./docs/informe_arquitectura.pdf) (22 páginas con diagramas UML)

---

## 🐳 Docker

```bash
docker-compose up --build
```

Ver [DOCKER.md](./DOCKER.md) para instrucciones detalladas.

---

## 📊 Stack Tecnológico

| Capa | Tecnología | Rol |
|---|---|---|
| Frontend | Next.js 14 + React 18 | Interfaz de usuario |
| Backend | FastAPI + Socket.IO | API REST y comunicación en tiempo real |
| Motor STT | NVIDIA Riva | Reconocimiento de voz |
| Base de datos | MongoDB | Persistencia documental |
| IA | Kimi K2-Thinking | Formateo inteligente de notas |
| Audio | FFmpeg + pydub | Conversión y normalización |

---

> *"El futuro de tomar notas no es escribir, es escuchar."* — **SpeechNotes Team** 🍌
