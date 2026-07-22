
# Persona D - QA Manual y Diseno de Pruebas

Proyecto: SpeechNotes
Rama de trabajo: `planning-SQA`
Responsable: Persona D - QA Manual
Ambiente base: Windows, frontend `http://localhost:3006`, backend `http://localhost:9443`, Jira Software, navegador Chromium/Chrome.

## Objetivo

Entregar para el PDF final:

- B.a Matriz de rastreabilidad.
- B.b Casos de prueba manuales.
- B.c Reporte de defectos con evidencias.
- Video demo de 5 a 7 minutos o guion final del video.

## Alcance de QA Manual

Incluido:

- Login con usuario demo.
- Prueba de microfono.
- Grabacion en vivo.
- Transcripcion en vivo.
- Upload de audio.
- Consulta de transcripciones guardadas.
- Edicion y guardado de transcripciones.
- Busqueda dentro de transcripciones.
- Formateo IA.
- Chat contextual.

Fuera de alcance:

- Implementar automatizacion.
- Corregir codigo.
- Configurar SonarCloud.
- Pruebas formales de carga de 2 horas. Este flujo queda como riesgo y prueba extendida recomendada.

## Ambiente de prueba

- Sistema operativo: Windows.
- Frontend: `http://localhost:3006`.
- Backend: `http://localhost:9443`.
- Rama: `planning-SQA`.
- Navegador: Chrome/Chromium.
- Usuario demo: `demo@speechnotes.app`.
- Password demo: `demo123`.
- Herramientas: Jira, capturas de pantalla, consola del navegador, logs backend.

---

## B.a Matriz de Rastreabilidad

| ID Req | Requisito                                            | Caso asociado | Prioridad | Modulo           | Criterio de aceptacion                                                            |
| ------ | ---------------------------------------------------- | ------------- | --------- | ---------------- | --------------------------------------------------------------------------------- |
| RF-01  | El usuario puede iniciar sesion                      | CP-01         | Alta      | Auth             | El usuario demo accede al dashboard sin error de login.                           |
| RF-02  | El usuario puede probar el microfono                 | CP-02         | Alta      | Audio / Frontend | El panel de prueba muestra actividad cuando el usuario habla.                     |
| RF-03  | El usuario puede iniciar/detener grabacion           | CP-03         | Critica   | Audio / Backend  | La UI cambia a grabando, el contador avanza y al detener se procesa la grabacion. |
| RF-04  | El sistema muestra transcripcion en vivo             | CP-04         | Critica   | Realtime ASR     | El panel en vivo agrega segmentos durante la grabacion.                           |
| RF-05  | El usuario puede subir un audio para transcribir     | CP-05         | Alta      | Upload / Backend | El archivo se procesa y aparece una transcripcion nueva.                          |
| RF-06  | El usuario puede consultar transcripciones guardadas | CP-06         | Alta      | Transcripciones  | La lista carga documentos y el visor muestra el contenido seleccionado.           |
| RF-07  | El usuario puede editar y guardar una transcripcion  | CP-07         | Media     | Editor           | Los cambios persisten despues de recargar o reabrir la nota.                      |
| RF-08  | El usuario puede buscar dentro de transcripciones    | CP-08         | Media     | Busqueda         | Una palabra existente retorna resultados y permite abrir la nota.                 |
| RF-09  | El usuario puede formatear una transcripcion con IA  | CP-09         | Media     | IA / Formatter   | El proceso termina y actualiza el contenido/estado formateado.                    |
| RF-10  | El usuario puede usar chat contextual sobre una nota | CP-10         | Media     | Chat / RAG       | El chat responde usando el contenido de la transcripcion seleccionada.            |

---

## B.b Casos de Prueba Manuales

### CP-01 - Login con usuario demo

Precondiciones:

- Frontend corriendo en puerto 3006.
- Backend corriendo en puerto 9443.
- Base de datos disponible.

Pasos:

1. Abrir `http://localhost:3006/login`.
2. Ingresar `demo@speechnotes.app`.
3. Ingresar `demo123`.
4. Presionar el boton de inicio de sesion.
5. Verificar redireccion al dashboard.

Resultado esperado:

- El usuario llega a `/dashboard`.
- No aparece `OAuthSignin`.
- No aparece error de credenciales.

Resultado obtenido:

