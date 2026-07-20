<#
    run_backend_only.ps1
    Starts ONLY MongoDB + the Python backend (no frontend, no Tauri).
    Exits when both services are healthy and ready for tests.

    Use this when you want to run the Pytest suite without spinning up
    the full SpeechNotes stack (frontend / desktop app).

    Usage:
        .\scripts\run_backend_only.ps1                 # start and wait
        .\scripts\run_backend_only.ps1 -SkipDocker     # don't manage Mongo (use existing)
        .\scripts\run_backend_only.ps1 -BackendOnly    # only start the backend, skip Mongo

    Exit codes:
        0  Success (Mongo + Backend ready)
        1  Docker not available
        2  Mongo did not respond to ping within timeout
        3  Backend did not respond on /health within timeout
        4  No Python interpreter found
#>

[CmdletBinding()]
param(
    [switch]$SkipDocker,
    [switch]$BackendOnly,
    [int]$MongoTimeoutSec = 30,
    [int]$BackendTimeoutSec = 30
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
$BackendUrl = "http://localhost:9443"
$MongoUri = "mongodb://localhost:27017"

# ── Helpers ─────────────────────────────────────────────────────────────────
function Write-Step($msg)  { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Err($msg)   { Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Write-Hint($msg)  { Write-Host "    $msg" -ForegroundColor Yellow }

# ── Step 1: Python ──────────────────────────────────────────────────────────
Write-Step "Resolviendo interprete de Python..."
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonExe)) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    Write-Err "Python no encontrado. Activa el .venv o instala Python 3.10+."
    Write-Hint "python --version"
    exit 4
}
Write-Ok "Python: $PythonExe"

# ── Step 2: Free port 9443 ───────────────────────────────────────────────────
Write-Step "Liberando puerto 9443..."
$portProcess = Get-NetTCPConnection -LocalPort 9443 -ErrorAction SilentlyContinue
if ($portProcess) {
    $portProcess | ForEach-Object {
        try {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction Stop
            Write-Host "    - PID $($_.OwningProcess) terminado" -ForegroundColor Gray
        }
        catch {
            Write-Host "    - No se pudo terminar PID $($_.OwningProcess): $($_.Exception.Message)" -ForegroundColor DarkYellow
        }
    }
    Start-Sleep -Seconds 1
}
else {
    Write-Host "    (puerto libre)" -ForegroundColor Gray
}

# ── Step 3 + 4: MongoDB ─────────────────────────────────────────────────────
if (-not $SkipDocker -and -not $BackendOnly) {
    Write-Step "Verificando Docker..."
    $dockerOk = $false
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerOk = $true
        }
    }
    catch { }

    if (-not $dockerOk) {
        Write-Err "Docker no esta corriendo o no esta instalado."
        Write-Hint "Inicia Docker Desktop y vuelve a correr este script."
        Write-Hint "o usa -SkipDocker si ya tienes MongoDB corriendo en otro host."
        exit 1
    }
    Write-Ok "Docker disponible"

    Write-Step "Iniciando MongoDB (docker compose up -d mongodb)..."
    Push-Location -LiteralPath $RootDir
    try {
        & docker compose up -d mongodb 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    }
    finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Err "docker compose fallo con codigo $LASTEXITCODE"
        exit 1
    }

    # ── Step 5: Wait for Mongo ping ──────────────────────────────────────────
    Write-Step "Esperando a que MongoDB responda a ping (timeout ${MongoTimeoutSec}s)..."
    $deadline = (Get-Date).AddSeconds($MongoTimeoutSec)
    $mongoReady = $false
    while ((Get-Date) -lt $deadline) {
        $pingResult = & $PythonExe -c "
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import sys
try:
    c = MongoClient('$MongoUri', serverSelectionTimeoutMS=1500)
    c.admin.command('ping')
    print('OK')
except PyMongoError as e:
    print(f'FAIL:{e}')
    sys.exit(1)
" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $mongoReady = $true
            break
        }
        Start-Sleep -Seconds 2
    }
    if (-not $mongoReady) {
        Write-Err "MongoDB no respondio a ping en ${MongoTimeoutSec}s."
        Write-Hint "Revisa los logs: docker compose logs mongodb"
        exit 2
    }
    Write-Ok "MongoDB listo en $MongoUri"
}
else {
    if ($BackendOnly) {
        Write-Host "[SKIP] Saltando MongoDB (-BackendOnly)" -ForegroundColor DarkYellow
    }
    else {
        Write-Host "[SKIP] Saltando MongoDB (-SkipDocker)" -ForegroundColor DarkYellow
    }
}

# ── Step 6: Launch backend in new PowerShell window ─────────────────────────
Write-Step "Lanzando backend en nueva ventana PowerShell..."
$backendCmd = "Set-Location -LiteralPath '$RootDir'; `$env:PYTHONPATH='backend;.' ; & '$PythonExe' backend/main.py"
try {
    Start-Process powershell `
        -ArgumentList "-NoExit", "-Command", $backendCmd `
        -WindowStyle Normal `
        -WorkingDirectory $RootDir | Out-Null
    Write-Ok "Ventana de backend lanzada"
}
catch {
    Write-Err "No se pudo lanzar el backend: $($_.Exception.Message)"
    exit 3
}

# ── Step 7: Wait for /health ────────────────────────────────────────────────
Write-Step "Esperando a que el backend responda en $BackendUrl/health (timeout ${BackendTimeoutSec}s)..."
$deadline = (Get-Date).AddSeconds($BackendTimeoutSec)
$backendReady = $false
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    }
    catch {
        # Backend not up yet, keep polling
    }
    Start-Sleep -Seconds 1
}

if (-not $backendReady) {
    Write-Err "El backend no respondio en /health en ${BackendTimeoutSec}s."
    Write-Hint "Revisa la ventana del backend que se acaba de abrir."
    Write-Hint "O ejecutalo manualmente:  python backend/main.py"
    exit 3
}
Write-Ok "Backend listo en $BackendUrl"

# ── Step 8: Final instructions ──────────────────────────────────────────────
Write-Host ""
Write-Host "=== Servicios listos ===" -ForegroundColor Green
Write-Host "  - MongoDB:  $MongoUri" -ForegroundColor Gray
Write-Host "  - Backend:  $BackendUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "Ahora puedes correr los tests en otra terminal:" -ForegroundColor Cyan
Write-Host "    .\scripts\run_backend_tests.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Cuando termines, cierra la ventana del backend o ejecuta:" -ForegroundColor Cyan
Write-Host "    Get-Process python | Where-Object { `$_.CommandLine -like '*backend/main.py*' } | Stop-Process" -ForegroundColor White

exit 0
