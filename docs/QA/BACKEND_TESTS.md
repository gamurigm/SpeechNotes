# Backend Test Suite (Pytest)

Suite de automatizacion con **Pytest** para los endpoints principales del backend
de SpeechNotes. Valida codigos de respuesta HTTP, estructura y datos de las
respuestas JSON, y previene regresiones en los servicios web expuestos.

---

## Alcance

| Router | Endpoints cubiertos | Tests |
|--------|--------------------|-------|
| Root + Health | `GET /`, `GET /health` | 7 |
| Transcriptions | `GET /api/transcriptions`, `/latest`, `/search`, `/{id}`, `PUT /{id}`, `DELETE /{id}` | 16 |
| Documents | `GET /api/documents`, `GET /api/documents/{id}/content` | 8 |
| Settings | `GET/PUT/DELETE /api/settings/...` | 11 |
| VAD Config | `GET/POST /api/config/vad` | 6 |
| Auth (opt-in) | validacion de 200/401/403 | 4 (solo con `TEST_AUTH=1`) |
| **Total** | | **~52** |

> Los endpoints de `/api/chat`, `/api/translate`, `/api/audio/*` y el formatter
> agent **no estan incluidos** porque dependen de servicios externos (NVIDIA NIM,
> Riva, agentes LLM) que no siempre estan disponibles en CI. Si necesitas
> extender la suite a esos routers, los fixtures de `conftest.py` proveen el
> patron (seed + autouse cleanup) para reutilizar.

---

## Limitacion importante: backend de testing vs backend real

El backend de testing que arranca la suite (`backend/main_test.py`) **no es
identico** al backend de produccion (`backend/main.py`). Hay dos diferencias
clave que debes tener en cuenta al interpretar resultados:

### 1. Storage: SQLite vs MongoDB

El backend real usa **dos bases de datos** dependiendo del archivo:

| Import en el codigo | Resuelve a | Routers que lo usan |
|--------------------|------------|---------------------|
| `from src.database import MongoManager` | **SQLite** (es un alias) | `chat.py`, `documents.py`, `transcribe.py`, `transcription_repository.py`, `socket_handler_new.py`, `src/agent/*` |
| `from src.database.mongo_manager import MongoManager` | **Mongo real** | `admin.py`, `formatter_agent.py` |

Esto se origina en `src/database/__init__.py:12`:
```python
MongoManager = SQLiteManager  # alias de compatibilidad
```

**Implicacion para los tests:** los 4 routers que la suite ejercita
(`transcriptions`, `documents`, `settings`, `vad_config`) usan el alias, por
lo que las fixtures pueden sembrar directamente en SQLite
(`data/speechnotes.db`) y el backend los ve. **No necesitas MongoDB corriendo
para que la suite pase** (58/58 tests verifican esto).

**Lo que NO se valida:** los routers `admin` y `formatter_agent` que SI usan
Mongo real **no estan en `main_test.py`** (se excluyeron a proposito para
evitar la dependencia de Mongo). Si tocas `admin.py` o `formatter_agent.py`,
debes probarlos manualmente contra el `main.py` real con Mongo arriba.

### 2. Routers cargados

`main_test.py` carga solo **6 routers** (los que la suite ejercita):

```python
# backend/main_test.py
app.include_router(transcriptions.router, ...)
app.include_router(documents.router, ...)
app.include_router(settings.router, ...)
app.include_router(vad_config.router, ...)
app.include_router(admin.router, ...)       # NOTA: usa Mongo real si se incluye
app.include_router(debug.router, ...)
```

`main.py` real carga **12 routers** incluyendo chat, formatter, transcribe,
audio_processing, audio_format, translation, websocket. Esos dependen de
NVIDIA NIM, Riva, LangChain y otros servicios externos, por eso se omitieron
del `main_test.py`.

**Como extender la suite a un nuevo router:**