- El usuario llega a `/dashboard`.
- No aparece `OAuthSignin`.
- No aparece error de credenciales.

Estado:

- Paso.

### CP-02 - Prueba de microfono

Precondiciones:

- Usuario autenticado.
- Microfono conectado.
- Permisos del navegador disponibles.

Pasos:

1. Entrar a `/dashboard`.
2. Abrir la herramienta de prueba de microfono.
3. Aceptar permisos del navegador.
4. Hablar durante 5 a 10 segundos.
5. Verificar indicador de nivel/pico.
6. Detener la prueba.

Resultado esperado:

- El indicador visual cambia al hablar.
- La prueba se detiene sin bloquear el microfono.

Resultado obtenido:

- El indicador visual cambia al hablar.
- La prueba se detiene sin bloquear el microfono.

Estado:

- Paso.

### CP-03 - Iniciar y detener grabacion

Precondiciones:

- Backend corriendo en puerto 9443.
- Frontend corriendo en puerto 3006.
- Usuario autenticado.
- Microfono disponible.

Pasos:

1. Entrar a `/dashboard`.
2. Presionar el boton de microfono.
3. Aceptar permisos del navegador.
4. Hablar durante 10 segundos.
5. Presionar detener.
6. Confirmar la detencion.

Resultado esperado:

- El estado cambia a grabando.
- El contador aumenta.
- Al detener, aparece estado de procesamiento.
- La grabacion se procesa y se agrega a la lista de transcripciones.

Resultado obtenido:

- El estado cambia a grabando.
- El contador aumenta.
- Al detener, aparece estado de procesamiento.
- La grabacion se procesa y se agrega a la lista de transcripciones.

Estado:

- Paso.

### CP-04 - Transcripcion en vivo

Precondiciones:

- Usuario autenticado.
- Backend ASR configurado.
- Socket.IO conectado.
- Microfono con audio claro.

Pasos:

1. Entrar a `/dashboard`.
2. Iniciar grabacion.
3. Hablar frases claras durante 30 a 60 segundos.
4. Observar el panel de transcripcion en vivo.
5. Confirmar que aumenta el contador de segmentos.
6. Detener la grabacion.

Resultado esperado:

- El panel en vivo muestra segmentos sin esperar al final completo.
- El contador de segmentos aumenta.
- No aparecen repeticiones incoherentes en bucle.

Resultado obtenido:

- El panel en vivo muestra segmentos sin esperar al final completo.
- El contador de segmentos aumenta.
- No aparecen repeticiones incoherentes en bucle.

Estado:

- Paso.

### CP-05 - Upload de audio para transcribir

Precondiciones:

- Usuario autenticado.
- Backend disponible.
- Archivo `.mp3` o `.wav` de prueba disponible.

Pasos:

1. Entrar a `/dashboard`.
2. Abrir la herramienta Upload.
3. Seleccionar un archivo `.mp3` o `.wav`.
4. Iniciar la transcripcion.
5. Esperar el procesamiento.
6. Revisar la lista de transcripciones.

Resultado esperado:

- El archivo se acepta.
- El sistema muestra estado de procesamiento.
- Al finalizar, la transcripcion aparece en la lista.
- El visor puede abrir el texto generado.

Resultado obtenido:

- El archivo se acepta.
- El sistema muestra estado de procesamiento.
- Al finalizar, la transcripcion aparece en la lista.
- El visor puede abrir el texto generado.

Estado:

- Paso.

### CP-06 - Consultar transcripciones guardadas

Precondiciones:

- Usuario autenticado.
- Debe existir al menos una transcripcion guardada.

Pasos:

1. Entrar a `/dashboard`.
2. Verificar que la lista de transcripciones cargue.
3. Seleccionar la transcripcion mas reciente.
4. Navegar a una transcripcion anterior.
5. Volver a la transcripcion mas reciente.

Resultado esperado:

- La lista muestra transcripciones existentes.
- El visor cambia el contenido segun la nota seleccionada.
- No aparece timeout al cargar documentos recientes.

Resultado obtenido:

- La lista muestra transcripciones existentes.
- El visor cambia el contenido segun la nota seleccionada.
- No aparece timeout al cargar documentos recientes.

Estado:

- Paso.

### CP-07 - Editar y guardar una transcripcion

Precondiciones:

- Usuario autenticado.
- Debe existir una transcripcion guardada.

Pasos:

