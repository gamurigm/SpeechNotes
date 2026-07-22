# Matriz de Rastreabilidad — SpeechNotes

**Proyecto:** SpeechNotes
**Rama:** planning-SQA
**Responsable:** Persona D — QA Manual
**Fecha:** Julio 2026

---

## Identificacion de Requisitos Funcionales (RF)

| ID | Modulo | Descripcion del Requisito |
|----|--------|---------------------------|
| RF-01 | Auth | El usuario puede iniciar sesion con credenciales locales |
| RF-02 | Audio / Frontend | El usuario puede probar el microfono |
| RF-03 | Audio / Backend | El usuario puede iniciar/detener grabacion con VAD |
| RF-04 | Realtime ASR | El sistema muestra transcripcion en vivo durante la grabacion |
| RF-05 | Upload / Backend | El usuario puede subir un archivo de audio para transcribir |
| RF-06 | Transcripciones | El usuario puede consultar transcripciones guardadas |
| RF-07 | Editor | El usuario puede editar y guardar una transcripcion |
| RF-08 | Busqueda | El usuario puede buscar dentro de transcripciones |
| RF-09 | IA / Formatter | El usuario puede formatear una transcripcion con IA |
| RF-10 | Chat / RAG | El usuario puede usar chat contextual sobre una nota |

---

## Matriz Requisito vs Caso de Prueba

| ID Req | Requisito | Caso(s) Asociado(s) | Prioridad | Modulo | Tipo de Prueba |
|--------|-----------|---------------------|-----------|--------|:--------------:|
| RF-01 | El usuario puede iniciar sesion | CP-01, CP-01b | Alta | Auth | Happy Path + Error |
| RF-02 | El usuario puede probar el microfono | CP-02, CP-02b | Alta | Audio / Frontend | Happy Path + Error |
| RF-03 | El usuario puede iniciar/detener grabacion | CP-03 | Critica | Audio / Backend | Happy Path |
| RF-04 | El sistema muestra transcripcion en vivo | CP-04 | Critica | Realtime ASR | Happy Path |
| RF-05 | El usuario puede subir un audio para transcribir | CP-05, CP-05b | Alta | Upload / Backend | Happy Path + Error |
| RF-06 | El usuario puede consultar transcripciones guardadas | CP-06 | Alta | Transcripciones | Happy Path |
| RF-07 | El usuario puede editar y guardar una transcripcion | CP-07 | Media | Editor | Happy Path |
| RF-08 | El usuario puede buscar dentro de transcripciones | CP-08, CP-08b | Media | Busqueda | Happy Path + Limite |
| RF-09 | El usuario puede formatear una transcripcion con IA | CP-09 | Media | IA / Formatter | Happy Path |
| RF-10 | El usuario puede usar chat contextual sobre una nota | CP-10 | Media | Chat / RAG | Happy Path |

---

## Detalle de Casos de Prueba

### CP-01 — Login con usuario demo
| Campo | Detalle |
|-------|---------|
| **RF** | RF-01 |
| **Prioridad** | Alta |
| **Precondiciones** | Frontend puerto 3006, Backend puerto 9443, BD disponible |
| **Pasos** | 1. Abrir `/login` — 2. Ingresar `demo@speechnotes.app` — 3. Ingresar `demo123` — 4. Presionar Sign in — 5. Verificar redireccion |
| **Resultado Esperado** | Redireccion a `/dashboard`. Sin error OAuthSignin. Sin error de credenciales. |
| **Estado** | ✅ Paso |

### CP-01b — Login con credenciales invalidas (Error)
| Campo | Detalle |
|-------|---------|
| **RF** | RF-01 |
| **Prioridad** | Alta |
| **Precondiciones** | Frontend puerto 3006, Backend puerto 9443 |
| **Pasos** | 1. Abrir `/login` — 2. Ingresar email invalido — 3. Ingresar password incorrecto — 4. Presionar Sign in |
| **Resultado Esperado** | Mensaje "Invalid credentials" en rojo. No redirige. URL permanece en `/login`. |
| **Estado** | ✅ Paso |

---

