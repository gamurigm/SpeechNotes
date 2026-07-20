# Diseño de Casos de Prueba — SpeechNotes

> **Proyecto:** SpeechNotes — Transcripción inteligente asistida por IA
> **Versión:** 1.0
> **Fecha:** Julio 2026
> **Tipo de Prueba:** Pruebas Funcionales Manuales

---

## Convenciones

| Campo | Descripción |
|-------|-------------|
| **ID** | Identificador único del caso de prueba (CP-NNN) |
| **RF** | Requisito funcional asociado |
| **Título** | Nombre descriptivo del caso |
| **Precondiciones** | Estado necesario antes de ejecutar |
| **Pasos** | Secuencia numerada de acciones |
| **Resultado Esperado** | Comportamiento correcto del sistema |
| **Tipo** | Happy Path / Error / Límite |

---

## Módulo 1: Autenticación (RF-01)

### CP-001: Login exitoso con credentials
| Campo | Valor |
|-------|-------|
| **RF** | RF-01 |
| **Título** | Inicio de sesión exitoso con credenciales locales |
| **Precondiciones** | 1. App backend y frontend ejecutándose<br>2. Base de datos MongoDB con usuario registrado<br>3. Navegador en la página `/login` |
| **Pasos** | 1. Ingresar email válido en el campo "Email address"<br>2. Ingresar contraseña correcta en el campo "Password"<br>3. Hacer clic en "Sign in" |
| **Resultado Esperado** | El sistema redirige al dashboard (`/dashboard`). Se muestra la interfaz principal con el panel de grabación y transcripción. |
| **Tipo** | Happy Path |

### CP-002: Login fallido por credenciales inválidas
| Campo | Valor |
|-------|-------|
| **RF** | RF-01 |
| **Título** | Inicio de sesión rechazado con credenciales incorrectas |
| **Precondiciones** | 1. App backend y frontend ejecutándose<br>2. Navegador en la página `/login` |
| **Pasos** | 1. Ingresar email inválido o no registrado<br>2. Ingresar contraseña incorrecta<br>3. Hacer clic en "Sign in" |
| **Resultado Esperado** | El sistema muestra el mensaje "Invalid credentials" en un recuadro rojo. No se redirige al dashboard. |
| **Tipo** | Error |

### CP-003: Login con Google OAuth
| Campo | Valor |
|-------|-------|
| **RF** | RF-01 |
| **Título** | Inicio de sesión mediante proveedor Google OAuth |
| **Precondiciones** | 1. App backend y frontend ejecutándose<br>2. Google OAuth configurado en servidor<br>3. Navegador en la página `/login` |
| **Pasos** | 1. Hacer clic en "Sign in with Google"<br>2. En la ventana emergente de Google, seleccionar una cuenta<br>3. Autorizar la aplicación |
| **Resultado Esperado** | El sistema redirige al dashboard (`/dashboard`). La sesión se crea con los datos de la cuenta Google. |
| **Tipo** | Happy Path |

---

## Módulo 2: Grabación con VAD (RF-02)

### CP-004: Iniciar grabación de audio con detección de voz
| Campo | Valor |
|-------|-------|
| **RF** | RF-02 |
| **Título** | Iniciar sesión de grabación correctamente |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Micrófono conectado y con permisos otorgados<br>3. Panel de grabación visible |
| **Pasos** | 1. Hacer clic en el botón de grabación del `RecordingPanel`<br>2. Hablar al micrófono durante 5 segundos<br>3. Observar el indicador de nivel de audio |
| **Resultado Esperado** | El botón de grabación cambia a estado "grabando". Se emite el evento Socket.IO `start_recording`. El medidor de nivel de audio (`audio_level`) muestra variación al hablar. |
| **Tipo** | Happy Path |

### CP-005: Detener grabación y obtener transcripción
| Campo | Valor |
|-------|-------|
| **RF** | RF-02 / RF-03 |
| **Título** | Detener grabación y recibir transcripción procesada |
| **Precondiciones** | 1. Sesión de grabación activa (CP-004)<br>2. Se ha hablado al menos 10 segundos |
| **Pasos** | 1. Hacer clic en el botón de detener grabación<br>2. Esperar a que el backend procese los segmentos<br>3. Verificar el contenido en el `MarkdownViewer` |
| **Resultado Esperado** | Se emite el evento Socket.IO `stop_recording`. El backend persiste la transcripción en MongoDB. El `MarkdownViewer` muestra el texto transcrito formateado. Se emite `processing_complete`. |
| **Tipo** | Happy Path |

### CP-006: Error al grabar sin permiso de micrófono
| Campo | Valor |
|-------|-------|
| **RF** | RF-02 |
| **Título** | Intento de grabación sin permisos de micrófono |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Permiso de micrófono denegado en el navegador |
| **Pasos** | 1. Hacer clic en el botón de grabación |
| **Resultado Esperado** | El navegador muestra una advertencia de permiso denegado. El botón de grabación no cambia de estado o muestra un mensaje de error indicando que el micrófono no está disponible. |
| **Tipo** | Error |

