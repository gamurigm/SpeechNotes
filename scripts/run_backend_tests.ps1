<#
    run_backend_tests.ps1
    Runs the Pytest backend suite with pre-flight checks.

    Pre-requisites:
        - Backend running on http://localhost:9443 (or BACKEND_URL override)
        - MongoDB running on mongodb://localhost:27017 (or MONGO_URI override)
        - Python 3.10+ with dependencies from requirements-test.txt installed

    WSL note: Docker typically runs inside WSL, while Python and the backend
    run on Windows. Both the pre-flight health check and pytest can run from
    PowerShell because WSL2 forwards localhost to Windows. Use -UseWsl if
    your Python interpreter lives inside WSL.

    Usage:
        .\scripts\run_backend_tests.ps1                 # full suite
        .\scripts\run_backend_tests.ps1 -Smoke          # smoke only
        .\scripts\run_backend_tests.ps1 -Auth           # opt-in auth tests
        .\scripts\run_backend_tests.ps1 -SkipChecks     # skip pre-flight
        .\scripts\run_backend_tests.ps1 -Test "test_health.py"
        .\scripts\run_backend_tests.ps1 -UseWsl         # run pytest from inside WSL
#>

[CmdletBinding()]
param(
    [switch]$Smoke,
    [switch]$Auth,
    [switch]$SkipChecks,
    [switch]$UseWsl,
    [string]$Test = "",
    [string]$BackendUrl = "http://localhost:9443"
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot

# ── Helpers ─────────────────────────────────────────────────────────────────
function Write-Step($msg)  { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Err($msg)   { Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Write-Hint($msg)  { Write-Host "    $msg" -ForegroundColor Yellow }

function Get-WslPath([string]$WindowsPath) {
    $drive = $WindowsPath.Substring(0, 1).ToLower()
    $rest = $WindowsPath.Substring(2) -replace "\\", "/"
    return "/mnt/$drive/$rest"
}

# ── Resolve Python interpreter ───────────────────────────────────────────────
$pythonMode = "windows"
$PythonExe = $null

if ($UseWsl) {
    Write-Step "Usando Python dentro de WSL (-UseWsl)..."
    # Check that WSL is up
    try {
        $null = & wsl --status 2>&1
        if ($LASTEXITCODE -ne 0) { throw "wsl --status fallo" }
    }
    catch {
        Write-Err "WSL no esta disponible."
        exit 1
    }
    # Look for venv inside WSL
    $wslDir = Get-WslPath $RootDir
    $venvCheck = & wsl -e bash -c "test -x '$wslDir/.venv/bin/python' && echo OK || echo MISSING" 2>&1
    if ($venvCheck -match "OK") {
        $PythonExe = "$wslDir/.venv/bin/python"
        $pythonMode = "wsl"
        Write-Ok "Python (WSL venv): $PythonExe"
    }
    else {
        $fallbackCheck = & wsl -e bash -c "command -v python3 >/dev/null 2>&1 && echo OK || echo MISSING" 2>&1
        if ($fallbackCheck -match "OK") {
            $PythonExe = "python3"
            $pythonMode = "wsl"
            Write-Ok "Python (WSL system): python3"
        }
        else {
            Write-Err "WSL no tiene un Python utilizable."
            Write-Hint "Crea el venv:  wsl -e bash -c 'cd $wslDir && python3 -m venv .venv && .venv/bin/pip install -r requirements-test.txt'"
            exit 1
        }
    }
}
else {
    Write-Step "Resolviendo interprete de Python (Windows)..."
    $PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $PythonExe)) {
        $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    }
    if (-not $PythonExe) {
        Write-Err "Python no encontrado. Activa el .venv o instala Python 3.10+."
        Write-Hint "O usa -UseWsl si tu Python esta dentro de WSL."
        exit 1
    }
    Write-Ok "Python (Windows): $PythonExe"
}

# Helper: run a Python command and return the exit code
function Invoke-PythonCheck([string]$PyCode) {
    if ($pythonMode -eq "wsl") {
        $escaped = $PyCode -replace '"', '\"'
        $res = & wsl -e bash -c "$PythonExe -c `"$escaped`"" 2>&1
        return @{ Output = $res; ExitCode = $LASTEXITCODE }
    }
    else {
        $res = & $PythonExe -c $PyCode 2>&1
        return @{ Output = $res; ExitCode = $LASTEXITCODE }
    }
}

# ── Pre-flight: backend health ───────────────────────────────────────────────
if (-not $SkipChecks) {
    Write-Step "Verificando backend en $BackendUrl/health ..."
    try {
        $resp = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 5
        if ($resp.StatusCode -ne 200) {
            Write-Err "Backend respondio $($resp.StatusCode) en /health"
            Write-Hint "Levanta el backend antes de correr los tests:"
            Write-Hint "    .\run_all.ps1                                (todo el stack)"
            Write-Hint "    .\scripts\run_backend_only.ps1               (solo Mongo + backend, recomendado)"
            exit 1
        }
        Write-Ok "Backend respondio $($resp.StatusCode) en /health"
    }
    catch {
        Write-Err "Backend no accesible en $BackendUrl/health"
        Write-Host "    Detalle: $($_.Exception.Message)" -ForegroundColor Gray
        Write-Hint "Si Docker esta en WSL, asegurate de haber corrido run_backend_only.ps1 primero."
        Write-Hint "O levantalo manualmente:  python backend/main.py"
        exit 1
    }

    # ── Pre-flight: MongoDB reachable ───────────────────────────────────────
    $MongoUri = $env:MONGO_URI
    if (-not $MongoUri) { $MongoUri = "mongodb://localhost:27017" }
    Write-Step "Verificando MongoDB en $MongoUri ..."
    $pyCode = @"
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import sys
try:
    c = MongoClient('$MongoUri', serverSelectionTimeoutMS=2000)
    c.admin.command('ping')
    print('OK')
except PyMongoError as e:
    print(f'FAIL:{e}')
    sys.exit(1)
"@
    $res = Invoke-PythonCheck $pyCode
    if ($res.ExitCode -ne 0) {
        Write-Err "MongoDB no accesible en $MongoUri"
        $res.Output | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        Write-Hint "Si Docker esta en WSL:  wsl docker compose -f $(Get-WslPath (Join-Path $RootDir 'docker-compose.yml')) up -d mongodb"
        Write-Hint "O mas facil:  .\scripts\run_backend_only.ps1"
        exit 1
    }
    Write-Ok "MongoDB accesible"
}

# ── Install test dependencies (idempotent) ───────────────────────────────────
Write-Step "Verificando dependencias de testing..."
if ($pythonMode -eq "wsl") {
    $wslDir = Get-WslPath $RootDir
    & wsl -e bash -c "cd '$wslDir' && '$PythonExe' -m pip install -q -r requirements-test.txt" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Fallo instalando requirements-test.txt (WSL)"
        exit 1
    }
}
else {
    & $PythonExe -m pip install -q -r (Join-Path $RootDir "requirements-test.txt")
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Fallo instalando requirements-test.txt"
        exit 1
    }
}

# ── Build the pytest command ─────────────────────────────────────────────────
$pytestArgs = @("backend/tests", "-v", "--tb=short", "--color=yes")

if ($Smoke) {
    $pytestArgs += @("-m", "smoke")
}
elseif ($Auth) {
    $env:TEST_AUTH = "1"
    Write-Host "[*] TEST_AUTH=1 -> se incluiran los tests de auth (requiere API_KEY real en el backend)" -ForegroundColor Yellow
}

if ($Test -ne "") {
    $pytestArgs = @("backend/tests/$Test", "-v", "--tb=short", "--color=yes")
}

# Make sure the conftest can import `backend.tests.helpers` by adding root to PYTHONPATH
$env:PYTHONPATH = "$RootDir;$RootDir\backend;$env:PYTHONPATH"
$env:BACKEND_URL = $BackendUrl

Write-Host ""
if ($pythonMode -eq "wsl") {
    $wslDir = Get-WslPath $RootDir
    Write-Host "[*] Ejecutando en WSL: $PythonExe -m pytest $($pytestArgs -join ' ')" -ForegroundColor Cyan
}
else {
    Write-Host "[*] Ejecutando: $PythonExe -m pytest $($pytestArgs -join ' ')" -ForegroundColor Cyan
}
Write-Host ""

$exitCode = 0
if ($pythonMode -eq "wsl") {
    $wslDir = Get-WslPath $RootDir
    $wslBackendDir = "$wslDir/backend"
    $joined = $pytestArgs -join ' '
    # NOTE: use ${wslDir} and ${wslBackendDir} to avoid PowerShell parsing
    # $wslDir:$wslDir as a scope-qualified variable.
    & wsl -e bash -c "cd '${wslDir}' && PYTHONPATH='${wslDir}:${wslBackendDir}' BACKEND_URL='$BackendUrl' '$PythonExe' -m pytest $joined"
    $exitCode = $LASTEXITCODE
}
else {
    Push-Location -LiteralPath $RootDir
    try {
        & $PythonExe -m pytest @pytestArgs
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "[OK] Suite de tests completa con exito." -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "[FAIL] Algunos tests fallaron. Revisa el output arriba." -ForegroundColor Red
}
exit $exitCode
