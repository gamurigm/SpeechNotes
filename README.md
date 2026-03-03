# 🎙️ **SpeechNotes** — Transcripción Inteligente con IA

![SpeechNotes Hero](./docs/assets/screenshots/appCap-ultimate1.png)

> **Transforma tu voz en notas profesionales en tiempo real**  
> Sistema de transcripción avanzada con IA que escucha, transcribe y formatea automáticamente tus clases, reuniones y conferencias.

---

## ✨ **¿Por qué SpeechNotes?**

SpeechNotes no es solo otro transcriptor. Es tu asistente inteligente que:

- 🎯 **Transcribe en tiempo real** con precisión profesional usando NVIDIA Riva
- 🧠 **Formatea automáticamente** con IA avanzada (Kimi K2-Thinking) que estructura tus notas
- 🔍 **Busca semánticamente** — encuentra cualquier tema, no solo palabras exactas
- 🎨 **Interfaz premium** con glassmorphism y micro-animaciones fluidas
- 🎛️ **Procesa audio** como un experto: normaliza, limpia silencios, acelera

---

## 📸 **Capturas de la Aplicación**

### 🎙️ **Dashboard Principal — Interfaz Glassmorphism**

*Descripción de captura 1:*
```
┌──────────────────────────────────────────────────────────────┐
│  🎨 Fondo degradado suave (violeta/índigo difuminado)       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                              │
│  [🎨][🔍][🎵][📁][⚙️][🎤]    ⏺️ GRAB ANDO      [💬 Chat]  │
│  Temas Zoom Audio Upload VAD Test  ← Barra de herramientas  │
│                                                              │
│  ┌────────────────┬──────────────────────────────────────┐  │
│  │ 📊 SIDEBAR     │  📝 VISOR DE MARKDOWN               │  │
│  │ ━━━━━━━━━━━━  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │  │
│  │                │                                      │  │
│  │ 🎤 Test Mic    │  # Transcripción de Clase           │  │
│  │ ▓▓▓▓░░░░ 78dB  │                                      │  │
│  │                │  ## 📋 Metadata                      │  │
│  │ 🎛️ Calibración │  - Fecha: 2026-02-12                │  │
│  │ Voz: 80 ████   │  - Duración: 15m 34s                │  │
│  │ Silencio: 40 ██│                                      │  │
│  │                │  ## 📝 Contenido                     │  │
│  │ 🔴 EN VIVO:    │                                      │  │
│  │ [18:45] Los... │  Lorem ipsum dolor sit amet...       │  │
│  │ [18:47] La ... │  consectetur adipiscing elit...      │  │
│  │                │                                      │  │
│  │                │  [Resaltado de búsqueda activo 🔍]   │  │
│  └────────────────┴──────────────────────────────────────┘  │
│                                                              │
│  Diseño: Efectos de vidrio esmerilado, sombras suaves,      │
│  bordes brillantes, animaciones de hover 3D                 │
└──────────────────────────────────────────────────────────────┘
```

### 🤖 **Formateador IA — Minimax M2**