---

## Módulo 3: Transcripción en Vivo (RF-03)

### CP-007: Visualizar transcripción en tiempo real durante grabación
| Campo | Valor |
|-------|-------|
| **RF** | RF-03 |
| **Título** | Recepción de transcripción parcial mientras se graba |
| **Precondiciones** | 1. Sesión de grabación activa<br>2. Conexión Socket.IO establecida |
| **Pasos** | 1. Hablar frases cortas con pausas entre ellas<br>2. Observar el área de transcripción en vivo (`LiveTranscription`) |
| **Resultado Esperado** | Cada segmento de voz transcrito aparece en el área de transcripción en vivo a medida que el backend lo procesa. El evento `transcription` se emite con el texto parcial. |
| **Tipo** | Happy Path |

### CP-008: Caída de conexión WebSocket durante transcripción
| Campo | Valor |
|-------|-------|
| **RF** | RF-03 |
| **Título** | Interrupción de conexión Socket.IO durante grabación activa |
| **Precondiciones** | 1. Sesión de grabación activa<br>2. Conexión Socket.IO establecida |
| **Pasos** | 1. Interrumpir la conexión de red (desconectar WiFi/Ethernet)<br>2. Esperar 10 segundos<br>3. Restaurar la conexión de red |
| **Resultado Esperado** | El frontend detecta la desconexión y muestra un indicador. Al reconectarse, la sesión de grabación se reanuda o se notifica al usuario que debe reiniciar la grabación. |
| **Tipo** | Error |

---

## Módulo 4: Calibración VAD (RF-04)

### CP-009: Ajustar umbral de voz y guardar configuración
| Campo | Valor |
|-------|-------|
| **RF** | RF-04 |
| **Título** | Modificar umbral de sensibilidad de voz y persistir cambios |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Toolbar visible |
| **Pasos** | 1. Hacer clic en el ícono de sliders (Calibración VAD)<br>2. Mover el slider "Sensibilidad Voz" a un valor diferente (ej. 500)<br>3. Hacer clic en el check (✓) para guardar<br>4. Recargar la página y abrir nuevamente la calibración |
| **Resultado Esperado** | Se envía POST a `/api/config/vad/` con los nuevos valores. Al recargar, el slider muestra el valor guardado. El backend responde correctamente. |
| **Tipo** | Happy Path |

### CP-010: Ajustar umbral de silencio
| Campo | Valor |
|-------|-------|
| **RF** | RF-04 |
| **Título** | Modificar umbral de silencio y verificar persistencia |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Panel de calibración VAD abierto |
| **Pasos** | 1. Mover el slider "Umbral de Silencio" a 300<br>2. Hacer clic en el check (✓)<br>3. Recargar la página |
| **Resultado Esperado** | El valor del umbral de silencio se guarda en el backend mediante POST `/api/config/vad/`. Al recargar, el valor persiste. |
| **Tipo** | Happy Path |

### CP-011: Valores fuera de rango en calibración VAD
| Campo | Valor |
|-------|-------|
| **RF** | RF-04 |
| **Título** | Ingresar valores de umbral fuera del rango permitido |
| **Precondiciones** | 1. Panel de calibración VAD abierto |
| **Pasos** | 1. Intentar mover el slider "Sensibilidad Voz" por debajo de 20 o por encima de 1000<br>2. Intentar mover el slider "Umbral de Silencio" por debajo de 10 o por encima de 800 |
| **Resultado Esperado** | Los sliders están limitados a su rango definido (20-1000 y 10-800 respectivamente). No es posible ingresar valores fuera de estos límites mediante la UI. |
| **Tipo** | Límite |

---

## Módulo 5: Prueba de Micrófono (RF-05)

### CP-012: Verificar funcionamiento del micrófono
| Campo | Valor |
|-------|-------|
| **RF** | RF-05 |
| **Título** | Prueba de micrófono muestra nivel de audio en tiempo real |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Micrófono conectado y con permisos |
| **Pasos** | 1. Hacer clic en el ícono de micrófono en la toolbar<br>2. Hablar al micrófono<br>3. Observar el medidor de nivel en el componente `MicTest` |
| **Resultado Esperado** | El componente `MicTest` se muestra en la sidebar. Al hablar, el medidor de nivel de audio reacciona en tiempo real mostrando la actividad del micrófono. |
| **Tipo** | Happy Path |

### CP-013: Error al no detectar micrófono
| Campo | Valor |
|-------|-------|
| **RF** | RF-05 |
| **Título** | Prueba de micrófono sin dispositivo de audio disponible |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Ningún micrófono conectado al equipo |
| **Pasos** | 1. Hacer clic en el ícono de micrófono en la toolbar |
| **Resultado Esperado** | El componente `MicTest` muestra un mensaje indicando que no se detecta ningún micrófono o que los permisos no han sido otorgados. |
| **Tipo** | Error |

---

## Módulo 6: Subir y Transcribir Audio (RF-06)

