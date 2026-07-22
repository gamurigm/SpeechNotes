# Transcripcion en vivo con NVIDIA Riva (Parakeet + Whisper)

Este documento resume los cambios hechos para estabilizar la transcripcion en vivo de SpeechNotes y dejar preparado el pipeline para grabaciones largas.

## Objetivo

Resolver estos problemas observados en grabaciones largas o sesiones en vivo:

- La transcripcion en vivo no aparecia en la UI.
- Al presionar Stop no se cargaba el texto en el visor.
- Los modelos ASR pueden devolver repeticiones de baja informacion como `si si`, `no no`, `ah`.
- Las sesiones largas degradaban la calidad por acumulacion de audio en memoria y por cortes no controlados.
- El navegador podia capturar audio a 44.1/48 kHz aunque el backend esperaba PCM mono de 16 kHz.

## Flujo actual

1. El frontend captura microfono con Web Audio.
2. `AudioGraph` convierte la senal real del navegador a PCM mono Int16 de 16 kHz.
3. El cliente Socket.IO envia paquetes PCM cada 0.5 s al backend.
4. El backend escribe el WAV incrementalmente a disco para no acumular grabaciones largas en RAM.
5. El backend acumula ventanas ASR de 10 s con 1 s de overlap.
6. Cada ventana se manda a Parakeet (español) o Whisper (otros idiomas) via Riva gRPC.
7. El backend emite eventos de estado y transcripcion en vivo por Socket.IO.
8. Al detener, el backend drena la cola ASR, guarda el Markdown y emite `processing_complete`.
9. La UI recarga la lista y selecciona el documento cuando recibe `processing_complete`, no cuando recibe solo `recording_stopped`.

## Tiempos importantes

| Nivel | Duracion | Archivo / constante |
| --- | ---: | --- |
| Paquete PCM frontend | 0.5 s | `web/services/AudioGraph.ts` (`CHUNK_SECONDS`) |
| Ventana ASR en vivo | 10 s | `backend/services/realtime/socket_handler.py` (`MAX_SEGMENT_SECONDS`) |
| Overlap ASR | 1 s | `backend/services/realtime/socket_handler.py` (`OVERLAP_SECONDS`) |
| Frecuencia de audio | 16 kHz | frontend y backend |
| Formato de audio | PCM mono Int16 | frontend y backend |

La ventana ASR se bajo de 45 s a 10 s para que la UI muestre texto mas rapido. El valor de 45 s se habia usado temporalmente para reducir alucinaciones con audio degradado; despues se corrigio la captura PCM, por eso ahora es viable usar 10 s.

## Configuracion NVIDIA Riva ASR

SpeechNotes usa los dos modelos Riva documentados:

- Servidor: `grpc.nvcf.nvidia.com:443`
- Parakeet español: `nvidia/parakeet-ctc-0.6b-es`, Function ID `a9eeee8f-b509-4712-b19d-194361fa5f31`, idioma `es-US`.
- Whisper: `whisper-large-v3`, Function ID `b702f636-f60c-4a3d-a6f4-f3568c13bd7d`, con `multi` para autodetección.

Variables esperadas en `.env`:

```dotenv
NVIDIA_API_KEY_ASR=nvapi-...
RIVA_SERVER=grpc.nvcf.nvidia.com:443
RIVA_FUNCTION_ID_PARAKEET=a9eeee8f-b509-4712-b19d-194361fa5f31
RIVA_FUNCTION_ID_WHISPER=b702f636-f60c-4a3d-a6f4-f3568c13bd7d
```

El registro NIM ahora prioriza variables de entorno para ASR antes que valores persistidos en SQLite, evitando que una clave vieja guardada en `data/speechnotes.db` opaque el `.env`.

## Cambios backend

### `backend/services/realtime/socket_handler.py`

- Reemplazo de buffers de audio ilimitados por `IncrementalWavWriter`.
- Cola ASR bounded por sesion para evitar crecimiento indefinido en sesiones de 2 h.
- Worker ASR por sesion que procesa ventanas en orden.
- Emision de `audio_level` y `transcription_status` para que la UI muestre actividad aunque todavia no haya texto.
- Ventanas ASR de 10 s con 1 s de overlap.
- Normalizacion controlada de segmentos debiles antes de ASR.
- Filtros contra alucinaciones comunes:
  - frases tipo `gracias`, `suscribete`, `subtitulos`;
  - repeticiones `si si`, `no no`, `ah`;
  - segmentos cortos de baja energia;
  - duplicados por overlap.
- Al hacer Stop, se encola el ultimo segmento, se espera `queue.join()`, se guarda Markdown y se emite `processing_complete`.

### `backend/services/nim/registry.py`

