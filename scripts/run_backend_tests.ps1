<#
    run_backend_tests.ps1
    Runs the Pytest backend suite with pre-flight checks.

    Pre-requisites:
        - Backend running on http://localhost:9443 (or BACKEND_URL override)
        - MongoDB running on mongodb://localhost:27017 (or MONGO_URI override)
        - Python 3.10+ with dependencies from requirements-test.txt installed

    Usage:
        .\scripts\run_backend_tests.ps1                 # full suite
        .\scripts\run_backend_tests.ps1 -Smoke          # smoke only
        .\scripts\run_backend_tests.ps1 -Auth            # opt-in auth tests
        .\scripts\run_backend_tests.ps1 -SkipChecks     # skip pre-flight (faster)
        .\scripts\run_backend_tests.ps1 -Test "test_health.py"  # one file
#>

[CmdletBinding()]
param(
    [switch]$Smoke,
    [switch]$Auth,
    [switch]$SkipChecks,
    [string]$Test = "",
    [string]$BackendUrl = "http://localhost:9443"
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot

# ── Resolve Python interpreter ───────────────────────────────────────────────
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonExe)) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    Write-Host "[ERROR] Python no encontrado. Activa el .venv o instala Python 3.10+." -ForegroundColor Red
    exit 1
}
Write-Host "[*] Usando Python: $PythonExe" -ForegroundColor Gray

# ── Pre-flight: backend health ───────────────────────────────────────────────
if (-not $SkipChecks) {
    Write-Host "[*] Verificando backend en $BackendUrl/health ..." -ForegroundColor Cyan
    try {
        $resp = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 5
        if ($resp.StatusCode -ne 200) {
            Write-Host "[ERROR] Backend respondio $($resp.StatusCode) en /health" -ForegroundColor Red
            Write-Host "Levanta el backend antes de correr los tests:" -ForegroundColor Yellow
            Write-Host "    .\run_all.ps1" -ForegroundColor Yellow
            Write-Host "    o: docker compose up mongodb backend" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "[OK] Backend respondio $($resp.StatusCode) en /health" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Backend no accesible en $BackendUrl/health" -ForegroundColor Red
        Write-Host "Detalle: $($_.Exception.Message)" -ForegroundColor Gray
        Write-Host "Levanta el backend antes de correr los tests:" -ForegroundColor Yellow
        Write-Host "    .\run_all.ps1" -ForegroundColor Yellow
        Write-Host "    o: docker compose up mongodb backend" -ForegroundColor Yellow
        exit 1
    }

    # ── Pre-flight: MongoDB reachable ───────────────────────────────────────
    $MongoUri = $env:MONGO_URI
    if (-not $MongoUri) { $MongoUri = "mongodb://localhost:27017" }
    Write-Host "[*] Verificando MongoDB en $MongoUri ..." -ForegroundColor Cyan
    $mongoCheck = & $PythonExe -c "import sys; from pymongo import MongoClient; from pymongo.errors import PyMongoError; 
try:
    c = MongoClient('$MongoUri', serverSelectionTimeoutMS=2000); c.admin.command('ping'); print('OK')
except PyMongoError as e:
    print(f'FAIL:{e}'); sys.exit(1)
" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] MongoDB no accesible en $MongoUri" -ForegroundColor Red
        Write-Host "Detalle: $mongoCheck" -ForegroundColor Gray
        Write-Host "Levanta MongoDB antes de correr los tests:" -ForegroundColor Yellow
        Write-Host "    docker compose up mongodb" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[OK] MongoDB accesible" -ForegroundColor Green
}

# ── Install test dependencies (idempotent) ───────────────────────────────────
Write-Host "[*] Verificando dependencias de testing..." -ForegroundColor Cyan
& $PythonExe -m pip install -q -r (Join-Path $RootDir "requirements-test.txt")
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Fallo instalando requirements-test.txt" -ForegroundColor Red
    exit 1
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
Write-Host "[*] Ejecutando: $PythonExe -m pytest $($pytestArgs -join ' ')" -ForegroundColor Cyan
Write-Host ""

Push-Location -LiteralPath $RootDir
try {
    & $PythonExe -m pytest @pytestArgs
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
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