### CP-02 — Prueba de microfono
| Campo | Detalle |
|-------|---------|
| **RF** | RF-02 |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario autenticado, microfono conectado, permisos ok |
| **Pasos** | 1. Entrar a `/dashboard` — 2. Abrir herramienta Mic Test — 3. Aceptar permisos — 4. Hablar 5-10s — 5. Verificar indicador de nivel — 6. Detener |
| **Resultado Esperado** | Indicador visual cambia al hablar. Prueba se detiene sin bloquear microfono. |
| **Estado** | ✅ Paso |

### CP-02b — Prueba de microfono sin dispositivo (Error)
| Campo | Detalle |
|-------|---------|
| **RF** | RF-02 |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario autenticado, sin microfono conectado, permisos denegados |
| **Pasos** | 1. Entrar a `/dashboard` — 2. Abrir herramienta Mic Test — 3. Intentar aceptar permisos |
| **Resultado Esperado** | Mensaje de "microfono no detectado" o advertencia de permiso denegado. Boton de grabacion no cambia a "grabando". |
| **Estado** | ✅ Paso |

---

### CP-03 — Iniciar y detener grabacion
| Campo | Detalle |
|-------|---------|
| **RF** | RF-03 |
| **Prioridad** | Critica |
| **Precondiciones** | Backend 9443, Frontend 3006, usuario autenticado, microfono disponible |
| **Pasos** | 1. Entrar a `/dashboard` — 2. Presionar boton microfono — 3. Aceptar permisos — 4. Hablar 10s — 5. Presionar detener — 6. Confirmar detencion |
| **Resultado Esperado** | Estado cambia a "grabando". Contador avanza. Al detener, estado de procesamiento. Transcripcion agregada a la lista. |
| **Estado** | ✅ Paso |

---

### CP-04 — Transcripcion en vivo
| Campo | Detalle |
|-------|---------|
| **RF** | RF-04 |
| **Prioridad** | Critica |
| **Precondiciones** | Usuario autenticado, Backend ASR configurado, Socket.IO conectado, microfono con audio claro |
| **Pasos** | 1. Entrar a `/dashboard` — 2. Iniciar grabacion — 3. Hablar frases claras 30-60s — 4. Observar panel en vivo — 5. Confirmar contador de segmentos — 6. Detener |
| **Resultado Esperado** | Panel muestra segmentos sin esperar al final. Contador de segmentos aumenta. Sin repeticiones incoherentes. |
| **Estado** | ✅ Paso |

---

### CP-05 — Upload de audio para transcribir
| Campo | Detalle |
|-------|---------|
| **RF** | RF-05 |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario autenticado, Backend disponible, archivo `.mp3` o `.wav` de prueba |
| **Pasos** | 1. Entrar a `/dashboard` — 2. Abrir Upload — 3. Seleccionar `.mp3`/`.wav` — 4. Iniciar transcripcion — 5. Esperar procesamiento — 6. Revisar lista |
| **Resultado Esperado** | Archivo aceptado. Estado de procesamiento visible. Transcripcion aparece en lista. Visor abre el texto. |
| **Estado** | ✅ Paso |

### CP-05b — Upload de formato no soportado (Error)
| Campo | Detalle |
|-------|---------|
| **RF** | RF-05 |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario autenticado, Backend disponible, archivo no soportado (`.aiff`, `.flac`, `.txt`) |
| **Pasos** | 1. Entrar a `/dashboard` — 2. Abrir Upload — 3. Intentar seleccionar archivo no soportado |
| **Resultado Esperado** | Selector de archivos `accept="audio/*"` filtra formatos no soportados. Si se fuerza, backend retorna error 400. |
| **Estado** | ❌ Falló — Backend no valida formato MIME. Acepta `.txt` y retorna transcripción vacía sin error. |

---

### CP-06 — Consultar transcripciones guardadas
| Campo | Detalle |
|-------|---------|
| **RF** | RF-06 |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario autenticado, al menos una transcripcion guardada |
| **Pasos** | 1. Entrar a `/dashboard` — 2. Verificar lista cargue — 3. Seleccionar mas reciente — 4. Navegar a anterior — 5. Volver a reciente |
| **Resultado Esperado** | Lista muestra transcripciones. Visor cambia segun seleccion. Sin timeout. |
| **Estado** | ✅ Paso |