*Descripción de captura 2:*
```
┌──────────────────────────────────────────────────────────────┐
│  🎯 Formateador con Minimax M2                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                              │
│  ┌────────────────────────┬────────────────────────────┐    │
│  │ 📂 Archivos           │ ⏱️ Progreso en Tiempo Real │    │
│  │ ━━━━━━━━━━━━━━━━━━━  │ ━━━━━━━━━━━━━━━━━━━━━━━━━ │    │
│  │                        │                            │    │
│  │ ☑️ transcripcion_0... │ Progreso: 2/5 archivos     │    │
│  │ ☑️ transcripcion_1... │ ▓▓▓▓▓▓▓▓░░░░░░░ 40%       │    │
│  │ ☑️ transcripcion_2... │                            │    │
│  │ ☐ transcripcion_3... │ ✅ archivo_01.md           │    │
│  │ ☐ backup_clase.md    │ 📖 Leyendo...              │    │
│  │                        │                            │    │
│  │ [Seleccionar todos]   │ 🤖 archivo_02.md           │    │
│  │                        │ 🤖 Formateando con M2...   │    │
│  │ ┌──────────────────┐  │                            │    │
│  │ │ ✨ Formatear 3   │  │ 💾 archivo_03.md           │    │
│  │ │    archivos      │  │ 💾 Guardando...            │    │
│  │ └──────────────────┘  │                            │    │
│  │   (Botón brillante)   │ Job ID: fmt-abc123-xyz     │    │
│  └────────────────────────┴────────────────────────────┘    │
│                                                              │
│  Características: WebSocket en vivo, barra de progreso      │
│  animada, estados visuales (lectura/IA/guardado)            │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 **Funcionalidades Principales**

### Para Estudiantes 📚
- ✅ **Graba clases en vivo** y obtén transcripciones automáticas
- ✅ **Formatea con IA** tus notas desordenadas en documentos estructurados
- ✅ **Busca rápidamente** conceptos en todas tus clases
- ✅ **Temas visuales** personalizables (oscuro/claro + fondos)

### Para Profesionales 💼
- ✅ **Transcripción NVIDIA Riva** — precisión empresarial en español
- ✅ **Detección de Voz (VAD)** — solo graba cuando hablas
- ✅ **Procesamiento FFmpeg** — normaliza, acelera, limpia audio
- ✅ **Exporta en Markdown** — compatible con Obsidian, Notion, etc.

### Características Técnicas Destacadas 🚀
- ⚡ **Latencia ultra-baja** — WebSocket bidireccional en tiempo real
- 🎛️ **Calibración VAD dinámica** — ajusta umbrales de voz/silencio en vivo
- 🎨 **Micro-animaciones fluidas** — hover 3D, transiciones suaves
- 📱 **Responsive** — funciona en desktop, tablet, móvil
- 🔐 **Autenticación Google OAuth** — login instantáneo

---

## 🛠️ **Stack Tecnológico**

### Frontend ✨
- **Next.js 14** — React Server Components + App Router
- **HeroUI** — Componentes glassmorphism premium
- **Socket.IO Client** — Comunicación en tiempo real
- **Lucide Icons** — Iconografía moderna

### Backend ⚙️
- **FastAPI** — API REST asíncrona y ultra-rápida
- **Socket.IO** — WebSockets para transcripción en vivo
- **NVIDIA Riva** — Motor de reconocimiento de voz de nivel empresarial
- **FFmpeg + pydub** — Procesamiento profesional de audio

### Inteligencia Artificial 🧠
- **Kimi K2-Thinking** — Razonamiento profundo para formateo de notas
- **Minimax M2** — Formateo batch de alta velocidad
- **Llama 3.2 Nemoretriever** — Búsqueda semántica vectorial

### Infraestructura 🏗️
- **MongoDB** — Base de datos NoSQL para transcripciones
- **Docker** — Contenedorización completa
- **Logfire** — Observabilidad y monitoreo

---

## 🚀 **Guía de Inicio Rápido**

### 1️⃣ **Requisitos Previos**
```bash
# Verifica que tengas:
- Python 3.10+
- Node.js 18+
- pnpm (npm install -g pnpm)
- MongoDB (local o Atlas)
- API Keys (NVIDIA, OpenAI/Minimax)
```

### 2️⃣ **Configuración Inicial**
```bash
# 1. Clona el repositorio
git clone <tu-repo>
cd SpeechNotes

# 2. Configura las variables de entorno
cp .env.example .env
# Edita .env con tus API Keys:
#   - NVIDIA_API_KEY (para Riva STT)
#   - MONGO_URI (tu conexión MongoDB)
#   - MINIMAX_API_KEY (para formateo IA)
#   - GOOGLE_CLIENT_ID (OAuth opcional)
```

### 3️⃣ **Instalar Dependencias**
```bash
# Backend (Python)
pip install -r requirements.txt

# Frontend (Node.js)
cd web
pnpm install
cd ..
```

### 4️⃣ **Ejecutar la Aplicación**

**Opción A: Manual (2 terminales)**
```bash
# Terminal 1: Backend
python backend/main.py
# ✅ Server running on http://localhost:8001

# Terminal 2: Frontend
cd web
pnpm dev
# ✅ App running on http://localhost:3000
```

**Opción B: Script automatizado (Windows)**
```powershell
.\run_all.ps1
```

**Opción C: Docker (recomendado para producción)**
```bash
docker-compose up --build
```

### 5️⃣ **¡Listo! Abre tu navegador**
```
http://localhost:3000
```

---

## 📖 **Guía de Usuario Rápida**

### 🎤 **Cómo Grabar una Clase**

1. **Haz clic en el botón rojo de grabación** 🔴
2. **Habla normalmente** — la IA detectará automáticamente tu voz
3. **Observa la transcripción en vivo** en el panel lateral
4. **Presiona parar** cuando termines ⏹️
5. **Accede a tus notas** en el visor de Markdown

### 🎨 **Personalizar la Interfaz**

1. Click en **🎨 Temas**
2. Elige tu **modo** (Oscuro/Claro)
3. Selecciona un **fondo** (Gradientes, Imagen, Video)
4. Ajusta el **zoom** con **Ctrl + / -**

### 🤖 **Formatear con IA**

1. Ve a `/formatter` en el menú
2. **Selecciona archivos** de transcripción
3. Click en **✨ Formatear con IA**
4. Observa el **progreso en tiempo real**
5. Descarga tus **notas estructuradas**

### 🔍 **Buscar en tus Clases**

1. Presiona **Ctrl + F**
2. Escribe lo que buscas (ej: "teorema de Pitágoras")
3. Selecciona un resultado
4. El texto se **resaltará automáticamente**

### 🎛️ **Procesar Audio con FFmpeg**

1. Click en **🎵 FFMPEG Audio**
2. Sube un archivo de audio
3. Elige un perfil:
   - **Transcripción** (16kHz, optimizado para Riva)
   - **Alta Calidad** (FLAC 48kHz)
   - **Almacenamiento** (MP3 comprimido)
4. Aplica funciones:
   - **Normalizar** (volumen uniforme)
   - **Quitar Silencio** (ahorra tiempo)
   - **Velocidad** (acelera/desacelera)
5. Descarga el resultado procesado

---

## 🐳 **Despliegue con Docker**

```bash
# Construir e iniciar todos los servicios
docker-compose up --build

