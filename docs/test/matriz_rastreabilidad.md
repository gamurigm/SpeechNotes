# Matriz de Rastreabilidad — SpeechNotes

> **Proyecto:** SpeechNotes — Transcripción inteligente asistida por IA
> **Versión:** 1.0
> **Fecha:** Julio 2026
> **Propósito:** Mapear cada requisito funcional con sus casos de prueba correspondientes

---

## Identificación de Requisitos Funcionales (RF)

| ID | Módulo | Descripción del Requisito |
|----|--------|---------------------------|
| RF-01 | Autenticación | El sistema debe permitir inicio de sesión mediante credenciales locales y Google OAuth |
| RF-02 | Grabación VAD | El sistema debe grabar audio detectando actividad de voz (VAD) mediante Socket.IO |
| RF-03 | Transcripción Vivo | El sistema debe transcribir audio en tiempo real y mostrar resultados durante la grabación |
| RF-04 | Calibración VAD | El sistema debe permitir ajustar umbrales de voz y silencio para la detección VAD |
| RF-05 | Prueba Micrófono | El sistema debe permitir verificar el funcionamiento del micrófono antes de grabar |
| RF-06 | Subir Audio | El sistema debe permitir subir archivos de audio locales para transcripción batch |
| RF-07 | Procesamiento FFmpeg | El sistema debe ofrecer transformaciones de audio: normalizar, silencios, velocidad, etc. |
| RF-08 | Búsqueda RAG | El sistema debe permitir búsqueda semántica sobre transcripciones usando ChromaDB |
| RF-09 | Chat Contextual | El sistema debe permitir chatear con un agente IA contextual sobre la transcripción activa |
| RF-10 | Temas y Fondo | El sistema debe permitir personalizar la apariencia visual (tema claro/oscuro, fondos) |
| RF-11 | Zoom Interfaz | El sistema debe permitir ajustar el nivel de zoom de la interfaz (50%-145%) |
| RF-12 | Formateador IA | El sistema debe formatear transcripciones usando IA con progreso vía WebSocket |
| RF-13 | Configuración | El sistema debe permitir gestionar API keys y parámetros de configuración |
| RF-14 | Chat Documentos | El sistema debe ofrecer un chat independiente con el agente sobre todos los documentos |
| RF-15 | Pipeline Audio | El sistema debe ejecutar pipeline completo: BNR → ASR → Traducción |
| RF-16 | Traducción | El sistema debe detectar idioma, traducir texto y soportar traducción batch |
| RF-17 | Gestión Transcripciones | El sistema debe listar, ver, buscar, editar y eliminar transcripciones |
| RF-18 | Batch FFmpeg | El sistema debe procesar conversiones por lote con progreso vía WebSocket |
| RF-19 | Salud Sistema | El sistema debe exponer endpoints de health check y monitoreo |

---

## Matriz RF vs Casos de Prueba

| Requisito | Casos de Prueba | Happy Path | Error / Límite | Total |
|-----------|----------------|:----------:|:--------------:|:-----:|
| **RF-01** Autenticación | CP-001, CP-002, CP-003 | CP-001, CP-003 | CP-002 | 3 |
| **RF-02** Grabación VAD | CP-004, CP-005, CP-006 | CP-004, CP-005 | CP-006 | 3 |
| **RF-03** Transcripción Vivo | CP-007, CP-008 | CP-007 | CP-008 | 2 |
| **RF-04** Calibración VAD | CP-009, CP-010, CP-011 | CP-009, CP-010 | CP-011 | 3 |
| **RF-05** Prueba Micrófono | CP-012, CP-013 | CP-012 | CP-013 | 2 |
| **RF-06** Subir Audio | CP-014, CP-015, CP-016 | CP-014 | CP-015, CP-016 | 3 |
| **RF-07** Procesamiento FFmpeg | CP-017, CP-018, CP-019, CP-020 | CP-017, CP-018, CP-019 | CP-020 | 4 |
| **RF-08** Búsqueda RAG | CP-021, CP-022, CP-023 | CP-021, CP-022 | CP-023 | 3 |
| **RF-09** Chat Contextual | CP-024, CP-025 | CP-024 | CP-025 | 2 |
| **RF-10** Temas y Fondo | CP-026, CP-027 | CP-026, CP-027 | — | 2 |
| **RF-11** Zoom Interfaz | CP-028, CP-029 | CP-028 | CP-029 | 2 |
| **RF-12** Formateador IA | CP-030, CP-031, CP-032, CP-033 | CP-030, CP-031 | CP-032, CP-033 | 4 |
| **RF-13** Configuración | CP-034, CP-035, CP-036 | CP-034, CP-035, CP-036 | — | 3 |
| **RF-14** Chat Documentos | CP-037, CP-038 | CP-037 | CP-038 | 2 |
| **RF-15** Pipeline Audio | CP-039, CP-040 | CP-039, CP-040 | — | 2 |
| **RF-16** Traducción | CP-041, CP-042, CP-043, CP-044 | CP-041, CP-042, CP-043 | CP-044 | 4 |
| **RF-17** Gestión Transcripciones | CP-045, CP-046, CP-047 | CP-045, CP-046, CP-047 | — | 3 |
| **RF-18** Batch FFmpeg | CP-048, CP-049 | CP-048, CP-049 | — | 2 |
| **RF-19** Salud Sistema | CP-050, CP-051 | CP-050, CP-051 | — | 2 |
| | **TOTAL** | **34** | **17** | **51** |