| Router nuevo | Que hacer |
|--------------|-----------|
| Solo lee/escribe datos simples (SQLite) | Agregar a `main_test.py` + agregar tests |
| Usa Mongo real (ej. `admin`) | Mantener Mongo corriendo en CI + ajustar fixtures |
| Depende de servicio externo (NIM, Riva) | Marcar esos tests como opt-in o mockear la respuesta |

### Verificacion

La limitacion fue validada con esta corrida real:

```
58 passed, 0 failed, 0 skipped in 8.40s
```

Si tocas codigo que rompe alguno de los routers excluidos, **la suite NO lo
detectara** — esos cambios requieren prueba manual contra `main.py` real.

---

## Prerrequisitos

1. **Backend levantado y accesible** en `http://localhost:9443` (o el override
   `BACKEND_URL`).
   ```powershell
   .\run_all.ps1
   # o equivalentemente:
   docker compose up mongodb backend
   ```
2. **MongoDB accesible** en `mongodb://localhost:27017` (o `MONGO_URI`).
3. **Python 3.10+** con las dependencias de testing instaladas.
   ```powershell
   pip install -r requirements-test.txt
   ```
   `pymongo`, `pytest` y `requests` ya estan en `requirements-test.txt` y en
   `backend/requirements.txt`.

Si el backend o Mongo no estan disponibles, los tests **hacen skip limpio**
mostrando un mensaje claro en la consola — no fallan con error de conexion
confuso.

### Entornos soportados

| Entorno | Soporte | Notas |
|---------|---------|-------|
| **Windows + WSL** (recomendado) | ✅ Nativo | Docker corre en WSL, Python y backend en Windows. Los scripts detectan esto automaticamente. |
| Windows + Docker Desktop nativo | ✅ | Usa `-UseWindowsDocker` en `run_backend_only.ps1` |
| WSL puro (todo dentro de WSL) | ✅ | Usa `-UseWsl` en `run_backend_tests.ps1` |
| Linux / macOS | ⚠️ Parcial | Los `.ps1` no funcionan directamente; considera crear `.sh` equivalentes |

---

## Quick start (flujo de 2 terminales)

Si quieres correr la suite rapidamente sin levantar todo el stack de
SpeechNotes (frontend, desktop app, etc.), usa **dos terminales**:

```powershell
# Terminal 1: arrancar SOLO Mongo + Backend (sin frontend, sin Tauri)
.\scripts\run_backend_only.ps1

# Terminal 2: una vez que el script anterior reporta "Servicios listos"
.\scripts\run_backend_tests.ps1
```

`run_backend_only.ps1`:
1. Verifica que WSL este disponible (o usa `-UseWindowsDocker`)
2. Libera el puerto 9443
3. Levanta MongoDB via `wsl docker compose up -d mongodb`
4. Espera a que Mongo responda a ping
5. Lanza el backend en una nueva ventana PowerShell
6. Espera a que `/health` responda 200
7. Imprime las instrucciones para correr tests

**Exit codes del script:**

| Codigo | Significado |
|--------|-------------|
| 0 | Mongo + Backend listos |
| 1 | Docker no disponible |
| 2 | Mongo no respondio a tiempo |
| 3 | Backend no respondio a tiempo |
| 4 | Python no encontrado |
| 5 | WSL no disponible |

**Flags utiles:**

```powershell
.\scripts\run_backend_only.ps1 -SkipDocker        # si ya tienes Mongo en otro host
.\scripts\run_backend_only.ps1 -BackendOnly       # solo lanza el backend, asume Mongo externo
.\scripts\run_backend_only.ps1 -UseWindowsDocker  # si tienes Docker Desktop nativo
```

Para detener el backend al terminar, cierra su ventana o ejecuta:

```powershell
Get-Process python | Where-Object { $_.CommandLine -like '*backend/main.py*' } | Stop-Process
```

---

## Como correr la suite

### Opcion A: script PowerShell (recomendado para Windows / WSL)