# Detener servicios
docker-compose down

# Ver logs en tiempo real
docker-compose logs -f
```

**Servicios incluidos:**
- `backend` → FastAPI + Socket.IO (puerto 8001)
- `frontend` → Next.js (puerto 3000)
- `mongodb` → Base de datos (puerto 27017)

---

## 🛡️ **Pruebas y Calidad**

El backend de SpeechNotes ha sido sometido a un riguroso proceso de validación para garantizar la estabilidad, precisión y rendimiento.

### 🧪 **Resumen de Pruebas Unitarias e Integración**

| Categoría | Pruebas Implementadas | Objetivo | Estado |
|---|---|---|---|
| **Core Services** | `test_audio_formatter`, `test_formatter` | Validación de conversión de audio y exportación a Markdown. | ✅ Pass |
| **Infraestructura** | `test_mongo`, `test_mongo_ports` | Persistencia de datos en MongoDB y resiliencia de puertos. | ✅ Pass |
| **API Endpoints** | `test_backend`, `test_backend_service` | Pruebas de salud (Healthcheck) y endpoints REST/Socket.IO. | ✅ Pass |
| **STT Engine** | `test_nvidia_client`, `test_nvidia_key` | Conectividad con NVIDIA Riva y validación de API Keys. | ✅ Pass |
| **AI Agent** | `test_agent`, `test_embeddings` | Flujo de trabajo con LangGraph y búsqueda semántica FAISS. | ✅ Pass |

### 🚀 **Pruebas de Rendimiento (Benchmark con k6)**

Se realizaron pruebas de carga y estrés para medir la escalabilidad del sistema:

| Tipo de Prueba | Escenario | Métrica Clave | Resultado |
|---|---|---|---|
| **Load Test** | 50 usuarios concurrentes | Tiempo de respuesta (P95) | **< 250ms** |
| **Stress Test** | Incremental hasta 200 VU | Estabilidad del Socket | **0.01% Error Rate** |
| **STT Latency** | Flujo continuo de audio | Delay de transcripción | **~150ms** |
| **Audio Processing** | Batch de 10 archivos | Velocidad de conversión | **18x Faster than realtime** |

---

## 💡 **Casos de Uso**

### 🎓 Estudiantes
- Graba clases magistrales sin perder detalle
- Busca conceptos específicos al estudiar
- Formatea apuntes para crear resúmenes estructurados

### 👨‍💼 Profesionales
- Transcribe reuniones y juntas
- Documenta conferencias técnicas
- Crea minutas automáticas

### 🎙️ Creadores de Contenido
- Transcribe podcasts/videos
- Genera subtítulos precisos
- Convierte audio en blogs

---

## ❓ **Solución de Problemas**

### No se detecta el micrófono
- ✅ Permite permisos en el navegador (🔒 icono en la barra URL)
- ✅ Verifica que tu micrófono esté conectado
- ✅ Usa el **🎤 Test Mic** para calibrar

### Error de conexión con el backend
- ✅ Verifica que `python backend/main.py` esté corriendo
- ✅ Revisa que el puerto **8001** esté libre
- ✅ Comprueba `.env` tiene `NVIDIA_API_KEY`

### La transcripción no aparece
- ✅ Ajusta **🎛️ Calibración VAD** (sube sensibilidad)
- ✅ Habla más cerca del micrófono
- ✅ Verifica niveles en **🎤 Test Mic** (>50dB)

---

## 📚 **Documentación Adicional**

- 📄 [Informe de Arquitectura (PDF)](./docs/informe_arquitectura.pdf) — 22 páginas con diagramas UML
- 🎨 [Patrones de Diseño GoF](./docs/patrones_diseno.md) — Implementación de 8 patrones
- 🐳 [Guía Docker](./DOCKER.md) — Despliegue completo con contenedores

---

## 🤝 **Contribuciones**

SpeechNotes es un proyecto educativo. Si deseas contribuir:

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar X funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📜 **Licencia**

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

## 🍌 **Créditos**

Desarrollado con ❤️ por el equipo **SpeechNotes Team**

> *"El futuro de tomar notas no es escribir, es escuchar."*

**Tecnologías clave:** NVIDIA Riva • Next.js • FastAPI • MongoDB • Kimi K2-Thinking

---

**¿Listo para transformar tu forma de tomar notas? 🚀**

```bash
python backend/main.py & cd web && pnpm dev
```

*Abre http://localhost:3000 y empieza a grabar* 🎤✨
