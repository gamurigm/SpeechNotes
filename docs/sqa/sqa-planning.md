# Plan Asincrónico Riguroso SQA - SpeechNotes (Sprint Acelerado: 18 al 21 de Julio)

Este plan ha sido **comprimido a 4 días** para cumplir con la entrega del 21 de julio. Cubre **estrictamente cada punto de la rúbrica y estructura documental** solicitada en la guía. Se detalla el uso de Jira para gestión de incidencias y la responsabilidad exacta sobre cada sección del PDF final.

**Plataforma CI/CD:** GitHub Actions + SonarCloud (Online)
**Gestor de Bugs y Tareas:** Jira Software
**Equipo:** 4 Personas (A, B, C, D)

---

## 👥 Asignación de Roles y Checklist Riguroso

### 📝 Persona A: QA Lead & Test Manager (Responsable del Documento Final)
*Objetivo:* Asegurar la calidad metodológica, integrar las evidencias y redactar las conclusiones. Responsable de la **Sección A, C y D** del PDF.

- [ ] **Tarea A.1: Configuración de Jira y Proyecto (18 de julio)**
  - Crear un proyecto en Jira y configurar el flujo (`To Do` -> `In Progress` -> `In Testing` -> `Done`). Invitar al equipo.
- [ ] **Tarea A.2: Redacción del SQAP - Sección A (18 de julio)**
  - **A.a. Alcance:** Qué se probará y qué no, con justificación.
  - **A.b. Estrategia:** Definir tipos de prueba y *Entry/Exit Criteria*.
  - **A.c. Herramientas:** Justificar Jira, SonarCloud, Pytest y Cypress.
  - **A.d. Gestión de Riesgos:** Documentar riesgos de producto y pruebas.
- [ ] **Tarea A.3: Informe de Cierre - Sección C (20 de julio)**
  - Recolectar datos de Jira. Calcular % de Casos Pasados vs Fallados y Densidad de Defectos.
- [ ] **Tarea A.4: Conclusiones y Ensamblaje PDF Final (21 de julio)**
  - Redactar valoración crítica. Unir el trabajo de todos en un único PDF (`GRUPO#_PROYECTOFINAL_PARCIAL3.pdf`).

### ⚙️ Persona B: QA Automation Backend & CI/CD
*Objetivo:* Pruebas del Backend, métricas de SonarQube y despliegue del pipeline. Responsable de evidencias para la **Sección B**.

- [ ] **Tarea B.1: Pipeline SonarCloud y Análisis "Antes" (18 de julio)**
  - Configurar `.github/workflows/sonar.yml` con SonarCloud.
  - Tomar captura del primer reporte (Deuda técnica inicial).
- [ ] **Tarea B.2: Pruebas Backend - Carpeta `Tests` (19 de julio)**
  - Crear script `pytest` y automatizar endpoints principales.
- [ ] **Tarea B.3: Refactorización y Análisis "Después" (20 de julio)**
  - Corregir "code smells" detectados. Generar y capturar el nuevo reporte de SonarCloud.

### 💻 Persona C: QA Automation Frontend
*Objetivo:* Pruebas de Interfaz (Next.js), automatización visual y apoyo en CI/CD. Responsable de evidencias para la **Sección B**.

- [ ] **Tarea C.1: Configuración de Suite y Pruebas Iniciales (18 de julio)**
  - Configurar Cypress/Jest en `web/tests/`.
- [ ] **Tarea C.2: Automatización de Flujos Clave (19 de julio)**
  - Automatizar simulación de grabación de audio y vista de transcripciones.
- [ ] **Tarea C.3: Resolución de Bugs Frontend (20 de julio)**
  - Corregir bugs reportados por Persona D en Jira.
- [ ] **Tarea C.4: Evidencia de Pruebas Dinámicas (20 de julio)**
  - Enviar capturas de logs verdes de Cypress a la Persona A.

### 🕵️‍♂️ Persona D: QA Manual & Diseño de Pruebas
*Objetivo:* Creación de Casos, Matriz de Rastreabilidad, Ejecución Manual y Video. Responsable de las **Secciones B.a, B.b, B.c y del Video**.

- [ ] **Tarea D.1: Matriz y Diseño de Casos (18 de julio)**
  - Diseñar la Matriz de Rastreabilidad y los Casos de Prueba Manuales (ID, Precondiciones, Pasos, Resultado Esperado).
- [ ] **Tarea D.2: Ejecución Manual y Reporte de Bugs (19 de julio)**
  - Probar la app, levantar tickets en Jira con capturas, severidad y prioridad.
- [ ] **Tarea D.3: Re-testing y Extracción de Evidencias (20 de julio)**
  - Verificar correcciones de B y C. Pasar tickets a "Done". Exportar capturas de Jira.
- [ ] **Tarea D.4: Producción del Video (21 de julio)**
  - Grabar el video (5-7 mins): 1) SonarCloud en GitHub Actions, 2) Pruebas automatizadas corriendo, 3) Flujo manual, 4) Tablero Jira.

---

## 📋 Resumen de Responsabilidades para el PDF Final

Para que la Persona A compile sin estrés, el **20 de julio (Día 3 en la noche)** todos deben entregarle:

* **Persona D:** Tabla de Matriz (B.a), Casos Manuales (B.b) y capturas Jira (B.c).
* **Persona B:** Capturas SonarCloud "Antes/Después" (B.d) y métricas de pytest.
* **Persona C:** Capturas Cypress y métricas de frontend.

## 💡 Recomendaciones para este Sprint Acelerado:

1. **Dependencias:** Ya que hay poco tiempo, la Persona A puede avanzar el documento SQAP (Sección A) hoy mismo mientras B y C levantan los entornos.
2. **Priorización:** Enfóquense solo en los **Flujos Críticos** (Grabación y transcripción). No intenten probar el 100% del sistema; es mejor tener pocos casos de prueba perfectamente documentados que muchos casos sin evidencia.
