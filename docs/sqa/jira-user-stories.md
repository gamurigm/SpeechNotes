# Guía de Gestión en Jira: Épicas, Historias de Usuario y Bugs (SpeechNotes)

En un proyecto de Aseguramiento de Calidad (SQA), utilizar Jira correctamente es fundamental para generar métricas automáticas y demostrar una metodología rigurosa. Esta guía explica cómo estructurar el proyecto *SpeechNotes* en Jira.

---

## 🏔️ 1. Épicas (Epics)

Una Épica es un bloque grande de trabajo que se puede dividir en tareas más pequeñas (Historias, Tareas o Bugs). Agrupa elementos que comparten un objetivo común.

**¿Cómo se debería llamar la Épica principal y qué debe cubrir?**
Para este proyecto de 1 semana, recomendamos tener **dos Épicas principales**:

1. **Épica 1: `SQA: Automatización y Análisis Estático`**
   - *Qué cubre:* Todo el esfuerzo técnico para integrar SonarCloud, configurar GitHub Actions y programar los tests automatizados (Cypress, Pytest).
2. **Épica 2: `SQA: Pruebas Funcionales y Documentación`**
   - *Qué cubre:* El esfuerzo de levantar el SQAP, diseñar casos de prueba manuales, ejecutar la app para cazar bugs y armar el reporte final.

*Nota:* Cada Tarea, Historia o Bug que creen debe estar enlazado a una de estas dos Épicas. Esto permitirá generar gráficos en Jira que mostrarán qué área requirió más esfuerzo.

---

## 📖 2. Historias de Usuario (User Stories)

Las Historias de Usuario describen una funcionalidad desde la perspectiva de quien la utilizará. Para QA, a menudo adaptamos esto para definir las "tareas técnicas de calidad" o los casos de prueba de negocio.

**Estructura Estándar:**
> **Como** [Rol/Usuario]
> **Quiero** [Acción/Funcionalidad]
> **Para** [Beneficio/Valor]

**Ejemplo aplicado a SpeechNotes (QA):**
> **Como** QA Automation Engineer (Persona C)
> **Quiero** tener un script E2E en Cypress que valide el inicio de grabación
> **Para** asegurar que la detección de voz (VAD) reacciona correctamente en el frontend sin intervención manual.

### ✅ Criterios de Aceptación (Acceptance Criteria)
Toda Historia **debe** tener criterios de aceptación. Son las reglas para decidir si la historia está "Done" (Terminada).
Se recomienda usar el formato *Given-When-Then* (Dado-Cuando-Entonces):
- **Dado** que el usuario está en la pantalla principal y tiene micrófono conectado
- **Cuando** presiona el botón "Iniciar Transcripción"
- **Entonces** el sistema debe pedir permisos de micrófono y el indicador de grabación debe encenderse.

---

## 🎯 3. Puntos de Usuario (Story Points)

Los Story Points no miden tiempo (horas), sino **esfuerzo, complejidad e incertidumbre**. Se suele usar la escala de Fibonacci: `1, 2, 3, 5, 8, 13, 21`.

**¿Cómo estimar en el equipo de 4 personas?**
- **1 Punto:** Tarea trivial, muy rápida y sin riesgos (Ej. Crear carpeta `Tests` en el repo).
- **3 Puntos:** Tarea normal, clara pero que toma cierto esfuerzo (Ej. Escribir 5 casos de prueba manuales).
- **5 Puntos:** Tarea compleja o con dependencias (Ej. Configurar SonarCloud con GitHub Actions desde cero).
- **8 Puntos:** Tarea muy compleja y larga. (Si una tarea tiene 8 puntos, **debe dividirse** en historias más pequeñas).

*Recomendación:* Cuando asignen tareas, discutan rápidamente cuántos puntos le dan. Al final del proyecto, Jira les dirá su "Velocidad" (Cuántos puntos lograron en la semana).

---

## 🐛 4. Bugs vs Historias vs Tareas (Issue Types en Jira)

Para generar las métricas de calidad (Punto C.a de su documento final), es CRÍTICO que usen los tipos de incidencias correctos en Jira:

- 📘 **Story / Task:** Úsenlo para trabajo a realizar (Escribir SQAP, hacer script de Cypress, configurar SonarQube).
- 🐞 **Bug:** Úsenlo ÚNICAMENTE cuando algo en *SpeechNotes* está roto o no funciona como debería.

### ¿Cómo escribir un Bug perfecto en Jira?
La **Persona D** (QA Manual) debe seguir esta estructura al levantar un Bug:
1. **Título:** [Módulo] Descripción corta del error. *(Ej. [Audio Pipeline] El botón de Denoise crashea al subir MP3).*
2. **Severidad (Custom field o Labels):** `Blocker`, `Critical`, `Major`, `Minor`.
3. **Pasos para Reproducir:**
   1. Abrir la app web.
   2. Subir el archivo `test.mp3`.
   3. Hacer clic en "Denoise".
4. **Resultado Esperado:** El audio debe limpiarse y poder descargarse en WAV.
5. **Resultado Actual:** La página se queda en blanco y la consola muestra Error 500.
6. **Evidencia:** Adjuntar Screenshot o pequeño video.

*Tip de Oro:* Agreguen **Etiquetas (Labels)** a los bugs como `Frontend`, `Backend`, o `BD`. Así, el Día 6, la Persona A podrá ir a Jira, buscar "Tipo: Bug + Label: Frontend" y calcular instantáneamente la *Densidad de Defectos por módulo*.