```powershell
# Suite completa
.\scripts\run_backend_tests.ps1

# Solo smoke tests (rapido, ~5s)
.\scripts\run_backend_tests.ps1 -Smoke

# Tests de autenticacion (opt-in)
.\scripts\run_backend_tests.ps1 -Auth

# Solo un archivo
.\scripts\run_backend_tests.ps1 -Test "test_health.py"

# Saltar pre-flight checks
.\scripts\run_backend_tests.ps1 -SkipChecks

# Si tu Python vive dentro de WSL (no en Windows)
.\scripts\run_backend_tests.ps1 -UseWsl
```

El script:
1. Verifica `/health` (5s timeout)
2. Verifica que Mongo responde a `ping`
3. Instala `requirements-test.txt` si falta
4. Ejecuta pytest con el verbosity adecuado
5. Sale con exit code 0 (verde) o 1 (rojo)

### Opcion B: pytest directo

```bash
# Toda la suite
pytest backend/tests/ -v

# Por marker
pytest backend/tests/ -m smoke -v
pytest backend/tests/ -m regression -v

# Por archivo
pytest backend/tests/test_transcriptions.py -v
pytest backend/tests/test_settings.py -v

# Por patron
pytest backend/tests/ -k "test_delete" -v
pytest backend/tests/ -k "404" -v
```

---

## Variables de entorno

| Variable | Default | Proposito |
|----------|---------|-----------|
| `BACKEND_URL` | `http://localhost:9443` | URL base del backend |
| `API_KEY` | `dev-secret-api-key` | API key enviada en `x-api-key` (bypassea auth en modo dev) |
| `MONGO_URI` | `mongodb://localhost:27017` | URI de MongoDB (usado por fixtures de seed) |
| `MONGO_DB_NAME` | `agent_knowledge_base` | Nombre de la base usada en seed/cleanup |
| `TEST_AUTH` | (unset) | Si es `1`, habilita los tests de `test_auth.py` |
| `PYTEST_DEBUG_HTTP` | (unset) | Si es `1`, loguea cada request/response en consola |

---

## Interpretacion del reporte

Pytest muestra al final un resumen asi:

```
============= 48 passed, 2 skipped in 12.34s =============
```

- **passed** = verde, el endpoint respondio como se esperaba.
- **failed** = rojo, hay regresion o el backend esta caido. Revisa el traceback.
- **skipped** = amarillo, el test se omitio porque faltaba una dependencia
  (ej. Mongo no accesible). Para "des-skippear", levanta el servicio.
- **xfail / xpassed** = casos marcados con `@pytest.mark.xfail` (no usados
  actualmente).

### Output con `-v`

Cada test se imprime en una linea con su path completo:

```
backend/tests/test_health.py::TestRoot::test_root_returns_200 PASSED
backend/tests/test_health.py::TestRoot::test_root_returns_ok_status PASSED
backend/tests/test_transcriptions.py::TestGetTranscriptionById::test_get_by_id_404_when_missing PASSED
```

---

## Marcadores disponibles

| Marker | Proposito |
|--------|-----------|
| `smoke` | Tests de humo (< 2s cada uno, validan que el proceso responde) |
| `regression` | Suite de regresion completa |
| `slow` | Tests que pueden tardar > 5s (reservado para futuro) |
| `auth` | Solo se ejecutan con `TEST_AUTH=1` |

```bash
pytest backend/tests/ -m "smoke or regression" -v
pytest backend/tests/ -m "not auth" -v   # explicito: excluye auth
```

---

## Tests de autenticacion (opt-in)

Por defecto **los tests de auth estan deshabilitados** porque el backend de
desarrollo usa la clave por defecto (`dev-secret-api-key`) y el modulo
`require_auth` la bypassa (ver `backend/utils/auth.py:118-120`).

Para validar el flujo real de autenticacion:

1. Reinicia el backend con una clave real:
   ```powershell
   $env:API_KEY = "mi-clave-secreta-real"
   python backend/main.py
   ```
2. En otra terminal, corre los tests:
   ```powershell
   $env:API_KEY = "mi-clave-secreta-real"
   $env:TEST_AUTH = "1"
   .\scripts\run_backend_tests.ps1
   ```