### CP-014: Subir archivo de audio soportado y transcribir
| Campo | Valor |
|-------|-------|
| **RF** | RF-06 |
| **Título** | Transcripción exitosa de archivo de audio subido (MP3) |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Archivo MP3 válido disponible (ej. `grabacion.mp3`)<br>3. API key de NVIDIA configurada |
| **Pasos** | 1. Hacer clic en el ícono de upload (FileAudio2) en la toolbar<br>2. En el panel "Subir Audio", hacer clic en el área de carga<br>3. Seleccionar un archivo MP3 válido<br>4. Hacer clic en "Iniciar Transcripción"<br>5. Esperar a que el procesamiento termine |
| **Resultado Esperado** | El archivo se envía mediante POST a `/api/transcribe-file`. El backend procesa el audio y guarda la transcripción en MongoDB. El `MarkdownViewer` muestra el resultado transcrito. |
| **Tipo** | Happy Path |

### CP-015: Subir archivo de formato no soportado
| Campo | Valor |
|-------|-------|
| **RF** | RF-06 |
| **Título** | Intento de transcripción con formato de audio no soportado |
| **Precondiciones** | 1. Panel "Subir Audio" abierto |
| **Pasos** | 1. Hacer clic en el área de carga<br>2. Seleccionar un archivo con extensión no soportada (ej. `.aiff`, `.flac`, o un archivo no-audio como `.txt`)<br>3. Hacer clic en "Iniciar Transcripción" |
| **Resultado Esperado** | El selector de archivos `accept="audio/*"` filtra archivos no-audio. Si se fuerza un formato no soportado, el backend retorna un error 400 indicando formato inválido y el frontend muestra un mensaje de error. |
| **Tipo** | Error |

### CP-016: Subir archivo vacío o corrupto
| Campo | Valor |
|-------|-------|
| **RF** | RF-06 |
| **Título** | Transcripción de archivo de audio corrupto o vacío |
| **Precondiciones** | 1. Panel "Subir Audio" abierto |
| **Pasos** | 1. Crear un archivo de audio vacío o corrupto (ej. MP3 de 0 bytes)<br>2. Arrastrarlo al área de carga o seleccionarlo<br>3. Hacer clic en "Iniciar Transcripción" |
| **Resultado Esperado** | El backend retorna un error indicando que el archivo no puede ser procesado. El frontend muestra una notificación de error. |
| **Tipo** | Error |

---

## Módulo 7: Procesamiento FFmpeg (RF-07)

### CP-017: Normalizar volumen de audio
| Campo | Valor |
|-------|-------|
| **RF** | RF-07 |
| **Título** | Normalización de volumen de un archivo de audio |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Panel de "Transformación de Audio" abierto (ícono Waves)<br>3. Archivo de audio cargado |
| **Pasos** | 1. Hacer clic en el botón "Normalizar"<br>2. Esperar la respuesta del sistema |
| **Resultado Esperado** | Se envía POST a `/api/audio-format/normalize`. El backend procesa el audio y normaliza el volumen a -16dB. Se muestra una notificación "Normalizando volumen a -16dB...". |
| **Tipo** | Happy Path |

### CP-018: Eliminar silencios de audio
| Campo | Valor |
|-------|-------|
| **RF** | RF-07 |
| **Título** | Eliminación de silencios al inicio y final del audio |
| **Precondiciones** | 1. Panel de transformación de audio abierto<br>2. Archivo de audio cargado |
| **Pasos** | 1. Hacer clic en "Quitar Silencio"<br>2. Esperar la respuesta |
| **Resultado Esperado** | Se envía POST a `/api/audio-format/trim-silence`. El backend procesa y elimina silencios. Se muestra notificación confirmando la operación. |
| **Tipo** | Happy Path |

### CP-019: Cambiar velocidad de reproducción
| Campo | Valor |
|-------|-------|
| **RF** | RF-07 |
| **Título** | Modificar velocidad del audio a 1.5x |
| **Precondiciones** | 1. Panel de transformación de audio abierto<br>2. Archivo de audio cargado |
| **Pasos** | 1. Hacer clic en "Velocidad"<br>2. Esperar la respuesta |
| **Resultado Esperado** | Se envía POST a `/api/audio-format/change-speed`. El audio se procesa con el factor de velocidad solicitado. |
| **Tipo** | Happy Path |

### CP-020: Procesar sin archivo seleccionado
| Campo | Valor |
|-------|-------|
| **RF** | RF-07 |
| **Título** | Intentar operación FFmpeg sin archivo de audio cargado |
| **Precondiciones** | 1. Panel de transformación de audio abierto<br>2. Ningún archivo seleccionado |
| **Pasos** | 1. Hacer clic en "Normalizar", "Quitar Silencio" o cualquier operación<br>2. Observar el estado de los botones |
| **Resultado Esperado** | Los botones de acción ("Descargar", "Procesar") y las operaciones están deshabilitados (`disabled=true`) mientras no haya un archivo cargado. |
| **Tipo** | Error |

---

## Módulo 8: Búsqueda Semántica — RAG (RF-08)

