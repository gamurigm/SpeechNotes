### 1

# Proyecto Final – Plan Aseguramiento de la Calidad SQA

## Tema Actividad: Guía del Proyecto Final: Implementación de un Plan de Aseguramiento de la Calidad

## (SQAP).

Estimad@s estudiantes:

Reciban la bienvenida a la siguiente actividad final del presente semestre, donde podrán aplicar las competencias desarrolladas
hasta el momento.

Para tales efectos, se solicita seguir las siguientes instrucciones:

Docente Ing. Diego Leonado Gamboa Mgtr.

**Descripción del Escenario**

En el mundo profesional, es común que un ingeniero de QA no comience un proyecto desde cero, sino que
deba auditar y asegurar la calidad de un sistema existente (Legacy).
Para este proyecto final, simularán ser una Consultora de Calidad Externa. Su misión es tomar un software
desarrollado previamente por ustedes mismos (el "SUT" - System Under Test), auditar su estado actual,
definir una estrategia de calidad y ejecutarla bajo un marco metodológico riguroso.

**Objetivo General:** Demostrar la capacidad de planificar, documentar y ejecutar un proceso de SQA,
evidenciando la mejora en la confiabilidad del producto final.

**Objetivos Específicos**
1. **Planificar la estrategia de calidad:** Elaborar un Plan Maestro de Pruebas que defina el alcance, los
    recursos, el stack tecnológico y los riesgos asociados al aseguramiento de un software ya
    desarrollado, justificando la selección de herramientas y tipos de pruebas.
2. **Evaluar la deuda técnica:** Realizar pruebas estáticas mediante herramientas de análisis de código
    (p. ej. SonarQube, Linters) para identificar, clasificar y documentar vulnerabilidades, code smells y
    violaciones a las buenas prácticas de programación.
3. **Ejecutar pruebas dinámicas y automatizadas:** Diseñar e implementar casos de prueba (unitarios,
    de integración o funcionales) manuales y automatizados, gestionando el ciclo de vida de los defectos
    encontrados (detección, reporte y verificación) en un repositorio de incidencias.
4. **Documentar y evidenciar resultados:** Generar artefactos de calidad trazables (matrices de
    pruebas, reportes de ejecución y métricas de defectos) que fundamenten la decisión final sobre la
    idoneidad del software para su paso a producción.

**El SUT y Stack Tecnológico**
- **System Under Test (SUT):** Deberán seleccionar un proyecto de software desarrollado en semestres
    anteriores (pueden ser proyectos de Programación Web, Móvil o Arquitectura de Software).
       o Condición: El software debe ser funcional (compilable/ejecutable) para poder realizar las
          pruebas.
- **Stack Tecnológico (Libertad de Herramientas):** Tienen total libertad para elegir las herramientas
    que mejor se adapten a la tecnología de su SUT.
       o Ejemplos: Si su SUT está en Java, pueden usar JUnit + Selenium; si es JS, Jest + Cypress;
          para gestión pueden usar Jira, Trello, TestLink o mantenedores de Excel.


### 2

**Desarrollo**

**1. Cronograma del trabajo (Spring de 3 Semanas)**

Dado que el tiempo es limitado, trabajaremos bajo un esquema de Sprint de Calidad. Se espera que
dediquen tiempo fuera del aula para cumplir los hitos.

**Semana 1: Planificación y Análisis Estático (El "Plan")**
- Recuperación y despliegue del SUT en un entorno de pruebas.
- Diligenciamiento de la Plantilla SQAP (Documento Maestro): Definición de alcance,
    recursos, riesgos y estrategia.
- Ejecución de Pruebas Estáticas: Uso de herramientas de análisis de código (ej. SonarQube,
    ESLint) para detectar deuda técnica inicial.
