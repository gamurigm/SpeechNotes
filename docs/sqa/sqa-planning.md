# Plan Asincrónico Riguroso SQA - SpeechNotes (1 Semana)

Este plan está diseñado para cubrir **estrictamente cada punto de la rúbrica y estructura documental** solicitada en la guía. Se detalla el uso de Jira para gestión de incidencias y la responsabilidad exacta sobre cada sección del PDF final.

**Plataforma CI/CD:** GitHub Actions + SonarCloud (Online)
**Gestor de Bugs y Tareas:** Jira Software
**Equipo:** 4 Personas (A, B, C, D)

---

## 👥 Asignación de Roles y Checklist Riguroso

### 📝 Persona A: QA Lead & Test Manager (Responsable del Documento Final)
*Objetivo:* Asegurar la calidad metodológica, integrar las evidencias y redactar las conclusiones. Responsable de la **Sección A, C y D** del PDF.

- [ ] **Tarea A.1: Configuración de Jira y Proyecto (Día 1)**
  - Crear un proyecto en Jira (tipo "Bug Tracking" o "Scrum").
  - Configurar un flujo simple: `To Do` -> `In Progress` -> `In Testing` -> `Done`.
  - Invitar al resto del equipo a Jira.
- [ ] **Tarea A.2: Redacción del SQAP - Sección A (Día 1-2)**
  - **A.a. Alcance:** Redactar detalladamente qué módulos se probarán (ej. *API de transcripción, interfaz de grabación*) y cuáles NO (ej. *algoritmos internos de los modelos NIM*), justificando el porqué.
  - **A.b. Estrategia:** Definir tipos de prueba (E2E, Unitarias) y establecer los *Entry/Exit Criteria* formales.
  - **A.c. Herramientas:** Justificar Jira (gestión), SonarCloud+GitHub Actions (análisis estático), Pytest (Backend) y Cypress (Frontend).
  - **A.d. Gestión de Riesgos:** Documentar riesgos del producto (ej. latencia de IA) y riesgos de prueba (ej. cuellos de botella en automatización).
- [ ] **Tarea A.3: Informe de Cierre - Sección C (Día 6)**
  - Recolectar datos de Jira y herramientas de testeo.
  - **C.a. Métricas:** Calcular el % de Casos Pasados vs Fallados y la Densidad de Defectos (bugs por módulo: Backend vs Frontend).
- [ ] **Tarea A.4: Conclusiones - Sección D y Ensamblaje PDF (Día 7)**
  - Redactar la valoración crítica (*"¿SpeechNotes está listo para salir a producción según su calidad actual?"*).
  - Unir el trabajo de B, C y D en un único PDF estructurado y formal.

### ⚙️ Persona B: QA Automation Backend & CI/CD
*Objetivo:* Pruebas del Backend, métricas de SonarQube y despliegue del pipeline. Responsable de evidencias para la **Sección B**.

- [ ] **Tarea B.1: Pipeline GitHub Actions y SonarCloud (Día 1)**
  - Crear archivo `.github/workflows/sonar.yml` para ejecutar SonarCloud al hacer push.
  - Enlazar el repositorio de GitHub con SonarCloud.
- [ ] **Tarea B.2: Análisis Estático "Antes" - Evidencia B.d (Día 2)**
  - Tomar captura del primer reporte de SonarCloud mostrando vulnerabilidades, code smells y deuda técnica del código Legacy.
- [ ] **Tarea B.3: Pruebas Backend - Carpeta `Tests` (Día 3-5)**
  - Crear script de `pytest` (ej. `backend/tests/test_api.py`).
  - Probar funcionalidad de endpoints principales (Mock de los NIM si es necesario).
  - Subir código de pruebas al repositorio.
- [ ] **Tarea B.4: Refactorización y Análisis Estático "Después" - Evidencia B.d (Día 6)**
  - Arreglar "code smells" reportados en Python.
  - Generar y capturar el nuevo reporte de SonarCloud demostrando la mejora. Entregar a Persona A.

### 💻 Persona C: QA Automation Frontend
*Objetivo:* Pruebas de Interfaz (Next.js), automatización visual y apoyo en CI/CD. Responsable de evidencias para la **Sección B**.

