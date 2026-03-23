# Script to run both Backend and Frontend for SpeechNotes

# Pre-check: MongoDB via Docker (WSL)
Write-Host "[*] Verificando MongoDB en Docker..." -ForegroundColor Gray
$mongoRunning = wsl docker ps --filter "name=speechnotes-mongodb" --format "{{.Status}}" 2>$null
if (-not $mongoRunning) {
    Write-Host "[*] Iniciando MongoDB en Docker (WSL)..." -ForegroundColor Yellow
    wsl -e bash -c "cd /mnt/c/Users/gamur/Documents/SN/SpeechNotes && docker compose up -d mongodb" 2>$null
    Start-Sleep -Seconds 3
    Write-Host "[OK] MongoDB iniciado en Docker." -ForegroundColor Green
} else {
    Write-Host "[OK] MongoDB ya esta corriendo en Docker." -ForegroundColor Green
}

# 1. Kill potentially hanging processes
Write-Host "[*] Limpiando procesos anteriores..." -ForegroundColor Gray
# Kill processes by name/path
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*p\backend*" -or $_.CommandLine -like "*backend/main.py*" } | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*p\web*" } | Stop-Process -Force

# Kill anything listening on backend or frontend ports
$ports = @(9443, 3006)
foreach ($port in $ports) {
    $portProcess = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($portProcess) {
        $portProcess | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    }
}


Write-Host "[*] Iniciando SpeechNotes..." -ForegroundColor Cyan

# Get the root directory
$RootDir = Get-Location

# 2. Start Backend in a new window
Write-Host "[*] Iniciando Backend en puerto 9443..." -ForegroundColor Green
$PythonPath = "$RootDir\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonPath)) { $PythonPath = "python" } # fallback
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location -LiteralPath '$RootDir'; `$env:PYTHONPATH='backend;.' ; & '$PythonPath' backend/main.py" -WindowStyle Normal

# 3. Start Frontend in a new window
Write-Host "[*] Iniciando Frontend en puerto 3006..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location -LiteralPath '$RootDir\web'; npm run dev" -WindowStyle Normal

# 4. Start Desktop App
Write-Host "[*] Iniciando Desktop App..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location -LiteralPath '$RootDir\desktop'; npm run electron:dev" -WindowStyle Normal
Write-Host "Services started!"