- `asr_es` usa `nvidia/parakeet-ctc-0.6b-es`.
- Se agrego `RIVA_FUNCTION_ID_PARAKEET` con fallback al Function ID oficial.
- Se prioriza `.env` para claves ASR mediante `_env_first`.

### `backend/services/nim/riva_asr_client.py`

- El cliente Riva ya no esta documentado solo como Whisper; sirve para ASR Riva en general.
- Para Parakeet se usa `language_code=es-US`, mientras Whisper puede usar `multi` para autodeteccion.
- Se envia `source_language` en `custom_configuration` cuando el idioma es conocido.
- Se normalizan codigos cortos: `es` -> `es-ES`, `en` -> `en-US`.

## Cambios frontend

### `web/services/AudioGraph.ts`

- Ya no se asume que `new AudioContext({ sampleRate: 16000 })` sera respetado por el navegador.
- Se captura a la frecuencia real del navegador y se hace downsampling explicito a 16 kHz.
- Se emite PCM mono Int16 deterministicamente.
- Se limita la muestra antes de convertir a Int16 para evitar clipping fuerte.
- Se desactivan `echoCancellation` y `noiseSuppression` porque pueden destruir voz para ASR.
- Se permite pasar `deviceId` para elegir microfono fisico.

### `web/hooks/useRecording.ts`

- Espera conexion Socket.IO y evento `recording_started` antes de empezar a enviar audio.
- Escucha `audio_level`, `transcription_status`, `transcription`, `recording_stopped`, `warning` y `error`.
- Expone `liveStatus` para la UI.
- Lista dispositivos `audioinput`, permite seleccionar `deviceId` y refrescar entradas.

### `web/app/dashboard/components/RecordingPanel.tsx`

- Refactor para reducir complejidad y limpiar warnings de Sonar.
- Selector de microfono en configuracion.
- Controles de ganancia, umbral visual y diarizacion.

### `web/app/dashboard/components/LiveTranscription.tsx`

- Muestra estado vivo aunque no haya texto todavia:
  - RMS recibido;
  - segundos acumulados;
  - cola ASR;
  - segmento en proceso.

### `web/app/dashboard/hooks/useTranscriptionService.ts`

- Ya no recarga documentos inmediatamente en `recording_stopped`.
- Espera `processing_complete` para recargar lista y contenido final.
- Esto evita timeouts y visor vacio mientras el ASR aun procesa.

### `web/app/layout.tsx`

- Limpieza defensiva de `fdprocessedid`, atributo inyectado por extensiones de navegador que provocaba hydration mismatch.
- `themeColor` movido a `viewport`.

## Pruebas ejecutadas

Comandos de validacion usados:

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\services\realtime\socket_handler.py backend\services\nim\registry.py backend\services\nim\riva_asr_client.py
cd web
npm exec eslint -- services/AudioGraph.ts hooks/useRecording.ts app/dashboard/components/RecordingPanel.tsx
npm run build
```

Pruebas funcionales realizadas:

- Health backend: `GET http://127.0.0.1:9443/health` -> `200`.
- Dashboard: `GET http://127.0.0.1:3006/dashboard` -> `200`.
- Socket.IO `start_recording` confirma `max_segment_seconds=10`.
- Parakeet y Whisper responden con la clave ASR actual, sin `PERMISSION_DENIED`.
- Replay de WAVs reales demostro que el backend recibe audio y que el filtro descarta basura de baja informacion en vez de guardarla como transcripcion final.

## Diagnostico si vuelve a fallar

1. Recargar dashboard con `Ctrl + Shift + R` para asegurar que cargue el `AudioGraph` nuevo.
2. Abrir configuracion de audio y elegir el microfono fisico correcto.
3. Evitar entradas virtuales, mezcla stereo, monitor, auriculares sin microfono o dispositivos de cancelacion de ruido.
4. Grabar una frase clara de 20 a 30 s.
5. Revisar en vivo el RMS:
   - muy bajo: subir ganancia o cambiar microfono;
   - muy alto o saturado: bajar ganancia;
   - RMS activo pero texto basura: probar otro ASR o fallback automatico.
6. Revisar logs backend para eventos:
   - `ASR Queue` confirma ventanas enviadas;
   - `ASR Filter` confirma segmentos descartados;
   - `Transcribed ... chars` confirma respuesta de NVIDIA.

## Limitaciones actuales

- Cualquier ASR puede seguir alucinando en audio pobre, ruido alto, musica o microfono equivocado.
- La transcripcion en vivo depende de ventanas de 10 s; no es token streaming real.
- El fallback automatico a otro ASR todavia no esta implementado.
- Los jobs de formateo/Minimax siguen mostrando errores 404 en logs; no bloquean la transcripcion en vivo, pero deben corregirse por separado.
