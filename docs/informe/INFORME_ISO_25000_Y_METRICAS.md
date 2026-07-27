# Informe de alineación con ISO/IEC 25000 y métricas de calidad — SpeechNotes

**Proyecto:** SpeechNotes  
**Fecha de corte:** 22 de julio de 2026  
**Tipo de revisión:** análisis documental, inspección del repositorio y ejecución local de pruebas  
**Alcance:** backend Python/FastAPI, frontend Next.js/TypeScript, componentes de escritorio, transcripción y funciones asistidas por IA

> **Aclaración de alcance.** Este informe identifica alineación y evidencias frente a normas de calidad. No constituye una auditoría independiente, una certificación ISO ni una declaración formal de conformidad. Los umbrales indicados son criterios de aceptación propuestos para SpeechNotes; ISO/IEC 25023 no impone por sí sola valores universales de aprobación.

## 1. Resumen ejecutivo

SpeechNotes tiene una base de aseguramiento de calidad considerablemente madura para un proyecto académico: requisitos trazables, casos positivos y negativos, pruebas automatizadas de backend y frontend, pruebas E2E, análisis estático, control de cobertura y un *Quality Gate* dentro de CI/CD. Estas prácticas se relacionan directamente con la familia SQuaRE: ISO/IEC 25010:2023 aporta el modelo de calidad; ISO/IEC 25023:2016 orienta la medición; ISO/IEC 25030:2019 ayuda a convertir necesidades en requisitos cuantificables; e ISO/IEC 25040:2024 estructura la evaluación.

Los puntos más fuertes evidenciados son:

- **Adecuación funcional:** 19 de 19 requisitos funcionales tienen al menos un caso asociado; existen 51 casos diseñados y cada requisito posee entre 2 y 4 casos.
- **Mantenibilidad:** el repositorio separa responsabilidades, usa pruebas unitarias y de integración, linting, SonarCloud, reportes de cobertura y dependencias bloqueadas.
- **Seguridad:** existen autenticación, pruebas de rutas y validación, análisis estático de seguridad y un *Quality Gate*. El cierre histórico reportó calificación A y cero incidencias de seguridad abiertas.
- **Fiabilidad y capacidad de recuperación:** hay comprobación de salud, pruebas de errores de WebSocket, entradas inválidas, servicios externos y escenarios sin micrófono o sin claves.
- **Evaluación repetible:** GitHub Actions ejecuta pytest, Jest, Cypress y SonarCloud, y conserva artefactos como cobertura, JUnit, videos y capturas.
- **Calidad para componentes de IA:** existen adaptadores, proveedores sustituibles y pruebas con dobles; esto es una buena base para ISO/IEC 25059, aunque todavía no se miden WER, alucinación, fidelidad RAG ni desempeño por idioma.

La principal conclusión es que el proyecto **está bien alineado en prácticas**, pero su evidencia cuantitativa es desigual. Las cifras históricas del cierre SQA son favorables en cobertura de código y análisis estático; sin embargo, la ejecución local del 22 de julio de 2026 encontró una falla en backend y otra en frontend por falta de aislamiento de variables sensibles. Tampoco hay series actuales de latencia, disponibilidad, usabilidad o exactitud de transcripción. Por ello, el estado global se clasifica como **alineación parcial-alta, con brechas de medición operativa y aislamiento de pruebas**.

## 2. Normas aplicables y relación con el proyecto