**Semana 2: Diseño y Ejecución Dinámica (La "Acción")**
- Diseño de Casos de Prueba (Test Case Design) basados en los requerimientos originales
del sistema.
- Ejecución de Pruebas Unitarias (Cobertura de código crítica) y Funcionales (Manuales y/o
Automatizadas).
- Registro de defectos (Bug Tracking).
**Semana 3: Cierre, Documentación y Evidencias (El "Entregable")**
- Generación de reportes de ejecución.
- Grabación de los videos de evidencia.
- Consolidación del PDF final con el análisis de resultados.
**2. Estructura de la Documentación (Enfoque Principal)**

El mayor peso de la calificación recae en la calidad de su documentación y la metodología aplicada.
Deberán entregar un único documento PDF basado en la plantilla proporcionada, que debe incluir
obligatoriamente:

**A. Plan de Aseguramiento de la Calidad (SQAP)**
a. Alcance: ¿Qué módulos se van a probar y cuáles NO? (Justificar).
b. Estrategia de Pruebas:
   i. Tipos de pruebas seleccionados (Unitarias, Integración, Sistema, etc.).
   ii. Criterios de Aceptación y Rechazo (Entry/Exit Criteria).
c. Herramientas: Justificación técnica del stack elegido.
d. Gestión de Riesgos: Riesgos del producto y del proyecto de pruebas.
**B. Diseño y Ejecución (Evidencias)**
a. Matriz de Rastreabilidad: Requisito vs. Caso de Prueba.
b. Diseño de Casos de Prueba: Muestra representativa de los casos diseñados (Título, Precondiciones, Pasos, Resultado Esperado).
c. Reporte de Defectos: Evidencia de los bugs encontrados (Screenshots, severidad, prioridad).
d. Análisis Estático: Reporte del "Antes" y "Después" (si hubo refactorización) del análisis de código estático.
**C. Informe de Cierre (Test Summary Report)**
a. Métricas de Calidad:
   i. % de Casos Pasados vs. Fallados.
   ii. Densidad de Defectos (Defectos por módulo).
**D. Conclusiones:**
a. Valoración crítica del estado de calidad del software entregado.

### 3

**Entregables Clave**

Para la evaluación final, el equipo deberá subir a la plataforma los siguientes 3 elementos:

**1) Documento SQAP (PDF):**
a. Contiene todo lo descrito en la sección 4. Debe ser formal, con redacción técnica y
referencias bibliográficas si aplica.
**2) Código Fuente (Repositorio):**
a. Enlace a GitHub/GitLab.
b. Debe contener el código del SUT y, en una carpeta separada AreadePruebas o Tests, los
scripts de automatización o pruebas unitarias generados.
**3) Video de Ejecución (Demo):**
a. Duración máxima: 5-7 minutos.
b. El equipo debe narrar y mostrar:
   i. La ejecución de la suite de pruebas automatizadas (si aplica).
   ii. La demostración de un flujo de prueba manual complejo.
   iii. La visualización de los reportes generados por las herramientas.

**Rúbrica**

| Criterio | Peso | Descripción |
| :--- | :---: | :--- |
| Metodología y Planificación | 40% | Coherencia del SQAP, análisis de riesgos y estrategia definida en el PDF. |
| Ejecución y Evidencias | 30% | Calidad de los casos de prueba, reporte correcto de bugs y trazabilidad. |
| Uso de Herramientas | 20% | Implementación correcta del stack tecnológico (Análisis estático + Pruebas dinámicas). |
| Exposición y Video | 10% | Claridad en la comunicación y demostración de resultados. |
- Bibliografía sugerida: Si aplica
- Guarde el/los archivo(s) de la tarea elaborada en formato **.zip o .rar** con su el nombre del grupo,
    seguidos de la palabra Actividad2_Parcial2. **Ejemplo: GRUPO#_PROYECTOFINAL_PARCIAL 3 .pdf**
- El tamaño del documento será de máximo. **10 Mb**
- Cargue el documento a través de este espacio, dentro del plazo establecido para la entrega.

Esta actividad tendrá un puntaje de: **20 puntos**

Atentamente,
Ing. Diego Gamboa Mgtr.