Los 4 tests de `test_auth.py` validan:
- 200 con `x-api-key` correcta
- 200 con `Authorization: Bearer <key>`
- 401/403 sin credenciales
- 401/403 con clave incorrecta

---

## Como añadir un nuevo test

1. Crea (o edita) un archivo `backend/tests/test_<router>.py`.
2. Reutiliza los fixtures ya disponibles:
   - `http_client` -> `BackendHttpClient` con base URL y headers preconfigurados
   - `seed_transcription` / `seed_document` -> inserta data y limpia al final
   - `mongo_client` -> conexion directa a Mongo si necesitas sembrar/validar
   - `unique_id` -> id unico por test
3. Marca el archivo con `@pytest.mark.regression` o `@pytest.mark.smoke`.
4. Estructura recomendada:
   ```python
   class Test<Endpoint>:
       def test_<happy_path>(self, http_client):
           resp = http_client.get("/api/...")
           assert resp.status_code == 200
           body = resp.json()
           assert "key" in body

       def test_<negative_path>(self, http_client):
           resp = http_client.get("/api/.../no-existe")
           assert resp.status_code == 404
   ```
5. Corre el archivo en aislado:
   ```bash
   pytest backend/tests/test_<router>.py -v
   ```

---

## Troubleshooting

| Sintoma | Causa probable | Solucion |
|---------|---------------|----------|
| `Backend no accesible en /health` | El proceso `backend/main.py` no esta corriendo | `.\run_all.ps1` o `docker compose up mongodb backend` |
| `MongoDB no accesible` | El contenedor de mongo no levanto | `docker compose up -d mongodb` |
| Todos los tests de un archivo aparecen `SKIPPED` | El fixture `backend_health` fallo | Verifica que el backend este respondiendo en `/health` |
| `ModuleNotFoundError: backend.tests.helpers` | Falta `PYTHONPATH` | Usa `run_backend_tests.ps1` (lo configura) o `export PYTHONPATH=.` |
| Tests de auth fallan con 200 cuando esperan 401 | El backend esta en modo dev | Configura `API_KEY` real en el entorno del backend |
| El VAD config queda modificado tras los tests | Bug en el fixture de backup | Verifica que `temporal_docs/configuracion/.vad_config.json` no este en uso por otro proceso |

---

## Archivos del modulo

```
backend/tests/
├── __init__.py
├── pytest.ini                       # config local de pytest
├── conftest.py                      # fixtures compartidos
├── helpers/
│   ├── __init__.py
│   ├── http_client.py               # wrapper sobre requests.Session
│   └── seed.py                      # siembra/cleanup de Mongo
├── test_health.py                   # smoke: GET /, /health
├── test_vad_config.py               # /api/config/vad
├── test_transcriptions.py           # CRUD /api/transcriptions/*
├── test_documents.py                # /api/documents/*
├── test_settings.py                 # /api/settings/*
└── test_auth.py                     # opt-in (TEST_AUTH=1)

pytest.ini                           # config raiz (descubrimiento)
requirements-test.txt                # pytest, requests, pymongo
scripts/run_backend_tests.ps1        # wrapper con pre-flight checks
scripts/run_backend_only.ps1         # levanta Mongo + Backend (sin frontend)
```

---

## Cumplimiento de criterios de aceptacion

| Criterio | Estado |
|----------|--------|
| Suite de Pytest configurada en el repositorio | ✅ `pytest.ini` (raíz) + `requirements-test.txt` |
| Peticiones a endpoints principales | ✅ 5 routers, ~52 tests |
| Validar codigos HTTP esperados (200, 400, 404, 422, 500) | ✅ Cada test hace `assert resp.status_code == <expected>` |
| Validar estructura y datos de respuestas JSON | ✅ `assert isinstance()`, validacion de keys y tipos |
| Ejecucion sin intervencion manual | ✅ `pytest backend/tests/ -v` o `.\scripts\run_backend_tests.ps1` |
| Reporte claro en consola | ✅ `-v` con `--tb=short` y resumen de pass/fail/skip |
| Prevenir regresiones | ✅ Happy path + casos negativos en cada endpoint |
