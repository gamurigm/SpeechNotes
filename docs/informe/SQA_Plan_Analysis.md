# Análisis y Mapeo: Plan de Aseguramiento de Calidad (SQA) - SpeechNotes

Al revisar a profundidad la documentación del proyecto (específicamente la carpeta `docs/sqa/`), he podido extraer la estructura real, roles, y responsabilidades planificadas para el Sprint de SQA (del 18 al 21 de Julio). A continuación, el mapeo detallado que responde exactamente a las secciones requeridas por el SQA Plan Template:

---

## 1. PROPÓSITO Y ALCANCE (PURPOSE)
- **Alcance definido:** El aseguramiento de calidad cubrirá los flujos críticos (grabación y transcripción) para la versión web. No se intentará probar el 100% del sistema, sino los casos de uso fundamentales asegurando alta calidad y evidencia documentada.
- **Estrategia:** Pruebas dinámicas (Cypress para Frontend, Pytest para Backend), pruebas estáticas (SonarCloud), y pruebas manuales basadas en flujos clave.

## 2. GESTIÓN Y ORGANIZACIÓN (MANAGEMENT)
- **Estructura Organizacional (Scrum + Roles SQA):**
  - **Persona A (QA Lead & Test Manager):** Responsable de configuración en Jira, elaboración de la Sección A del SQAP, recolección de métricas, conclusiones y ensamblaje final del documento.
  - **Persona B (QA Automation Backend & CI/CD):** Responsable del backend (`backend/tests/`), automatización con Pytest, despliegue en GitHub Actions y validaciones de SonarCloud.
  - **Persona C (QA Automation Frontend):** Responsable de pruebas UI (`web/tests/`) usando Cypress/Jest y corrección de bugs frontend.
  - **Persona D (QA Manual & Diseño de Pruebas):** Responsable del diseño de casos de prueba (CP-01 al CP-10), ejecución manual, re-testing y producción del video final.

## 3. TAREAS DE SQA (SQA TASKS)
- **Tareas planificadas:**
  - Elaboración de Matriz de Rastreabilidad (Persona D).
  - Integración Continua y análisis estático (Persona B con SonarCloud).
  - Ejecución Manual y pruebas exploratorias (Persona D en Jira).
  - Corrección de bugs y resolución de deuda técnica detectada (Personas B y C).

## 4. DOCUMENTACIÓN (DOCUMENTATION)
- El proyecto ya cuenta con guías estructuradas:
  - `guia-jira-setup.md`
  - `guia-rol-a.md`
  - `sqa-planning.md`
  - Historias de usuario (`jira-user-stories.md`).
- **Pendiente:** Integrar los reportes generados de SonarCloud y las evidencias fotográficas de Cypress/Pytest al documento final (responsabilidad de la Persona A de compilarlo el 21 de Julio).

## 5. ESTÁNDARES, PRÁCTICAS Y MÉTRICAS (STANDARDS & METRICS)
- **Herramientas de Análisis Estático:** Se utiliza **SonarCloud** (configurado en `.github/workflows/sonar.yml`).
- **Métricas:** Deuda técnica inicial ("Antes") vs ("Después"), porcentaje de Casos Pasados vs Fallados, y Densidad de Defectos calculadas a partir del reporte de Jira.

## 6. PRUEBAS (TESTING)
- **Pruebas Estáticas:** SonarCloud en GitHub Actions.
- **Pruebas Unitarias/API:** `pytest` en la carpeta `backend/tests/` (Persona B).
- **Pruebas E2E / Frontend:** Cypress en `web/tests/` (Persona C).
- **Pruebas Manuales:** 10 casos críticos de prueba (ej. CP-03 Grabación, CP-09 Formateo IA) ejecutados por Persona D.

## 7. REPORTE DE PROBLEMAS Y RESOLUCIÓN (PROBLEM REPORTING)
- **Gestión:** Uso exclusivo de **Jira Software**.
- **Flujo de Tickets:** `To Do` -> `In Progress` -> `In Testing` -> `Done`.
- **Reglas de Bug Report:** Cada bug manual (reportado por Persona D) debe incluir: módulo, severidad, prioridad, pasos para reproducir, resultado esperado, resultado actual y **capturas de pantalla/logs** de evidencia.
- **Re-testing:** Al solucionarse un bug (por Persona B o C), el ticket se mueve a `In Testing` donde Persona D repite el caso y lo pasa a `Done` si adjunta evidencia de que funciona, de lo contrario lo devuelve a `In Progress`.

## 8. HERRAMIENTAS Y METODOLOGÍAS (TOOLS & METHODOLOGIES)
- GitHub Actions (CI/CD)
- Jira Software (Gestión de proyectos, Test Management)
- Cypress / Jest (Testing Web)
- Pytest (Testing Backend)
- SonarCloud (Análisis estático de código)

## 9. CONTROL DE CÓDIGO (CODE CONTROL)
- **Estrategia:** Rama dedicada `planning-SQA` para integraciones, verificada mediante pipelines de CI/CD que ejecutan SonarCloud antes de permitir fusiones. (Sugerido en la documentación de la demo).

## 10 a 14. EXCEPCIONES Y OTROS PROCESOS
- **Gestión de Riesgos:** Documentación de riesgos de producto y pruebas (responsabilidad de Persona A).
- *Control de Medios y Proveedores:* No aplica estrictamente en esta fase de aceleración (Sprint de 4 días), pero se enfoca puramente en el aseguramiento técnico del desarrollo.