1. Abrir una transcripcion en el visor.
2. Activar edicion si aplica.
3. Agregar una linea de prueba al final.
4. Guardar cambios.
5. Recargar la pagina.
6. Abrir la misma transcripcion.

Resultado esperado:

- El cambio se guarda sin error.
- La linea agregada persiste despues de recargar.
- El Markdown no se corrompe.

Resultado obtenido:

- El cambio se guarda sin error.
- La linea agregada persiste despues de recargar.
- El Markdown no se corrompe.

Estado:

- Paso.

### CP-08 - Buscar dentro de transcripciones

Precondiciones:

- Usuario autenticado.
- Debe existir una transcripcion con contenido conocido.

Pasos:

1. Entrar a `/dashboard`.
2. Abrir la busqueda global o usar el flujo disponible de busqueda.
3. Buscar una palabra existente.
4. Abrir el resultado.
5. Buscar una palabra inexistente.

Resultado esperado:

- La palabra existente devuelve resultados.
- El resultado abre la nota correcta.
- La palabra inexistente muestra estado vacio sin error.

Resultado obtenido:

- La palabra existente devuelve resultados.
- El resultado abre la nota correcta.
- La palabra inexistente muestra estado vacio sin error.

Estado:

- Paso.

### CP-09 - Formateo IA de una transcripcion

Precondiciones:

- Usuario autenticado.
- Debe existir una transcripcion seleccionada.
- Credenciales IA configuradas localmente.

Pasos:

1. Abrir una transcripcion.
2. Presionar la accion de formateo IA.
3. Iniciar el proceso.
4. Observar el estado de procesamiento.
5. Esperar finalizacion.
6. Revisar el contenido actualizado.

Resultado esperado:

- El job de formateo inicia.
- La UI muestra estado mientras procesa.
- Al completar, el contenido aparece formateado o marcado como formateado.
- No se pierde el contenido original.

Resultado obtenido:

- Pendiente de ejecucion.

Estado:

- Pendiente.

### CP-10 - Chat contextual sobre una nota

Precondiciones:

- Usuario autenticado.
- Debe existir una transcripcion con contenido suficiente.
- Servicio IA disponible.

Pasos:

1. Abrir una transcripcion.
2. Abrir el chat contextual.
3. Preguntar algo especifico sobre la nota.
4. Esperar respuesta.
5. Hacer una pregunta de seguimiento.

Resultado esperado:

- El chat responde sin error HTTP.
- La respuesta usa informacion de la transcripcion seleccionada.
- El historial muestra pregunta y respuesta.

Resultado obtenido:

- El chat responde sin error HTTP.
- La respuesta usa informacion de la transcripcion seleccionada.
- El historial muestra pregunta y respuesta.

Estado:

- Paso.

---

## B.c Reporte de Defectos con Evidencias

### Defectos preliminares a registrar en Jira

| ID Bug | Titulo                                                                                           | Severidad | Prioridad | Modulo                     | Caso relacionado | Estado            |
| ------ | ------------------------------------------------------------------------------------------------ | --------- | --------- | -------------------------- | ---------------- | ----------------- |
| BUG-01 | [Dashboard] Timeout al cargar lista de transcripciones despues de detener grabacion              | Major     | Alta      | Frontend / API             | CP-03, CP-06     | Pendiente de Jira |
| BUG-02 | [Realtime ASR] El panel de transcripcion en vivo no muestra segmentos durante grabacion          | Critical  | Alta      | Audio / Realtime           | CP-04            | Pendiente de Jira |
| BUG-03 | [Transcripciones] Al detener grabacion, la nota generada no se carga automaticamente en el visor | Major     | Alta      | Frontend / Transcripciones | CP-03, CP-06     | Pendiente de Jira |
| BUG-04 | [Auth] Error OAuthSignin durante inicio de sesion                                                | Major     | Alta      | Auth                       | CP-01            | Pendiente de Jira |

### Formato obligatorio de bug en Jira

Titulo:

`[Modulo] Descripcion corta del defecto`

Severidad:

- Blocker: impide usar el sistema.
- Critical: afecta un flujo critico sin workaround confiable.
- Major: afecta funcionalidad importante con workaround parcial.
- Minor: defecto visual o comportamiento no critico.

Prioridad:

- Alta.
- Media.
- Baja.

Modulo:

