# 🤖 Thinking vs Fast: Modos de Inteligencia en el Chat

El sistema de chat de SpeechNotes incluye dos modos de procesamiento para el asistente IA (Kimi), permitiendo equilibrar la profundidad del análisis con la velocidad de respuesta.

## 🧠 ¿Qué son estos modos?

### 1. Modo Thinking (Análisis Profundo)
Es el modo predeterminado y el más potente. Utiliza las capacidades de **Chain-of-Thought (CoT)** o razonamiento interno del modelo.

- **Cómo funciona:** Antes de responder, el modelo realiza un proceso de reflexión interna para entender mejor el contexto del documento y la pregunta del usuario.
- **Configuración técnica:**
    - `reasoning_budget`: 16,384 tokens.
    - `enable_thinking`: `true`.
- **Ideal para:** 
    - Preguntas complejas que requieren relacionar diferentes partes de una clase.
    - Resúmenes detallados o análisis de conceptos técnicos.
    - Cuando la precisión es más importante que la velocidad inmediata.
- **Indicador Visual:** Aparece como **"Thinking"** con una animación de pulso en el sidebar.

### 2. Modo Fast (Respuesta Rápida)
Este modo prioriza la latencia mínima, entregando una respuesta directa.

- **Cómo funciona:** Se desactiva el presupuesto de razonamiento, obligando al modelo a responder de forma inmediata sin un monólogo interno extendido.
- **Configuración técnica:**
    - `reasoning_budget`: 0 tokens.
    - `chat_template_kwargs`: `thinking: false`.
- **Ideal para:**
    - Preguntas rápidas de "sí o no".
    - Consultas sobre datos puntuales (ej. "¿En qué fecha fue la clase?").
    - Interacciones rápidas donde el usuario necesita la información al instante.
- **Indicador Visual:** Aparece como **"Fast"** con un diseño simplificado.

---

## 🛠️ Implementación Detallada

### Backend (Python/FastAPI)
El control se gestiona en `backend/services/pydantic_agent.py` dentro de la función `chat_stream_direct`. 

Dependiendo del modelo configurado en el `.env` (`MODEL_NAME`), el sistema envía parámetros específicos al proveedor (NVIDIA NIM):
- Para modelos **DeepSeek** o **Kimi**: Se utiliza `extra_body` para configurar el `reasoning_budget`.
- Para modelos **Nemotron**: Se añade el prefijo `/think` al `system_prompt`.

### Frontend (React/Next.js)
El toggle se encuentra en `ChatSidebar.tsx`. El estado `useThinking` se envía en cada petición al endpoint `/api/chat/stream`.

---

## 🔄 Cómo cambiar entre modos
En la parte superior derecha del chat, encontrarás una "Pill" (pastilla) interactiva. Al hacer clic, alternarás entre ambos estados. El sistema recordará tu preferencia durante la sesión actual.
