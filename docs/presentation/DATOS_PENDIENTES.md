# Datos Pendientes de Actualizar en la Presentación

Este documento lista todos los datos **estimados o inferidos** en `index.html` que deben ser reemplazados con los valores reales una vez ejecutadas las pruebas.

---

## Slide 8 & 9 — Análisis Estático (SonarCloud)

> Estado actualizado desde la API pública de SonarCloud.

| Campo | Valor Actual (SonarCloud API) | Estado |
|-------|------------------------------|--------|
| Vulnerabilidades | `0` | ✅ Real (API) |
| Code Smells | `0` | ✅ Real (API) |
| Bugs Estáticos | `0` | ✅ Real (API) |
| Deuda Técnica | `0 min` | ✅ Real (API) |
| Cobertura | `90.4%` | ✅ Real (API) |
| Duplicación | `0.5%` | ✅ Real (API) |
| Confiabilidad | `Rating A (1.0)` | ✅ Real (API) |
| Seguridad | `Rating A (1.0)` | ✅ Real (API) |
| Mantenibilidad | `Rating A (1.0)` | ✅ Real (API) |
| Líneas de código (NCLOC) | `13,847` | ✅ Real (API) |

## Slide 9 — Análisis Estático (Después)

> Líneas aproximadas: buscar `Slide 9`, la sección `compare` y las barras de progreso.

### Caja "Antes" (resumen)
| Campo | Valor actual (estimado) | Qué poner |
|-------|------------------------|-----------|
| Code Smells | `12` | Mismo valor que Slide 8 (debe coincidir) |
| Deuda Técnica | `~2h` | Mismo valor que Slide 8 |

### Caja "Después"
| Campo | Valor actual (estimado) | Qué poner |
|-------|------------------------|-----------|
| Code Smells restantes | `4` | Número real del segundo reporte SonarCloud |
| Deuda Técnica | `~45min` | Valor real del segundo reporte |
| Handlers modularizados | texto genérico | Describir la refactorización real si aplica |

### Barras de progreso
| Barra | Texto actual (estimado) | Qué poner |
|-------|------------------------|-----------|
| Code Smells | `12 → 4 (−67%)` | `X → Y (−Z%)` con valores reales |
| Deuda Técnica | `2h → 45min (−63%)` | Valores reales |
| Duplicación | `Reducida 80%` | Porcentaje real o quitar si no aplica |

### Texto del highlight box
> "La integración de SonarCloud en GitHub Actions asegura..."

Actualizar si hay observaciones adicionales del análisis.

---

## Slide 12 — Ejecución de Pruebas

> Buscar `Slide 12` o el bloque de stats con `58`.

| Campo | Valor actual | Fuente | Verificar |
|-------|-------------|--------|-----------|
| Tasa de Aprobación | `92.86%` | conclusiones.tex | ✅ Probablemente real — verificar |
| Tests Backend (Pytest) | `58` | BACKEND_TESTS.md | ✅ Verificar con última corrida |
| Tests Frontend (Jest + Cypress) | `3` | conteo de archivos | ⚠️ Actualizar si agregaron más |
| Casos Manuales | `10` | persona-d | ✅ Real |

### Bloque de código al final de la slide
```
============= 58 passed, 0 failed, 0 skipped in 8.40s =============
```
→ Reemplazar con la salida real de `pytest backend/tests/ -v`

---

## Slide 13 — Reporte de Defectos

> Buscar `Slide 13` o la tabla de bugs.

### Stats superiores
| Campo | Valor actual | Verificar |
|-------|-------------|-----------|
| Bugs Reportados | `8` | Contar en Jira |
| Corregidos | `3` | Contar en Jira (estado Done) |
| Pendientes | `5` | Contar en Jira (estados abiertos) |

### Tabla de bugs

Los **bugs 01–04** fueron sacados del documento de Persona D y son reales.
Los **bugs 05–08** fueron **inferidos** de las conclusiones del SQAP que mencionan "3 bugs Minor de UX". Los títulos exactos son estimados:

| ID | Título actual (estimado) | Acción requerida |
|----|--------------------------|------------------|
| BUG-05 | Tooltip duplicado en panel de grabación | ⚠️ Reemplazar con bug real de Jira |
| BUG-06 | Icono play/pausa inconsistente | ⚠️ Reemplazar con bug real de Jira |
| BUG-07 | Placeholder incorrecto en registro | ⚠️ Reemplazar con bug real de Jira |
| BUG-08 | React ref no encontrada (BNR Component) | ⚠️ Verificar título y estado en Jira |

Para cada bug verificar: **severidad**, **prioridad**, **módulo** y **estado** (Pendiente/Corregido).

---

## Slide 14 — Métricas de Calidad

> Buscar `Slide 14`.

### Resumen por severidad
| Severidad | Valor actual | Verificar contra Jira |
|-----------|-------------|----------------------|
| Critical | `1` | ¿Cuántos bugs critical reales? |
| Major | `4` | ¿Cuántos bugs major reales? |
| Minor | `3` | ¿Cuántos bugs minor reales? |
| Blocker | `0` | ¿Cuántos bugs blocker reales? |

### Barras de densidad de defectos por módulo
| Módulo | Bugs actuales (estimado) | Verificar |
|--------|-------------------------|-----------|
| Frontend / UX | 3 bugs, width: 60% | Contar en Jira por label |
| Frontend / API | 2 bugs, width: 40% | Contar en Jira por label |
| Audio / Realtime | 1 bug, width: 20% | Contar en Jira por label |
| Auth | 1 bug, width: 20% | Contar en Jira por label |
| Backend | 1 bug, width: 20% | Contar en Jira por label |

Las barras usan `width: XX%` en el HTML. Ajustar proporcionalmente al módulo con más bugs.

---

## Resumen rápido

```
Datos REALES (no tocar salvo cambios):
  ✅ Stack tecnológico (slide 3)
  ✅ Alcance — 10 módulos incluidos/excluidos (slide 4)
  ✅ Estrategia de pruebas (slide 5)
  ✅ Herramientas con justificación (slide 6)
  ✅ Tabla de 6 riesgos (slide 7)
  ✅ Matriz de rastreabilidad (slide 10)
  ✅ Casos de prueba CP-01 a CP-10 (slide 11)
  ✅ Conclusiones y lecciones (slide 15)
  ✅ Trabajo futuro (slide 16)

Datos ESTIMADOS (actualizar con valores reales):
  ⚠️ SonarCloud Antes: smells, vulns, deuda (slide 8)
  ⚠️ SonarCloud Después: smells, deuda, % reducción (slide 9)
  ⚠️ Salida de pytest: passed/failed/time (slide 12)
  ⚠️ Bugs 05–08: títulos, severidad, estado (slide 13)
  ⚠️ Severidad totales y densidad por módulo (slide 14)
```