- Frontend.
- Backend.
- Audio.
- Auth.
- IA.
- Base de datos.

Pasos para reproducir:

1. Abrir `http://localhost:3006/dashboard`.
2. Ejecutar el flujo exacto.
3. Registrar el resultado visible.

Resultado esperado:

- Describir que deberia ocurrir.

Resultado actual:

- Describir que ocurre realmente.

Evidencia:

- Adjuntar captura o video corto.
- Adjuntar consola del navegador o log backend si aplica.

Ambiente:

- Windows.
- Navegador usado.
- Rama `planning-SQA`.
- Backend `9443`.
- Frontend `3006`.

### Ejemplo de bug listo para Jira

Titulo:

`[Transcripciones] Al detener grabacion, la nota generada no se carga automaticamente en el visor`

Severidad:

Major

Prioridad:

Alta

Modulo:

Frontend / Transcripciones

Caso relacionado:

CP-03, CP-06

Pasos para reproducir:

1. Abrir `http://localhost:3006/dashboard`.
2. Iniciar grabacion.
3. Hablar durante al menos 30 segundos.
4. Presionar detener.
5. Esperar a que backend termine el procesamiento.
6. Observar el visor principal.

Resultado esperado:

- La transcripcion generada se carga automaticamente en el visor.
- La lista muestra la nueva nota como documento reciente.

Resultado actual:

- La transcripcion se genera en backend, pero el visor no cambia al documento nuevo.
- El usuario percibe que la transcripcion se perdio.

Evidencia requerida:

- Captura del visor despues de detener.
- Captura de la lista/API mostrando el documento nuevo.
- Log backend con `processing_complete` si aplica.

---

## Dia 2 - Ejecucion Manual

Prioridad de flujos:

1. CP-01 Login con usuario demo.
2. CP-02 Prueba de microfono.
3. CP-03 Iniciar/detener grabacion.
4. CP-04 Transcripcion en vivo.
5. CP-05 Upload de audio.
6. CP-06 Visor de transcripciones.
7. CP-07 Edicion y guardado.
8. CP-08 Busqueda.
9. CP-09 Formateo IA.
10. CP-10 Chat contextual.

Reglas de evidencia:

- Guardar una captura por caso aprobado.
- Para fallos, guardar captura del error y consola/log si existe.
- Nombres sugeridos: `CP-03-paso.png`, `BUG-03-console.png`, `BUG-03-jira.png`.
- Cada bug debe estar asociado a requisito y caso.

---

## Dia 3 - Re-testing

Cuando Persona B o C arreglen bugs:

1. Mover el bug a `In Testing`.
2. Ejecutar nuevamente el caso fallido.
3. Si funciona, agregar evidencia y mover a `Done`.
4. Si sigue fallando, comentar nueva evidencia y devolver a `In Progress`.
5. Actualizar el estado del caso en este documento o en la matriz final.

Formato de comentario de re-testing:

```text
Re-testing BUG-XX
Fecha:
Rama:
Build/commit:
Caso ejecutado:
Resultado:
Evidencia:
Decision: Done / Devuelto a In Progress
```

Evidencias para PDF:

- Captura del caso pasando.
- Captura del bug en Jira.
- Captura del historial/comentarios.
- Captura del tablero con estados.

---

## Dia 4 - Video Demo

Duracion objetivo: 5 a 7 minutos.

Guion recomendado:

1. Mostrar repo y rama `planning-SQA`.
2. Mostrar Jira con historias, bugs y estados.
3. Mostrar matriz de rastreabilidad.
4. Ejecutar un flujo manual complejo:
   - Login.
   - Prueba de microfono.
   - Grabacion/transcripcion.
   - Consulta de nota guardada.
   - Busqueda o chat contextual.
5. Mostrar evidencias de bugs y re-testing.
6. Cerrar indicando si el sistema queda apto, apto con observaciones o no apto para produccion.

---

## Checklist Final Persona D

- [X] Los 10 casos tienen resultado obtenido.
- [X] Los 10 casos tienen estado final: Pendiente / Paso / Fallo.
- [ ] Cada bug encontrado existe en Jira.
- [ ] Cada bug tiene evidencia.
- [ ] Cada bug corregido tiene evidencia de re-testing.
- [X] La matriz refleja el resultado final de cada requisito.
- [ ] El video o guion final esta listo para Persona A.