### CP-021: Buscar concepto existente en transcripciones
| Campo | Valor |
|-------|-------|
| **RF** | RF-08 |
| **Título** | Búsqueda semántica de un término que existe en las transcripciones |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Existen transcripciones en la base de datos<br>3. ChromaDB configurado y poblado |
| **Pasos** | 1. Presionar Ctrl+F o hacer clic en el ícono de búsqueda<br>2. En la paleta de búsqueda, escribir un término existente (ej. "patrones de diseño")<br>3. Esperar los resultados |
| **Resultado Esperado** | El sistema realiza GET a `/api/transcriptions/search?q=patrones%20de%20diseno`. Se muestran resultados relevantes con fragmentos de transcripciones coincidentes. |
| **Tipo** | Happy Path |

### CP-022: Buscar término sin resultados
| Campo | Valor |
|-------|-------|
| **RF** | RF-08 |
| **Título** | Búsqueda semántica de un término inexistente |
| **Precondiciones** | 1. Paleta de búsqueda abierta |
| **Pasos** | 1. Escribir un término que no existe en ninguna transcripción (ej. "xyzzy123")<br>2. Observar los resultados |
| **Resultado Esperado** | El sistema muestra "sin resultados" o lista vacía. No se produce ningún error. |
| **Tipo** | Happy Path |

### CP-023: Búsqueda con término muy corto
| Campo | Valor |
|-------|-------|
| **RF** | RF-08 |
| **Título** | Búsqueda con menos de 2 caracteres |
| **Precondiciones** | 1. Paleta de búsqueda abierta |
| **Pasos** | 1. Escribir un carácter suelto (ej. "a")<br>2. Observar el comportamiento |
| **Resultado Esperado** | El sistema no realiza la búsqueda. La lógica del frontend (`if (val.length < 2)`) previene consultas con menos de 2 caracteres. |
| **Tipo** | Límite |

---

## Módulo 9: Chat Contextual (RF-09)

### CP-024: Pregunta contextual sobre transcripción activa
| Campo | Valor |
|-------|-------|
| **RF** | RF-09 |
| **Título** | Enviar pregunta al agente contextual sobre la transcripción actual |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Transcripción activa seleccionada en el `MarkdownViewer` |
| **Pasos** | 1. Hacer clic en el ícono de chat en la sidebar para abrir `ChatSidebar`<br>2. Escribir una pregunta sobre el contenido de la transcripción (ej. "¿De qué trata esta clase?")<br>3. Presionar Enter o enviar |
| **Resultado Esperado** | La pregunta se envía al backend mediante POST `/api/chat/stream` o POST `/api/chat/`. El agente responde basándose en el contexto de la transcripción activa. La respuesta se muestra en el `ChatSidebar`. |
| **Tipo** | Happy Path |

### CP-025: Pregunta sin transcripción activa
| Campo | Valor |
|-------|-------|
| **RF** | RF-09 |
| **Título** | Chat contextual sin ninguna transcripción cargada |
| **Precondiciones** | 1. ChatSidebar abierto<br>2. Ninguna transcripción seleccionada |
| **Pasos** | 1. Escribir una pregunta genérica<br>2. Enviar la pregunta |
| **Resultado Esperado** | El agente responde indicando que no hay contexto de transcripción disponible o responde de forma genérica sin referencia a documentos específicos. |
| **Tipo** | Error |

---

## Módulo 10: Temas y Fondo (RF-10)

### CP-026: Cambiar tema de la interfaz
| Campo | Valor |
|-------|-------|
| **RF** | RF-10 |
| **Título** | Aplicar un tema visual diferente |
| **Precondiciones** | 1. Sesión iniciada en el dashboard |
| **Pasos** | 1. Hacer clic en el ícono de paleta (Temas)<br>2. En el panel `ThemeSettings`, seleccionar un tema diferente (claro/oscuro)<br>3. Observar el cambio visual |
| **Resultado Esperado** | La interfaz cambia al tema seleccionado inmediatamente. Los colores de fondo, texto y componentes se actualizan según el tema elegido. |
| **Tipo** | Happy Path |

### CP-027: Aplicar fondo personalizado
| Campo | Valor |
|-------|-------|
| **RF** | RF-10 |
| **Título** | Seleccionar imagen de fondo personalizada |
| **Precondiciones** | 1. Panel de temas abierto |
| **Pasos** | 1. En el `BackgroundPicker`, seleccionar una imagen de fondo<br>2. Observar el cambio en el dashboard |
| **Resultado Esperado** | El fondo del dashboard cambia a la imagen seleccionada. La imagen se aplica correctamente sin distorsionar la interfaz. |
| **Tipo** | Happy Path |

---

## Módulo 11: Zoom de Interfaz (RF-11)

