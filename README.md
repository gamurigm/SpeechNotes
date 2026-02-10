# 🎙️ SpeechNotes: The Ultimate AI Research Companion 🚀

![Ultimate Dashboard](./docs/assets/screenshots/appCap-ultimate1.png)

**SpeechNotes** no es solo una grabadora; es tu **Segundo Cerebro**. Captura, transcribe, formatea y entiende tus clases y reuniones con una suite de herramientas de IA de vanguardia.

---

## 🍌 Guía Avanzada de Funciones

Descubre todo el poder "Nano Banana" que tienes a tu disposición:

### ⚡ 1. Transcripción en Tiempo Real (Riva + VAD)
*   **Zero-Latency Capture:** Usa **NVIDIA Riva** para transcribir tu voz en milisegundos.
*   **VAD Visual:** El anillo de grabación y el visualizador reaccionan a tu voz. Si el anillo brilla, ¡te escuchamos!
*   **Sync Instantáneo:** Gracias a nuestros _WebSockets optimizados_, lo que dices aparece en tu pantalla al instante. **Ya no hay esperas:** el texto "crudo" se muestra mientras la IA lo pule.

### 🎛️ 2. Formatting Magic Station (Nuevo)
Convierte audios desordenados en obras maestras:
*   **🪄 Magic Format:** Detecta automáticamente el tipo de audio y aplica el mejor perfil.
*   **🔊 Normalización:** Nivela el volumen automáticamente a -16dB LUFS para un sonido broadcast.
*   **✂️ Silence Remover:** Elimina los silencios incómodos de tus grabaciones largas.
*   **🚀 Speed Up:** Acelera audios lentos (1.5x) sin cambiar el tono de la voz gracias a FFmpeg.

### 🧠 3. Cerebro Dual (Kimi & Minimax)
Dos modelos de IA trabajando en paralelo para ti:
*   **Kimi (Thinking Mode):** Tu analista profundo. Úsalo para razonar sobre el contenido, encontrar conexiones ocultas y responder preguntas complejas. *Perfecto para exámenes.*
*   **Minimax (Formatting):** El arquitecto de la información. Estructura tus notas con Markdown impecable, tablas y resúmenes ejecutivos.

### 🔎 4. Búsqueda Semántica "Neural"
Olvídate de buscar "palabras exactas".
*   Presiona `Ctrl+F` y describe lo que buscas (ej: *"la parte donde el profe habló de mitocondrias"*).
*   Nuestro motor **Llama 3.2 Nemoretriever** entenderá el *significado* y te llevará al momento exacto.

### 🎨 5. Experiencia "Glassmorphism"
*   **Interfaz Inmersiva:** Fondos dinámicos, desenfoques en tiempo real y micro-interacciones suaves.
*   **Modo Zen:** Colapsa el chat y la barra lateral para enfocarte solo en tus notas.
*   **Temas:** Personaliza tu entorno desde el menú `Temas` para que coincida con tu vibe.

---

## 🚀 Inicio Rápido

1. **Configura tus llaves:**
   Asegúrate de que tu `.env` tenga `NVIDIA_API_KEY` y `MONGO_URI`.

2. **Enciende los motores:**
   ```bash
   # Terminal 1: Backend
   python backend/main.py

   # Terminal 2: Frontend
   pnpm dev
   ```

3. **¡Graba!**
   Presiona el botón del micrófono y deja que la magia ocurra.

---

## 🏗️ Arquitectura y Patrones de Diseño

Este proyecto implementa una arquitectura robusta basada en **Patrones de Diseño (GoF)** y **Principios SOLID** para garantizar mantenibilidad, escalabilidad y testabilidad.

Consulta la documentación detallada en [ARCHITECTURE.md](./ARCHITECTURE.md), donde se explican:
- **Backend**: Service Layer, Facade (Socket.IO), Adapter (Audio), Strategy (VAD), Singleton, Repository.
- **Frontend**: Builder (AudioGraph), Singleton/Facade (ApiClient), Observer.

---

> *"El futuro de tomar notas no es escribir, es escuchar."* - **SpeechNotes Team** 🍌