| Norma | Aporte al proyecto | Evidencia o aplicación en SpeechNotes |
|---|---|---|
| [ISO/IEC 25000:2014](https://www.iso.org/standard/64764.html) | Guía y vocabulario general de SQuaRE. | Permite ordenar el SQAP, los requisitos, las medidas y la evaluación bajo un mismo marco. |
| [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) | Modelo vigente de calidad del producto con nueve características. | La sección 3 relaciona adecuación funcional, eficiencia de desempeño, compatibilidad, capacidad de interacción, fiabilidad, seguridad, mantenibilidad, flexibilidad y seguridad operacional con evidencias del repositorio. |
| [ISO/IEC 25023:2016](https://www.iso.org/standard/35747.html) | Medidas cuantitativas para las características de producto. Su revisión está en curso a la fecha de corte. | Base metodológica del catálogo de métricas de la sección 5. Los límites de aceptación se definen para el contexto de SpeechNotes. |
| [ISO/IEC 25030:2019](https://www.iso.org/standard/72116.html) | Marco para elicitar, definir y gobernar requisitos de calidad medibles. | Se usa al convertir atributos generales en fórmula, fuente, frecuencia, meta y responsable. |
| [ISO/IEC 25040:2024](https://www.iso.org/standard/83467.html) | Marco vigente para planificar y ejecutar evaluaciones de productos, datos y servicios TI. | El proyecto ya conserva plan, criterios, resultados y evidencias; falta formalizar revisión periódica y decisión de aceptación. |
| [ISO/IEC 25012:2008](https://www.iso.org/standard/35736.html) | Modelo de calidad de datos, confirmado como vigente en 2025. | Aplica a transcripciones, metadatos, embeddings y documentos; aún faltan medidas de completitud, exactitud, consistencia y trazabilidad del dato. |
| [ISO/IEC 25059:2023](https://www.iso.org/standard/80655.html) | Extensión SQuaRE para sistemas de IA. | Aplica al ASR, traducción, formateo y RAG. Hay arquitectura y pruebas funcionales, pero no un conjunto de evaluación de IA versionado. |
| [ISO/IEC/IEEE 29119-2:2021](https://www.iso.org/standard/79428.html) | Procesos de gobierno, gestión e implementación de pruebas. | Casos identificados, matriz RF–CP, criterios de entrada/salida, automatización y registros de defectos. |
| [ISO/IEC/IEEE 12207:2026](https://www.iso.org/standard/90219.html) | Marco vigente de procesos del ciclo de vida del software. | Git, CI/CD, desarrollo, prueba, operación y mantenimiento están presentes; falta hacer explícita la medición continua y el retiro/gestión operativa. |
| [ISO/IEC 27001:2022](https://www.iso.org/standard/27001) | Gestión de riesgos para confidencialidad, integridad y disponibilidad. | Autenticación, manejo de configuración, análisis estático y pruebas de seguridad. No existe evidencia suficiente para afirmar conformidad con un SGSI completo. |
| [ISO 9241-11:2018](https://www.iso.org/standard/63500.html) | Usabilidad entendida como resultado de uso en un contexto definido. | La interfaz incorpora temas, zoom, estados, mensajes y prueba de micrófono; faltan pruebas con usuarios y métricas de eficacia, eficiencia y satisfacción. |
| [IEEE 730](https://standards.ieee.org/ieee/730/5284/) | Procesos y planificación de aseguramiento de calidad. | El SQAP local se apoya en IEEE 730-1998. Esa edición está superada; se recomienda actualizar la referencia y realizar un análisis de cambios respecto de la edición/proyecto vigente. |

## 3. ISO/IEC 25010:2023: puntos a favor y evidencia actual

| Característica | Puntos a favor evidenciados | Estado | Evidencia principal |
|---|---|:---:|---|
| **Adecuación funcional** | Requisitos enumerados, matriz bidireccional RF–CP, 51 casos con resultados esperados y cobertura de caminos exitosos, errores y límites. | **Fuerte** | `docs/test/matriz_rastreabilidad.md`, `docs/test/casos_de_prueba.md` |
| **Eficiencia de desempeño** | Arquitectura de streaming mediante WebSocket/Socket.IO, VAD y procesamiento por lotes; hay pruebas funcionales de esos flujos. | **Débil/no medida** | Código de `backend/services/realtime/`, `web/utils/socket.ts`; no se hallaron percentiles de latencia, uso de recursos ni capacidad. |
| **Compatibilidad** | API REST, WebSocket, frontend web, Electron y Tauri; proveedores NIM encapsulados mediante protocolos/adaptadores. | **Parcial** | `desktop/`, `web/src-tauri/`, `backend/services/nim/protocols.py`, `registry.py` |
| **Capacidad de interacción** | Pantallas de login, dashboard, estados de grabación, visualizador Markdown, temas, fondos, zoom y mensajes de error; casos manuales y E2E. | **Parcial** | `web/app/`, `web/tests/e2e/`, capturas del SQAP; no existen pruebas formales con usuarios. |
| **Fiabilidad** | Health check, manejo de pérdida de WebSocket, pruebas de entrada corrupta, ausencia de permisos, fallos de proveedores y persistencia. Uso de mocks para reducir dependencia externa. | **Parcial-fuerte** | `backend/tests/test_health.py`, `test_websocket_router.py`, `test_socket_handler_unit.py`, `docs/sqa/.../14_gestion_riesgos.tex` |
| **Seguridad** | NextAuth, pruebas de autenticación, validación de rutas, variables de entorno, SAST y control del *Quality Gate*. | **Parcial-fuerte** | `backend/utils/auth.py`, `src/core/path_security.py`, pruebas asociadas, `sonar-project.properties`, workflow de CI. La ejecución actual reveló aislamiento insuficiente de secretos. |
| **Mantenibilidad** | Arquitectura modular, patrones documentados, linters, 362 pruebas backend recolectadas, 42 pruebas frontend ejecutadas, cobertura y duplicación históricas controladas. | **Fuerte con reservas** | `docs/patrones_diseno.md`, suites `backend/tests/` y `web/tests/`, SonarCloud y CI/CD. Hay exclusiones amplias de cobertura y complejidad que deben revisarse. |
| **Flexibilidad** | Configuración por entorno, registro de proveedores NIM, interfaces/protocolos, rutas y servicios separados, versiones web y escritorio. | **Parcial-fuerte** | `.env.example`, `backend/services/nim/registry.py`, `protocols.py`, `src/core/environment_factory.py` |
| **Seguridad operacional (*safety*)** | Hay validaciones de límites y manejo de errores; el dominio no parece ser crítico para vida o integridad física. | **No demostrada** | No se encontró análisis específico de peligros, uso indebido de IA o consecuencias de transcripciones incorrectas. Debe definirse según el contexto real de uso. |

### Valoración de los puntos a favor

La mayor fortaleza no es una cifra aislada, sino la **cadena de evidencia**: requisito → caso de prueba → ejecución → defecto → corrección/reprueba → control automatizado. Esa cadena es coherente con SQuaRE, 29119 y 12207. También es positivo que el pipeline haga depender SonarCloud de las pruebas de backend y frontend y publique artefactos aun cuando un trabajo falla.

No obstante, una lista de casos diseñada no equivale a evidencia de ejecución, y una captura histórica no equivale a estado actual. El proyecto debe conservar ambas cosas con fecha, versión/commit, ambiente y responsable.

## 4. Evidencia histórica frente a medición actual

### 4.1 Línea base histórica documentada en el cierre SQA (18–21 de julio de 2026)

El archivo `docs/sqa/speechNotes_sqap/apendices/E_informe_cierre.tex` reporta:

- 10/10 requisitos del alcance original cubiertos.
- 17/17 casos manuales ejecutados.
- 13 casos aprobados y 4 fallidos: **76,47 % de aprobación**.
- 8 defectos encontrados y 3 corregidos: **37,5 % de cierre**.
- 100 % de defectos críticos corregidos, 50 % de mayores y 20 % de menores.
- Cobertura SonarCloud de **90,4 %**, duplicación de **0,5 %**, calificación de seguridad **A**, 0 incidencias abiertas y *Quality Gate* aprobado.

Estas cifras se aceptan como **evidencia histórica documentada**, respaldada por el SQAP y capturas, no como una medición reproducida durante esta revisión.

### 4.2 Alcance funcional documental vigente

La matriz `docs/test/matriz_rastreabilidad.md` amplía el alcance a:

- 19 requisitos funcionales, todos con casos asociados: **100 % de cobertura de diseño**.
- 51 casos diseñados: 34 exitosos, 13 de error y 4 de límite.
- Entre 2 y 4 casos por requisito, con promedio de 2,7.

Esta métrica acredita **cobertura del diseño de pruebas**, no que los 51 casos hayan sido ejecutados ni aprobados.

### 4.3 Ejecución local realizada el 22 de julio de 2026

| Suite | Recolectados | Aprobados | Fallidos | Omitidos | Tasa sobre ejecutados | Resultado |
|---|---:|---:|---:|---:|---:|:---:|
| Backend pytest | 362 | 251 | 1 | 110 | 251 / 252 = **99,60 %** | No cumple el criterio de suite verde |
| Frontend Jest | 42 | 41 | 1 | 0 | 41 / 42 = **97,62 %** | No cumple el criterio de suite verde |
| Consolidado ejecutado | 294 | 292 | 2 | 110 | 292 / 294 = **99,32 %** | No cumple el criterio de suite verde |

Comandos usados:

```text
python -m pytest backend/tests -q --disable-warnings
npm test -- --coverage --runInBand
```

Observaciones relevantes:

1. Ambas fallas se relacionaron con variables sensibles presentes en el ambiente local. Un test que esperaba ausencia de clave realizó una llamada real a un proveedor externo; el test de configuración del frontend heredó secretos que esperaba vacíos.
2. La salida de Jest llegó a mostrar valores sensibles. No se reproducen en este documento. Si eran credenciales reales, deben rotarse y debe redactarse/sanitizarse la salida de pruebas.
3. El backend se ejecutó con Python 3.14.3, mientras el pipeline declara Python 3.11; el resultado local no reemplaza el del entorno objetivo.
4. Las 110 omisiones corresponden principalmente a pruebas de integración que requieren servicios. Deben ejecutarse en CI con el ambiente declarado o clasificarse explícitamente como optativas.
5. El comando npm actual no propagó correctamente la opción de cobertura al Jest interno; por ello no se generó una cobertura frontend nueva y verificable en esta revisión.

## 5. Documento de métricas de calidad

### 5.1 Reglas de medición

Cada registro debe incluir: identificador, nombre, objetivo de calidad, definición, fórmula, unidad, fuente, versión o commit, ambiente, responsable, fecha, umbral, resultado y decisión. Los resultados se conservarán como artefactos de CI. Una métrica sin fecha, fuente o denominador no se utilizará para autorizar una versión.

Estados usados:

- **Cumple:** existe medición válida y alcanza el umbral.
- **No cumple:** existe medición válida y no alcanza el umbral.
- **Histórico:** alcanzó el umbral en una evidencia previa, pero debe reproducirse para el commit actual.
- **No medido:** existe evidencia cualitativa, pero falta una medición suficiente.

### 5.2 Catálogo, justificación, cumplimiento y evidencia

| ID | Métrica y definición | Fórmula / unidad | Justificación ISO y meta de SpeechNotes | Resultado al corte | Cumplimiento y evidencia |
|---|---|---|---|---|---|
| **M-01** | **Cobertura de requisitos por diseño:** proporción de RF con al menos un CP asociado. | `RF cubiertos / RF totales × 100` | Adecuación funcional y trazabilidad. **Meta: 100 %.** | 19/19 = **100 %** | **Cumple.** `docs/test/matriz_rastreabilidad.md`. No prueba ejecución. |
| **M-02** | **Profundidad mínima de prueba:** menor número de CP asociados a un RF. | `mínimo(CP por RF)` | Evita requisitos con cobertura nominal de un solo escenario. **Meta: ≥ 2 CP/RF y al menos un escenario negativo/límite para funciones críticas.** | Mínimo **2**; 17/51 casos son de error o límite. | **Cumple parcialmente.** La cantidad cumple; algunos RF no tienen caso negativo. Matriz RF–CP. |
| **M-03** | **Tasa de aprobación backend:** pruebas aprobadas entre pruebas realmente ejecutadas. Omitidas no entran al denominador y se reportan aparte. | `pasadas / (pasadas + fallidas + errores) × 100` | Fiabilidad y ausencia de regresiones. **Meta CI: 100 %.** | 251/252 = **99,60 %**; 110 omitidas. | **No cumple.** Ejecución local del 22/07/2026. |
| **M-04** | **Tasa de aprobación frontend:** pruebas Jest aprobadas entre ejecutadas. | Igual a M-03 | Fiabilidad y capacidad de interacción. **Meta CI: 100 %.** | 41/42 = **97,62 %**. | **No cumple.** Ejecución local del 22/07/2026. |
| **M-05** | **Tasa de ejecución automatizada:** pruebas no omitidas sobre pruebas recolectadas. | `(pasadas + fallidas + errores) / recolectadas × 100` | Distingue cobertura ejecutada de inventario de pruebas. **Meta backend en CI completo: ≥ 90 %.** | 252/362 = **69,61 %**. | **No cumple en ambiente local.** Debe medirse en CI con servicios; pytest reportó 110 omisiones. |
| **M-06** | **Cobertura de código:** instrucciones/líneas cubiertas por pruebas sobre total instrumentado. | `elementos cubiertos / elementos medibles × 100` | Mantenibilidad y capacidad de prueba. **Meta: ≥ 80 % global y ≥ 70 % por componente crítico.** | **90,4 % histórico**; no reproducido al corte. | **Histórico: cumple. Actual: no verificado.** Captura `docs/informe/images/coverage-90.png` y Apéndice D. Revisar las exclusiones de `sonar-project.properties`. |
| **M-07** | **Duplicación de código:** líneas duplicadas respecto del total analizado. | `líneas duplicadas / líneas analizadas × 100` | Mantenibilidad y modificabilidad. **Meta: ≤ 3 %.** | **0,5 % histórico**. | **Histórico: cumple.** Apéndice D de análisis estático. |
| **M-08** | **Incidencias estáticas abiertas por severidad:** hallazgos de calidad/seguridad no resueltos. | Conteo por severidad; unidad: incidencias | Seguridad y mantenibilidad. **Meta de liberación: 0 bloqueantes/críticas y 0 vulnerabilidades altas; las demás con aceptación de riesgo.** | 0 incidencias y seguridad A, históricos. | **Histórico: cumple.** SonarCloud/Apéndice D; debe reproducirse por commit. Las reglas excluidas requieren revisión documentada. |
| **M-09** | **Aprobación del Quality Gate:** decisión automatizada que agrupa umbrales. | Booleano: aprobado/rechazado | Control objetivo de aceptación conforme a 25040. **Meta: aprobado.** | Aprobado en cierre histórico; workflow configurado actualmente. | **Histórico/configurado.** `.github/workflows/sonar.yml`, `sonar-project.properties`. Falta enlazar la ejecución del commit revisado. |
| **M-10** | **Tasa de cierre de defectos:** defectos cerrados y verificados respecto de encontrados. | `defectos cerrados verificados / defectos encontrados × 100` | Fiabilidad y mejora. **Meta de release: 100 % de críticos y mayores; ≥ 80 % total o riesgo aceptado.** | 3/8 = **37,5 %** total; críticos 1/1 = 100 %; mayores 1/2 = 50 %. | **No cumple global ni mayores; cumple críticos.** `E_informe_cierre.tex` y reporte de defectos. |
| **M-11** | **Latencia de transcripción en vivo p95:** tiempo desde recepción de audio hasta presentación del texto parcial. | Percentil 95 de `t_texto - t_audio`; milisegundos | Eficiencia de desempeño y experiencia en tiempo real. **Meta inicial propuesta: p95 ≤ 2 000 ms, error < 1 %.** | Sin datos. | **No medido.** Instrumentar timestamps correlacionados en WebSocket/Socket.IO y reportar por sesión. |
| **M-12** | **Disponibilidad del servicio:** proporción de tiempo en que health y flujo crítico están operativos. | `(tiempo total - indisponibilidad no planificada) / tiempo total × 100` | Fiabilidad y disponibilidad. **Meta inicial mensual: ≥ 99,5 %.** | Solo existe health check, sin serie temporal. | **No medido.** `backend/tests/test_health.py` y endpoint `/health` son base, no evidencia de disponibilidad mensual. |
| **M-13** | **Tasa de reconexión exitosa:** sesiones WebSocket recuperadas sin pérdida indebida de estado. | `reconexiones exitosas / desconexiones simuladas × 100` | Fiabilidad y recuperabilidad. **Meta: ≥ 99 % en prueba controlada.** | Hay escenarios y pruebas, sin tasa consolidada. | **No medido.** Casos CP-008/CP-033 y pruebas de socket. |
| **M-14** | **Exactitud ASR mediante WER:** sustituciones, borrados e inserciones respecto de palabras de referencia. Menor es mejor. | `(S + D + I) / N × 100` | Adecuación funcional, ISO/IEC 25059 y calidad del dato. **Meta inicial propuesta para audio limpio en español: WER ≤ 15 %; definir metas separadas por ruido, acento e idioma.** | Sin corpus de referencia versionado. | **No medido.** Crear conjunto de audio y transcripción humana, con licencia, versión y estratos. |
| **M-15** | **Fidelidad de respuestas RAG/IA:** respuestas cuyas afirmaciones están respaldadas por el documento activo. | `respuestas respaldadas / respuestas evaluadas × 100` | Calidad de IA, corrección y prevención de alucinaciones. **Meta inicial: ≥ 95 %; 0 afirmaciones inventadas en preguntas fuera de contexto.** | Hay reglas en el prompt y pruebas unitarias, no evaluación de contenido. | **No medido.** `backend/services/agents/pydantic_agent.py`, `test_rag_agent.py`, `test_pydantic_agent.py`. |
| **M-16** | **Completitud de metadatos de transcripción:** registros con ID, origen/fecha, idioma, estado y contenido requeridos. | `registros completos / registros evaluados × 100` | ISO/IEC 25012: completitud, consistencia y trazabilidad del dato. **Meta: 100 % en campos obligatorios.** | Sin reporte. | **No medido.** Repositorios, esquema Prisma y pruebas de transcripciones son fuentes candidatas. |
| **M-17** | **Eficacia de tareas de usuario:** usuarios que completan una tarea crítica sin ayuda. | `usuarios que completan / usuarios participantes × 100`; además tiempo y SUS | Capacidad de interacción e ISO 9241-11. **Meta inicial: ≥ 90 % de éxito; SUS ≥ 80.** | Capturas y casos manuales, sin estudio con usuarios. | **No medido.** Evaluar login, grabación, transcripción, búsqueda y exportación con contexto de uso definido. |
| **M-18** | **Aislamiento de pruebas respecto de secretos y red externa:** ejecuciones que no leen secretos reales ni hacen llamadas no simuladas. | `pruebas aisladas / pruebas que acceden a configuración o proveedores × 100` | Seguridad, repetibilidad y fiabilidad del proceso. **Meta: 100 %.** | Se observaron al menos dos fallas por herencia de entorno y una llamada real no deseada. | **No cumple cualitativamente; denominador aún no inventariado.** Tests de `ConfigManager` y `pydantic_agent`. |

### 5.3 Ficha mínima que debe conservar cada medición

```yaml
metric_id: M-03
name: tasa_aprobacion_backend
commit: <sha completo>
timestamp_utc: <fecha-hora>
environment: python-3.11 / ubuntu-latest
scope: backend/tests
passed: 0
failed: 0
errors: 0
skipped: 0
value_percent: 0.0
threshold_percent: 100.0
status: cumple | no_cumple
artifact: <URL o ruta del JUnit/coverage/log sanitizado>
owner: QA
notes: <exclusiones y riesgos aceptados>
```

### 5.4 Periodicidad y responsables propuestos

| Momento | Métricas | Responsable | Evidencia obligatoria |
|---|---|---|---|
| Cada *push*/PR | M-03 a M-09 y M-18 | Desarrollo + QA | JUnit, cobertura, Sonar, logs sanitizados y SHA |
| Cada sprint | M-01, M-02, M-10 y M-16 | QA Lead + Product Owner | Matriz RF–CP, defectos y reporte de datos |
| Antes de liberar | Todas las de release; especialmente M-03, M-04, M-08, M-09, M-10, M-14 y M-15 | Comité de aceptación | Acta con cumplimiento, excepciones y riesgo residual |
| Operación mensual | M-11 a M-13 | Operaciones | Dashboard exportado, incidentes y SLO |
| Cambio de modelo/corpus/prompt | M-14 y M-15 | Responsable IA + QA | Dataset versionado, resultados por segmento y comparación con línea base |

## 6. Brechas y acciones prioritarias

1. **Aislar pruebas y secretos (prioridad crítica).** Construir un archivo de entorno exclusivo para test, limpiar explícitamente todas las variables sensibles en *fixtures*, bloquear llamadas de red no simuladas y sanitizar los reportes. Rotar cualquier credencial real que haya aparecido en logs.
2. **Restablecer suites verdes.** Corregir el aislamiento que causa las dos fallas y ejecutar backend bajo Python 3.11, Jest con cobertura y Cypress en el mismo commit.
3. **Unificar el alcance.** Explicar formalmente el paso de 10 RF/17 CP históricos a 19 RF/51 CP actuales y agregar estado de ejecución, resultado, fecha y evidencia a cada CP.
4. **Medir la calidad central del producto.** Sin WER, latencia y fidelidad RAG no se puede demostrar cuantitativamente la calidad de una aplicación cuyo propósito es transcribir y asistir con IA.
5. **Crear SLO operativos.** Medir latencia p50/p95/p99, disponibilidad, errores, reconexión y consumo de recursos con datos sanitizados.
6. **Evaluar usabilidad.** Ejecutar tareas con usuarios representativos y registrar éxito, tiempo, errores y satisfacción; las capturas de pantalla por sí solas no demuestran usabilidad.
7. **Revisar exclusiones Sonar.** Documentar propietario, razón, caducidad y riesgo de cada exclusión de cobertura o regla; evitar que una cifra global alta oculte componentes críticos sin instrumentar.
8. **Actualizar referencias normativas.** Reemplazar la referencia central a IEEE 730-1998 y mantener en el SQAP las ediciones vigentes o el motivo documentado de conservar una anterior.

## 7. Guion breve para conferencia (3–4 minutos)

> SpeechNotes es una plataforma de transcripción inteligente que combina captura de audio, detección de voz, transcripción en tiempo real, traducción, búsqueda semántica y chat sobre documentos. Durante el trabajo de calidad no solo se probaron pantallas: se construyó una cadena de trazabilidad entre requisitos, casos, defectos y automatización.
>
> Al relacionar el proyecto con la familia ISO/IEC 25000, usamos ISO 25010 como mapa de las características de calidad, ISO 25023 para pensar en medidas, ISO 25030 para formular requisitos cuantificables e ISO 25040 para organizar la evaluación. También consideramos ISO 25059 por los componentes de inteligencia artificial, ISO 25012 por la calidad de las transcripciones como datos, ISO 29119 para el proceso de pruebas e ISO 27001 para riesgos de seguridad.
>
> Los resultados favorables son claros. La matriz actual cubre los 19 requisitos funcionales con 51 casos diseñados, incluyendo caminos exitosos, errores y valores límite. El proyecto dispone de pytest, Jest, Cypress, SonarCloud y un pipeline que guarda cobertura y evidencias. El cierre SQA documentó 90,4 % de cobertura, 0,5 % de duplicación, calificación de seguridad A y un Quality Gate aprobado.
>
> También encontramos brechas que no debemos ocultar. En la verificación actual, backend aprobó 251 de 252 pruebas ejecutadas y frontend 41 de 42. Las dos fallas mostraron falta de aislamiento del entorno de pruebas y una de ellas provocó una llamada externa no deseada. Además, todavía no se miden de manera sistemática la latencia, la disponibilidad, la usabilidad, el WER de la transcripción ni la fidelidad de las respuestas de IA.
>
> Por tanto, la conclusión no es que SpeechNotes esté certificado por ISO, sino que posee una alineación práctica importante y una base verificable. El siguiente salto de madurez consiste en mantener las suites verdes, proteger completamente los secretos y convertir las cualidades principales del producto en métricas continuas con fórmula, umbral, responsable y evidencia por cada versión.

## 8. Conclusión final

SpeechNotes evidencia buenas prácticas compatibles con ISO/IEC 25000: trazabilidad funcional completa en diseño, pruebas multicapas, gestión de defectos, análisis estático y automatización del control de calidad. Sus fortalezas principales se concentran en adecuación funcional, mantenibilidad, seguridad técnica y disciplina de evaluación.

El cumplimiento de las métricas no es homogéneo. M-01 cumple; M-02 cumple parcialmente; M-03, M-04, M-05, M-10 y M-18 no cumplen al corte; M-06 a M-09 cuentan con cumplimiento histórico que debe reproducirse; y M-11 a M-17 permanecen sin medición suficiente. En consecuencia, el proyecto puede presentarse como **bien encaminado y sustentado por evidencia**, pero no como conforme integralmente con ISO/IEC 25010 ni certificado bajo alguna norma.

La recomendación inmediata es usar este catálogo como anexo vivo del SQAP: actualizarlo automáticamente en CI, vincular cada resultado a un commit y no aprobar una liberación sin evidencia vigente de las métricas críticas.

## 9. Fuentes y evidencias consultadas

### Fuentes internas

- `README.md`
- `docs/test/matriz_rastreabilidad.md`
- `docs/test/casos_de_prueba.md`
- `docs/QA/BACKEND_TESTS.md`
- `docs/sqa/speechNotes_sqap/secciones/05_estandares_metricas.tex`
- `docs/sqa/speechNotes_sqap/secciones/06_pruebas.tex`
- `docs/sqa/speechNotes_sqap/secciones/09_control_codigo.tex`
- `docs/sqa/speechNotes_sqap/secciones/14_gestion_riesgos.tex`
- `docs/sqa/speechNotes_sqap/apendices/D_analisis_estatico.tex`
- `docs/sqa/speechNotes_sqap/apendices/E_informe_cierre.tex`
- `.github/workflows/sonar.yml`
- `sonar-project.properties`, `pytest.ini`, `web/package.json`
- Suites `backend/tests/`, `web/tests/unit/` y `web/tests/e2e/`

### Fuentes normativas oficiales

Las páginas oficiales enlazadas en la sección 2 fueron consultadas el 22 de julio de 2026. Se emplearon sus resúmenes públicos para confirmar objeto, edición y estado; no se reproduce contenido normativo protegido ni se sustituye la consulta de los textos completos licenciados.