### CP-028: Ajustar zoom al 125%
| Campo | Valor |
|-------|-------|
| **RF** | RF-11 |
| **Título** | Incrementar el zoom de la interfaz al 125% |
| **Precondiciones** | 1. Sesión iniciada en el dashboard<br>2. Panel de zoom abierto (ícono de lupa) |
| **Pasos** | 1. Mover el slider de "Escala" a 125%<br>2. Observar el cambio en la interfaz |
| **Resultado Esperado** | Todos los elementos de la interfaz se escalan al 125%. El título del panel muestra el valor actualizado. |
| **Tipo** | Happy Path |

### CP-029: Zoom fuera del rango permitido (Ctrl +/+)
| Campo | Valor |
|-------|-------|
| **RF** | RF-11 |
| **Título** | Intentar zoom más allá del límite máximo usando teclas |
| **Precondiciones** | 1. Dashboard visible con foco |
| **Pasos** | 1. Presionar Ctrl + '+' repetidamente hasta sobrepasar 145%<br>2. Presionar Ctrl + '-' repetidamente hasta bajar de 50% |
| **Resultado Esperado** | El zoom se mantiene dentro del rango 50%-145%. Los límites `clampZoom` evitan valores fuera de rango. |
| **Tipo** | Límite |

---

## Módulo 12: Formateador IA (RF-12)

### CP-030: Formatear transcripciones seleccionadas exitosamente
| Campo | Valor |
|-------|-------|
| **RF** | RF-12 |
| **Título** | Formateo IA de múltiples transcripciones desde el formateador |
| **Precondiciones** | 1. Sesión iniciada<br>2. Existen transcripciones sin formatear en la BD<br>3. API key del modelo de formateo configurada<br>4. Navegador en `/formatter` |
| **Pasos** | 1. Verificar que la lista "Archivos Disponibles" muestra transcripciones<br>2. Seleccionar 2-3 transcripciones usando los checkboxes<br>3. Hacer clic en "Formatear N transcripciones"<br>4. Observar el progreso en el panel "Progreso en Tiempo Real"<br>5. Esperar a que todos los trabajos completen |
| **Resultado Esperado** | Se envía POST a `/api/format/start`. Se establece conexión WebSocket a `/api/format/ws/{job_id}`. El progreso se actualiza en tiempo real (reading → formatting → saving → completed). Al finalizar se muestra el resumen con exitosos/fallidos. |
| **Tipo** | Happy Path |

### CP-031: Ver progreso de formateo en tiempo real vía WebSocket
| Campo | Valor |
|-------|-------|
| **RF** | RF-12 |
| **Título** | Visualización de eventos de progreso durante formateo |
| **Precondiciones** | 1. Trabajo de formateo en ejecución |
| **Pasos** | 1. Durante el formateo (CP-030), observar el panel de progreso<br>2. Verificar que cada archivo muestra su estado individual |
| **Resultado Esperado** | Cada archivo procesado muestra su estado: 📖 Leyendo, 🤖 Formateando, 💾 Guardando, ✅ Completado. La barra de progreso global se actualiza. El Job ID se muestra. |
| **Tipo** | Happy Path |

### CP-032: Intentar formatear sin seleccionar archivos
| Campo | Valor |
|-------|-------|
| **RF** | RF-12 |
| **Título** | Botón de formateo deshabilitado sin selección |
| **Precondiciones** | 1. Página de formateador cargada<br>2. Ninguna transcripción seleccionada |
| **Pasos** | 1. Observar el estado del botón "Formatear" |
| **Resultado Esperado** | El botón "Formatear" está deshabilitado (`disabled=true`) con estilo gris y texto "Selecciona archivos primero" o similar. No se puede hacer clic. |
| **Tipo** | Error |

### CP-033: Error en formateo por fallo de conexión WebSocket
| Campo | Valor |
|-------|-------|
| **RF** | RF-12 |
| **Título** | Caída de WebSocket durante trabajo de formateo |
| **Precondiciones** | 1. Trabajo de formateo iniciado |
| **Pasos** | 1. Una vez iniciado el formateo, interrumpir la conexión de red<br>2. Observar el comportamiento del panel de progreso |
| **Resultado Esperado** | El WebSocket detecta el error (`websocket.onerror`) y el frontend muestra un indicador de error. El backend continúa procesando pero el frontend pierde la capacidad de recibir actualizaciones. |
| **Tipo** | Error |

---

## Módulo 13: Configuración de API Keys (RF-13)

### CP-034: Guardar API key correctamente
| Campo | Valor |
|-------|-------|
| **RF** | RF-13 |
| **Título** | Actualizar y guardar una clave de API |
| **Precondiciones** | 1. Sesión iniciada<br>2. Navegador en `/settings` |
| **Pasos** | 1. Localizar la categoría "IA / LLM"<br>2. Ingresar un valor en el campo `NVIDIA_API_KEY_ASR`<br>3. Hacer clic en "Guardar cambios"<br>4. Recargar la página |
| **Resultado Esperado** | Se envía PUT a `/api/settings/` con los cambios. El valor se muestra como guardado. Al recargar, el campo muestra "[masked]" confirmando que la clave se almacenó de forma segura. |
| **Tipo** | Happy Path |