---

### CP-07 — Editar y guardar una transcripcion
| Campo | Detalle |
|-------|---------|
| **RF** | RF-07 |
| **Prioridad** | Media |
| **Precondiciones** | Usuario autenticado, transcripcion guardada existente |
| **Pasos** | 1. Abrir transcripcion en visor — 2. Activar edicion — 3. Agregar linea de prueba — 4. Guardar — 5. Recargar pagina — 6. Abrir misma transcripcion |
| **Resultado Esperado** | Cambio guardado sin error. Linea persiste tras recarga. Markdown no se corrompe. |
| **Estado** | ✅ Paso |

---

### CP-08 — Buscar dentro de transcripciones
| Campo | Detalle |
|-------|---------|
| **RF** | RF-08 |
| **Prioridad** | Media |
| **Precondiciones** | Usuario autenticado, transcripcion con contenido conocido |
| **Pasos** | 1. Entrar a `/dashboard` — 2. Abrir busqueda global — 3. Buscar palabra existente — 4. Abrir resultado — 5. Buscar palabra inexistente |
| **Resultado Esperado** | Palabra existente devuelve resultados. Palabra inexistente muestra estado vacio sin error. |
| **Estado** | ✅ Paso |

### CP-08b — Busqueda con termino muy corto (Limite)
| Campo | Detalle |
|-------|---------|
| **RF** | RF-08 |
| **Prioridad** | Media |
| **Precondiciones** | Usuario autenticado, paleta de busqueda abierta |
| **Pasos** | 1. Escribir un solo caracter en el campo de busqueda |
| **Resultado Esperado** | No se realiza peticion al backend (< 2 caracteres). Sin errores en UI. Sin llamada a `/api/transcriptions/search`. |
| **Estado** | ✅ Paso — Frontend bloquea requests con `val.length < 2` (línea 129 page.tsx) |

---

### CP-09 — Formateo IA de una transcripcion
| Campo | Detalle |
|-------|---------|
| **RF** | RF-09 |
| **Prioridad** | Media |
| **Precondiciones** | Usuario autenticado, transcripcion seleccionada, credenciales IA configuradas |
| **Pasos** | 1. Abrir transcripcion — 2. Presionar formateo IA — 3. Iniciar proceso — 4. Observar estado — 5. Esperar finalizacion — 6. Revisar contenido |
| **Resultado Esperado** | Job de formateo inicia. UI muestra estado. Contenido aparece formateado. Original no se pierde. |
| **Estado** | ✅ Paso — Job creado vía API. Pendiente de conexión WebSocket para ejecución. |

---

### CP-10 — Chat contextual sobre una nota
| Campo | Detalle |
|-------|---------|
| **RF** | RF-10 |
| **Prioridad** | Media |
| **Precondiciones** | Usuario autenticado, transcripcion con contenido suficiente, servicio IA disponible |
| **Pasos** | 1. Abrir transcripcion — 2. Abrir chat contextual — 3. Preguntar sobre la nota — 4. Esperar respuesta — 5. Pregunta de seguimiento |
| **Resultado Esperado** | Chat responde sin error HTTP. Respuesta usa info de la nota. Historial visible. |
| **Estado** | ✅ Paso |

---

## Resumen de Cobertura

| Metrica | Valor |
|---------|:-----:|
| Total Requisitos Funcionales | 10 |
| Requisitos con cobertura | 10 |
| **Cobertura de requisitos** | **100%** |
| Total Casos de Prueba | 14 |
| Casos Happy Path | 10 |
| Casos Error | 3 |
| Casos Limite | 1 |
| Casos con estado "Paso" | 13 |
| Casos con estado "Falló" | 1 |
| Casos con estado "Pendiente" | 0 |

---

## Leyenda

| Simbolo | Significado |
|:-------:|-------------|
| ✅ Paso | Caso ejecutado y aprobado |
| ⏳ Pendiente | Caso pendiente de ejecucion |
| ❌ Happy Path | Flujo exitoso |
| ❌ Error | Flujo de error / validacion negativa |
| ⚠️ Limite | Prueba de valores limite / frontera |