- [ ] **Tarea C.1: Configuración Cypress/Jest (Día 1-2)**
  - Crear la suite de automatización dentro de `web/tests/`.
  - Configurar Cypress para E2E o Jest para componentes.
- [ ] **Tarea C.2: Automatización de Flujos Clave (Día 3-5)**
  - Escribir scripts para simular flujos: (1) Iniciar grabación de audio y (2) Ver y formatear transcripción.
  - Asegurar que estos scripts se suban a la rama principal en GitHub.
- [ ] **Tarea C.3: Resolución de Bugs Frontend en Jira (Día 5-6)**
  - Tomar los bugs frontend reportados por la Persona D en Jira y aplicar fixes en el código fuente para mejorar la calidad del entregable final.
- [ ] **Tarea C.4: Evidencia de Pruebas Dinámicas (Día 6)**
  - Tomar capturas de Cypress ejecutándose (los logs en verde) para adjuntarlos al documento final.

### 🕵️‍♂️ Persona D: QA Manual & Diseño de Pruebas
*Objetivo:* Creación de Casos, Matriz de Rastreabilidad, Ejecución Manual y Video. Responsable de las **Secciones B.a, B.b, B.c y del Video**.

- [ ] **Tarea D.1: Matriz y Casos de Prueba - Evidencias B.a y B.b (Día 1-3)**
  - Diseñar la Matriz de Rastreabilidad cruzando Requisitos de Negocio vs ID del Caso de Prueba.
  - Diseñar una muestra representativa de Casos Manuales con estructura estricta: *ID, Título, Precondiciones, Pasos 1..N, Resultado Esperado.*
- [ ] **Tarea D.2: Ejecución Manual y Jira - Evidencia B.c (Día 4-5)**
  - Ejecutar casos manuales en la app (especialmente la versión Desktop Electron).
  - Levantar tickets en Jira con capturas de pantalla, indicando **Severidad** (Crítico, Mayor, Menor) y **Prioridad**. 
  - Tomar capturas de los tickets de Jira como "Reporte de Defectos" para la Sección B.c del PDF.
- [ ] **Tarea D.3: Re-testing (Día 6)**
  - Mover tickets en Jira a "Done" si B y C lograron solucionar los bugs críticos.
- [ ] **Tarea D.4: Producción del Video (Día 7)**
  - Grabar el video (5-7 mins máximo). El guion DEBE incluir:
    1) Mostrar el flujo del pipeline en GitHub Actions con SonarCloud corriendo.
    2) Ejecutar `pytest` o `Cypress` en pantalla demostrando las pruebas automatizadas.
    3) Realizar un flujo de prueba manual complejo de la interfaz.
    4) Mostrar brevemente el tablero de Jira con los defectos encontrados.

---

## 📋 Resumen de Responsabilidades para el PDF Final

Para que la Persona A pueda compilar el documento sin contratiempos, el Día 6 todos deben entregarle:

* **Persona D:** Tabla de Matriz de Rastreabilidad (B.a), Casos de Prueba formateados (B.b) y capturas de bugs en Jira (B.c).
* **Persona B:** Capturas y links de SonarCloud "Antes" y "Después" (B.d) y métricas de test backend.
* **Persona C:** Capturas de Cypress/Jest corriendo y métricas de test frontend.

## 💡 Recomendaciones Extra para Garantizar el 100% de Calificación:

1. **Sobre el Video:** En los proyectos universitarios, el video es vital. Asegúrense de que el audio sea claro y que la persona que narra explique *por qué* están haciendo las pruebas, no solo mostrando comandos. (Ej: *"Aquí ejecutamos Cypress para validar el flujo del usuario..."*).
2. **Uso de Jira:** Cuando levanten tickets en Jira, usen etiquetas claras (Labels) como `Backend`, `Frontend`, `Code-Smell`, `Bug`. Esto le hará el trabajo sumamente fácil a la Persona A para calcular la *Densidad de Defectos por módulo* (Punto C.a.ii).
3. **Justificación del Alcance:** Es normal no probar el 100% del sistema. En el punto A.a, es crucial justificar *técnicamente* por qué algo no se probó (ej. "No se probarán los algoritmos internos de los modelos NIM porque son cajas negras provistas por un tercero, nos enfocaremos en probar la integración de nuestra API con ellos").