### CP-035: Validar claves faltantes
| Campo | Valor |
|-------|-------|
| **RF** | RF-13 |
| **Título** | Verificación de claves requeridas faltantes |
| **Precondiciones** | 1. Página de configuración cargada<br>2. Al menos una clave requerida sin configurar |
| **Pasos** | 1. Observar la parte superior de la página de configuración<br>2. Revisar las categorías de configuración |
| **Resultado Esperado** | Se muestra un card de advertencia "Claves requeridas faltantes" con la lista de claves faltantes como chips. El badge en el header muestra "N clave(s) faltante(s)". |
| **Tipo** | Happy Path / Error |

### CP-036: Mostrar/ocultar clave secreta
| Campo | Valor |
|-------|-------|
| **RF** | RF-13 |
| **Título** | Alternar visibilidad de una clave secreta |
| **Precondiciones** | 1. Página de configuración cargada<br>2. Una clave de API visible (categoría IA / LLM o Voz) |
| **Pasos** | 1. Hacer clic en el ícono de ojo (Eye) junto a un campo secreto<br>2. Ver el valor en texto plano<br>3. Hacer clic nuevamente en el ícono ojo tachado (EyeOff) |
| **Resultado Esperado** | Al hacer clic en Eye, el campo cambia de tipo `password` a `text` mostrando el valor. Al hacer clic en EyeOff, vuelve a `password` ocultando el valor. |
| **Tipo** | Happy Path |

---

## Módulo 14: Chat con Documentos (RF-14)

### CP-037: Conversación con el asistente sobre documentos
| Campo | Valor |
|-------|-------|
| **RF** | RF-14 |
| **Título** | Enviar mensaje y recibir respuesta del asistente de documentos |
| **Precondiciones** | 1. Sesión iniciada<br>2. Navegador en `/dashboard/chat`<br>3. API key del modelo de chat configurada |
| **Pasos** | 1. Escribir una pregunta en el campo de texto (ej. "¿De qué trata la clase de análisis y diseño?")<br>2. Hacer clic en "Enviar" o presionar Enter |
| **Resultado Esperado** | El mensaje aparece en el área de conversación. El asistente responde. El indicador de carga (animación de puntos) se muestra mientras el asistente procesa. |
| **Tipo** | Happy Path |

### CP-038: Enviar mensaje vacío
| Campo | Valor |
|-------|-------|
| **RF** | RF-14 |
| **Título** | Intentar enviar un mensaje sin contenido |
| **Precondiciones** | 1. Página de chat cargada |
| **Pasos** | 1. Dejar el campo de texto vacío<br>2. Hacer clic en "Enviar" |
| **Resultado Esperado** | El botón "Enviar" está deshabilitado (`disabled=true`) cuando el campo está vacío. No se envía ninguna petición al backend. |
| **Tipo** | Error |

---

## Módulo 15: Pipeline Completo de Audio (RF-15)

### CP-039: Ejecutar pipeline completo (BNR → ASR → Traducción)
| Campo | Valor |
|-------|-------|
| **RF** | RF-15 |
| **Título** | Pipeline full: limpieza de ruido + transcripción + traducción |
| **Precondiciones** | 1. Sesión iniciada<br>2. API keys de NVIDIA BNR, Parakeet, Mistral configuradas<br>3. Archivo de audio con ruido de fondo disponible |
| **Pasos** | 1. Enviar POST a `/api/audio/pipeline` con un archivo de audio y `variant=full`<br>2. Esperar el procesamiento<br>3. Verificar el resultado |
| **Resultado Esperado** | El backend procesa el audio en 3 etapas: (1) BNR elimina ruido, (2) Parakeet transcribe, (3) Mistral traduce al idioma destino. Retorna el texto transcrito y traducido. |
| **Tipo** | Happy Path |

### CP-040: Pipeline con modo ASR only
| Campo | Valor |
|-------|-------|
| **RF** | RF-15 |
| **Título** | Pipeline solo transcripción (sin limpieza ni traducción) |
| **Precondiciones** | 1. API key de ASR configurada<br>2. Archivo de audio disponible |
| **Pasos** | 1. Enviar POST a `/api/audio/pipeline` con `variant=asr_only` |
| **Resultado Esperado** | El backend solo ejecuta la transcripción con Parakeet, omitiendo BNR y Mistral. Retorna la transcripción directa. |
| **Tipo** | Happy Path |

---

## Módulo 16: Traducción y Detección de Idioma (RF-16)

### CP-041: Detectar idioma de un texto
| Campo | Valor |
|-------|-------|
| **RF** | RF-16 |
| **Título** | Detección automática de idioma de un fragmento de texto |
| **Precondiciones** | 1. API key de Gemma configurada<br>2. Herramienta como Postman o curl |
| **Pasos** | 1. Enviar POST a `/api/translate/detect` con un texto en español<br>2. Verificar la respuesta |
| **Resultado Esperado** | El backend retorna el idioma detectado (ej. `{"language": "spanish", "confidence": 0.98}`). |
| **Tipo** | Happy Path |

