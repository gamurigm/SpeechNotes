<#
    run_backend_only.ps1
    Starts ONLY MongoDB + the Python backend (no frontend, no Tauri).
    Exits when both services are healthy and ready for tests.

    Designed for WSL workflows: Docker runs inside WSL, so this script
    invokes 'wsl docker ...' for container operations (mirroring the
    pattern used in run_all.ps1). Python and HTTP health checks run
    natively on Windows, which work transparently because WSL2 forwards
    localhost to the Windows host.

    Usage:
        .\scripts\run_backend_only.ps1                 # start and wait
        .\scripts\run_backend_only.ps1 -SkipDocker     # don't manage Mongo
        .\scripts\run_backend_only.ps1 -BackendOnly    # only start backend, skip Mongo
        .\scripts\run_backend_only.ps1 -UseWindowsDocker  # fallback if Docker is in Windows

    Exit codes:
        0  Success (Mongo + Backend ready)
        1  Docker (WSL) not available
        2  Mongo did not respond to ping within timeout
        3  Backend did not respond on /health within timeout
        4  No Python interpreter found
        5  WSL not available
#>

[CmdletBinding()]
param(
    [switch]$SkipDocker,
    [switch]$BackendOnly,
    [switch]$UseWindowsDocker,
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

# Compute the WSL-side path of the project root. Used for 'wsl docker compose -f ...'.
function Get-WslPath([string]$WindowsPath) {
    # C:\Dev\GitHub\SpeechNotes  ->  /mnt/c/Dev/GitHub/SpeechNotes
    $drive = $WindowsPath.Substring(0, 1).ToLower()
    $rest = $WindowsPath.Substring(2) -replace "\\", "/"
    return "/mnt/$drive/$rest"
}

# Run a command in the default WSL distribution, returning the exit code
# and printing combined stdout/stderr.
function Invoke-Wsl([string]$BashCommand) {
    $output = & wsl -e bash -c $BashCommand 2>&1
    $code = $LASTEXITCODE
    return @{ Output = $output; ExitCode = $code }
}

# ── Step 0: WSL available? ──────────────────────────────────────────────────
if (-not $UseWindowsDocker) {
    Write-Step "Verificando WSL..."
    $wslOk = $false
    try {
        $wslStatus = & wsl --status 2>&1
        if ($LASTEXITCODE -eq 0) {
            $wslOk = $true
        }
    }
    catch { }

    if (-not $wslOk) {
        Write-Err "WSL no esta disponible. Se requiere WSL para Docker."
        Write-Hint "Instala WSL:  wsl --install"
        Write-Hint "O usa -UseWindowsDocker si tienes Docker Desktop nativo en Windows."
        exit 5
    }
    Write-Ok "WSL disponible"
}

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

    if ($UseWindowsDocker) {
        # Use Windows-native docker
        try {
            $null = docker info 2>&1
            if ($LASTEXITCODE -eq 0) { $dockerOk = $true }
        }
        catch { }
        if (-not $dockerOk) {
            Write-Err "Docker (Windows nativo) no esta corriendo o no esta instalado."
            Write-Hint "Inicia Docker Desktop y vuelve a correr este script."
            exit 1
        }
        Write-Ok "Docker (Windows) disponible"
    }
    else {
        # Use WSL docker
        $res = Invoke-Wsl "docker info > /dev/null 2>&1 && echo OK || echo FAIL"
        if ($res.ExitCode -eq 0 -and ($res.Output -join "") -match "OK") {
            $dockerOk = $true
        }
        if (-not $dockerOk) {
            Write-Err "Docker no esta corriendo en WSL o no esta instalado."
            Write-Hint "Desde WSL:  sudo service docker start   o  inicia Docker Desktop."
            Write-Hint "O usa -UseWindowsDocker si tienes Docker nativo en Windows."
            exit 1
        }
        Write-Ok "Docker (WSL) disponible"
    }

    # Compose file path (WSL-style for wsl docker compose)
    $composeWslPath = Get-WslPath (Join-Path $RootDir "docker-compose.yml")
    $projectWslDir = Get-WslPath $RootDir

    Write-Step "Iniciando MongoDB (docker compose up -d mongodb)..."
    $res = Invoke-Wsl "cd '$projectWslDir' && docker compose up -d mongodb"
    $res.Output | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    if ($res.ExitCode -ne 0) {
        Write-Err "docker compose fallo con codigo $($res.ExitCode)"
        exit 1
    }

    # ── Step 5: Wait for Mongo ping (via Windows python against localhost) ────
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
        Write-Hint "Revisa los logs: wsl docker compose -f '$composeWslPath' logs mongodb"
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

# ── Step 7: Wait for /health (Windows-side, localhost) ──────────────────────
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
    Write-Hint "Para pruebas manuales via WSL:  curl http://localhost:9443/health"
    exit 3
}
Write-Ok "Backend listo en $BackendUrl"

# ── Step 8: Final instructions ──────────────────────────────────────────────
Write-Host ""
Write-Host "=== Servicios listos ===" -ForegroundColor Green
Write-Host "  - MongoDB:  $MongoUri  (corriendo en WSL Docker)" -ForegroundColor Gray
Write-Host "  - Backend:  $BackendUrl  (corriendo en Windows)" -ForegroundColor Gray
Write-Host ""
Write-Host "Ahora puedes correr los tests en otra terminal:" -ForegroundColor Cyan
Write-Host "    .\scripts\run_backend_tests.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Cuando termines, cierra la ventana del backend o ejecuta:" -ForegroundColor Cyan
Write-Host "    Get-Process python | Where-Object { `$_.CommandLine -like '*backend/main.py*' } | Stop-Process" -ForegroundColor White

exit 0