---

## Detalle de Cobertura por Requisito

### RF-01: Autenticación
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-001 | Login exitoso con credentials | ✅ Happy Path |
| CP-002 | Login fallido por credenciales inválidas | ❌ Error |
| CP-003 | Login con Google OAuth | ✅ Happy Path |

### RF-02: Grabación VAD
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-004 | Iniciar grabación correctamente | ✅ Happy Path |
| CP-005 | Detener grabación y obtener transcripción | ✅ Happy Path |
| CP-006 | Error al grabar sin permiso de micrófono | ❌ Error |

### RF-03: Transcripción en Vivo
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-007 | Visualizar transcripción en tiempo real | ✅ Happy Path |
| CP-008 | Caída de conexión WebSocket durante transcripción | ❌ Error |

### RF-04: Calibración VAD
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-009 | Ajustar umbral de voz y guardar | ✅ Happy Path |
| CP-010 | Ajustar umbral de silencio | ✅ Happy Path |
| CP-011 | Valores fuera de rango | ⚠️ Límite |

### RF-05: Prueba Micrófono
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-012 | Verificar micrófono | ✅ Happy Path |
| CP-013 | Sin micrófono disponible | ❌ Error |

### RF-06: Subir Audio
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-014 | Subir MP3 y transcribir | ✅ Happy Path |
| CP-015 | Formato no soportado | ❌ Error |
| CP-016 | Archivo vacío o corrupto | ❌ Error |

### RF-07: Procesamiento FFmpeg
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-017 | Normalizar volumen | ✅ Happy Path |
| CP-018 | Eliminar silencios | ✅ Happy Path |
| CP-019 | Cambiar velocidad | ✅ Happy Path |
| CP-020 | Sin archivo seleccionado | ❌ Error |

### RF-08: Búsqueda RAG
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-021 | Buscar concepto existente | ✅ Happy Path |
| CP-022 | Buscar término sin resultados | ✅ Happy Path |
| CP-023 | Término muy corto (< 2 caracteres) | ⚠️ Límite |

### RF-09: Chat Contextual
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-024 | Pregunta sobre transcripción activa | ✅ Happy Path |
| CP-025 | Sin transcripción activa | ❌ Error |

### RF-10: Temas y Fondo
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-026 | Cambiar tema visual | ✅ Happy Path |
| CP-027 | Fondo personalizado | ✅ Happy Path |

### RF-11: Zoom Interfaz
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-028 | Ajustar zoom a 125% | ✅ Happy Path |
| CP-029 | Zoom fuera de rango | ⚠️ Límite |

### RF-12: Formateador IA
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-030 | Formatear transcripciones seleccionadas | ✅ Happy Path |
| CP-031 | Progreso WebSocket en tiempo real | ✅ Happy Path |
| CP-032 | Sin selección de archivos | ❌ Error |
| CP-033 | Caída de WebSocket | ❌ Error |

### RF-13: Configuración
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-034 | Guardar API key | ✅ Happy Path |
| CP-035 | Validar claves faltantes | ✅ Happy Path |
| CP-036 | Mostrar/ocultar clave secreta | ✅ Happy Path |

### RF-14: Chat Documentos
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-037 | Conversación con asistente | ✅ Happy Path |
| CP-038 | Mensaje vacío | ❌ Error |

### RF-15: Pipeline Audio
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-039 | Pipeline completo (BNR→ASR→Traducción) | ✅ Happy Path |
| CP-040 | Modo ASR only | ✅ Happy Path |

### RF-16: Traducción
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-041 | Detectar idioma | ✅ Happy Path |
| CP-042 | Traducir texto | ✅ Happy Path |
| CP-043 | Traducción batch | ✅ Happy Path |
| CP-044 | Sin API key configurada | ❌ Error |

### RF-17: Gestión Transcripciones
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-045 | Listar transcripciones | ✅ Happy Path |
| CP-046 | Seleccionar y ver transcripción | ✅ Happy Path |
| CP-047 | Eliminar transcripción | ✅ Happy Path |

### RF-18: Batch FFmpeg
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-048 | Conversión batch múltiples archivos | ✅ Happy Path |
| CP-049 | Descarga de archivo procesado | ✅ Happy Path |

### RF-19: Salud Sistema
| CP | Título | Tipo |
|:--:|--------|:----:|
| CP-050 | Health check backend | ✅ Happy Path |
| CP-051 | Root endpoint | ✅ Happy Path |

---

## Métricas de Cobertura

| Métrica | Valor |
|---------|:-----:|
| **Total Requisitos Funcionales** | 19 |
| **Requisitos con cobertura** | 19 |
| **Cobertura de requisitos** | **100%** |
| **Total Casos de Prueba** | 51 |
| **Casos Happy Path** | 34 (66.7%) |
| **Casos Error** | 13 (25.5%) |
| **Casos Límite** | 4 (7.8%) |
| **Promedio CP por RF** | 2.7 |
| **Mínimo CP por RF** | 2 |
| **Máximo CP por RF** | 4 |

---

## Leyenda

| Símbolo | Significado |
|:-------:|-------------|
| ✅ Happy Path | Flujo exitoso / funcionalidad esperada |
| ❌ Error | Flujo de error / validación negativa |
| ⚠️ Límite | Prueba de valores límite / frontera |