### CP-042: Traducir texto a otro idioma
| Campo | Valor |
|-------|-------|
| **RF** | RF-16 |
| **Título** | Traducción de texto usando Mistral Large |
| **Precondiciones** | 1. API key de Mistral configurada |
| **Pasos** | 1. Enviar POST a `/api/translate/` con `{"text": "Hello world", "target_language": "spanish"}` |
| **Resultado Esperado** | El backend retorna `{"translated_text": "Hola mundo"}` |
| **Tipo** | Happy Path |

### CP-043: Traducción batch de múltiples textos
| Campo | Valor |
|-------|-------|
| **RF** | RF-16 |
| **Título** | Traducción paralela de múltiples fragmentos de texto |
| **Precondiciones** | 1. API key de Mistral configurada |
| **Pasos** | 1. Enviar POST a `/api/translate/batch` con un array de textos |
| **Resultado Esperado** | Todos los textos se traducen en paralelo. Se retorna un array con las traducciones correspondientes. |
| **Tipo** | Happy Path |

### CP-044: Traducción sin API key configurada
| Campo | Valor |
|-------|-------|
| **RF** | RF-16 |
| **Título** | Intento de traducción sin clave de API configurada |
| **Precondiciones** | 1. API key de Mistral NO configurada |
| **Pasos** | 1. Enviar POST a `/api/translate/` |
| **Resultado Esperado** | El backend retorna error 500 o 400 indicando que el servicio de traducción no está configurado. |
| **Tipo** | Error |

---

## Módulo 17: Gestión de Transcripciones (RF-17)

### CP-045: Listar transcripciones disponibles
| Campo | Valor |
|-------|-------|
| **RF** | RF-17 |
| **Título** | Visualizar lista de transcripciones en el dashboard |
| **Precondiciones** | 1. Sesión iniciada en dashboard<br>2. Existen transcripciones en MongoDB |
| **Pasos** | 1. Observar la sidebar izquierda del dashboard<br>2. Verificar que se muestran las transcripciones recientes |
| **Resultado Esperado** | El frontend realiza GET a `/api/transcriptions` y muestra los títulos y fechas de las transcripciones disponibles en la sidebar. |
| **Tipo** | Happy Path |

### CP-046: Seleccionar y ver transcripción existente
| Campo | Valor |
|-------|-------|
| **RF** | RF-17 |
| **Título** | Cargar una transcripción existente en el visor Markdown |
| **Precondiciones** | 1. Sidebar con lista de transcripciones visible |
| **Pasos** | 1. Hacer clic en una transcripción de la lista<br>2. Esperar que se cargue en el `MarkdownViewer` |
| **Resultado Esperado** | El frontend realiza GET a `/api/transcriptions/{id}`. El contenido Markdown se renderiza en el visor con formato correcto (títulos, listas, código). |
| **Tipo** | Happy Path |

### CP-047: Eliminar transcripción
| Campo | Valor |
|-------|-------|
| **RF** | RF-17 |
| **Título** | Eliminación lógica de una transcripción |
| **Precondiciones** | 1. Sidebar con transcripciones visible<br>2. Opción de eliminar disponible |
| **Pasos** | 1. Ejecutar DELETE a `/api/transcriptions/{id}`<br>2. Verificar que la transcripción ya no aparece en la lista |
| **Resultado Esperado** | El backend marca la transcripción como eliminada (borrado lógico) y retorna confirmación. La sidebar ya no la muestra. |
| **Tipo** | Happy Path |

---

## Módulo 18: Procesamiento por Lotes — Batch (RF-18)

### CP-048: Conversión batch de múltiples archivos
| Campo | Valor |
|-------|-------|
| **RF** | RF-18 |
| **Título** | Conversión en lote de varios archivos de audio |
| **Precondiciones** | 1. API key configurada (si aplica)<br>2. Múltiples archivos de audio disponibles |
| **Pasos** | 1. Enviar POST a `/api/audio-format/batch` con múltiples archivos<br>2. Conectarse al WebSocket `/api/audio-format/ws/{job_id}`<br>3. Monitorear el progreso |
| **Resultado Esperado** | El backend procesa cada archivo secuencialmente. El WebSocket emite actualizaciones de progreso. Al finalizar, los archivos convertidos están disponibles para descarga. |
| **Tipo** | Happy Path |

### CP-049: Descarga de archivo procesado
| Campo | Valor |
|-------|-------|
| **RF** | RF-18 |
| **Título** | Descarga de un archivo de audio formateado |
| **Precondiciones** | 1. Archivo previamente procesado por FFmpeg<br>2. Ruta de descarga conocida |
| **Pasos** | 1. Realizar GET a `/api/audio-format/download/{path}` |
| **Resultado Esperado** | El servidor retorna el archivo procesado para descarga. El `Content-Type` corresponde al formato del archivo. |
| **Tipo** | Happy Path |

---

## Módulo 19: Salud y Monitoreo del Sistema (RF-19)

### CP-050: Verificar health check del backend
| Campo | Valor |
|-------|-------|
| **RF** | RF-19 |
| **Título** | Comprobar que el backend responde correctamente |
| **Precondiciones** | 1. Backend ejecutándose en puerto 9443 |
| **Pasos** | 1. Realizar GET a `http://localhost:9443/health` |
| **Resultado Esperado** | El backend retorna `{"status": "healthy"}` con código 200. |
| **Tipo** | Happy Path |

### CP-051: Verificar root endpoint
| Campo | Valor |
|-------|-------|
| **RF** | RF-19 |
| **Título** | Acceder a la raíz del API |
| **Precondiciones** | 1. Backend ejecutándose |
| **Pasos** | 1. Realizar GET a `http://localhost:9443/` |
| **Resultado Esperado** | El backend retorna información de estado del API incluyendo versión y estado. |
| **Tipo** | Happy Path |

---

## Resumen de Casos de Prueba

| ID | Módulo | Título | Tipo |
|----|--------|--------|------|
| CP-001 | Autenticación | Login exitoso con credentials | Happy Path |
| CP-002 | Autenticación | Login fallido por credenciales inválidas | Error |
| CP-003 | Autenticación | Login con Google OAuth | Happy Path |
| CP-004 | Grabación VAD | Iniciar grabación correctamente | Happy Path |
| CP-005 | Grabación VAD / Transcripción | Detener grabación y obtener transcripción | Happy Path |
| CP-006 | Grabación VAD | Error al grabar sin permiso de micrófono | Error |
| CP-007 | Transcripción Vivo | Visualizar transcripción en tiempo real | Happy Path |
| CP-008 | Transcripción Vivo | Caída de conexión WebSocket durante transcripción | Error |
| CP-009 | Calibración VAD | Ajustar umbral de voz y guardar | Happy Path |
| CP-010 | Calibración VAD | Ajustar umbral de silencio | Happy Path |
| CP-011 | Calibración VAD | Valores fuera de rango | Límite |
| CP-012 | Prueba Micrófono | Verificar micrófono | Happy Path |
| CP-013 | Prueba Micrófono | Sin micrófono disponible | Error |
| CP-014 | Subir Audio | Subir MP3 y transcribir | Happy Path |
| CP-015 | Subir Audio | Formato no soportado | Error |
| CP-016 | Subir Audio | Archivo vacío o corrupto | Error |
| CP-017 | FFmpeg | Normalizar volumen | Happy Path |
| CP-018 | FFmpeg | Eliminar silencios | Happy Path |
| CP-019 | FFmpeg | Cambiar velocidad | Happy Path |
| CP-020 | FFmpeg | Sin archivo seleccionado | Error |
| CP-021 | Búsqueda RAG | Buscar concepto existente | Happy Path |
| CP-022 | Búsqueda RAG | Buscar término sin resultados | Happy Path |
| CP-023 | Búsqueda RAG | Término muy corto (< 2 caracteres) | Límite |
| CP-024 | Chat Contextual | Pregunta sobre transcripción activa | Happy Path |
| CP-025 | Chat Contextual | Sin transcripción activa | Error |
| CP-026 | Temas | Cambiar tema visual | Happy Path |
| CP-027 | Temas | Fondo personalizado | Happy Path |
| CP-028 | Zoom | Ajustar zoom a 125% | Happy Path |
| CP-029 | Zoom | Zoom fuera de rango | Límite |
| CP-030 | Formateador IA | Formatear transcripciones seleccionadas | Happy Path |
| CP-031 | Formateador IA | Progreso WebSocket en tiempo real | Happy Path |
| CP-032 | Formateador IA | Sin selección de archivos | Error |
| CP-033 | Formateador IA | Caída de WebSocket | Error |
| CP-034 | Configuración | Guardar API key | Happy Path |
| CP-035 | Configuración | Validar claves faltantes | Happy Path |
| CP-036 | Configuración | Mostrar/ocultar clave secreta | Happy Path |
| CP-037 | Chat Documentos | Conversación con asistente | Happy Path |
| CP-038 | Chat Documentos | Mensaje vacío | Error |
| CP-039 | Pipeline Audio | Pipeline completo (BNR→ASR→Traducción) | Happy Path |
| CP-040 | Pipeline Audio | Modo ASR only | Happy Path |
| CP-041 | Traducción | Detectar idioma | Happy Path |
| CP-042 | Traducción | Traducir texto | Happy Path |
| CP-043 | Traducción | Traducción batch | Happy Path |
| CP-044 | Traducción | Sin API key configurada | Error |
| CP-045 | Gestión Transcripciones | Listar transcripciones | Happy Path |
| CP-046 | Gestión Transcripciones | Seleccionar y ver transcripción | Happy Path |
| CP-047 | Gestión Transcripciones | Eliminar transcripción | Happy Path |
| CP-048 | Batch | Conversión batch múltiples archivos | Happy Path |
| CP-049 | Batch | Descarga de archivo procesado | Happy Path |
| CP-050 | Salud Sistema | Health check backend | Happy Path |
| CP-051 | Salud Sistema | Root endpoint | Happy Path |
