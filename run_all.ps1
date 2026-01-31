# Script to run both Backend and Frontend for SpeechNotes

# Pre-check: MongoDB status
$MongoService = Get-Service MongoDB -ErrorAction SilentlyContinue
if ($MongoService -and $MongoService.Status -ne 'Running') {
    Write-Host "⚠️ ADVERTENCIA: El servicio MongoDB no está iniciado." -ForegroundColor Red
    Write-Host "Por favor, abre PowerShell como ADMINISTRADOR y corre: Start-Service MongoDB" -ForegroundColor Yellow
}
elseif (-not $MongoService) {
    Write-Host "⚠️ ADVERTENCIA: No se encontró el servicio MongoDB instalado." -ForegroundColor Red
}

# 1. Kill potentially hanging processes
Write-Host "🧹 Limpiando procesos anteriores..." -ForegroundColor Gray
# Kill processes by name/path
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*p\backend*" -or $_.CommandLine -like "*backend/main.py*" } | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*p\web*" } | Stop-Process -Force
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force

# Kill anything listening on backend port 8001
$portProcess = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($portProcess) {
    $portProcess | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

Write-Host "🚀 Iniciando SpeechNotes..." -ForegroundColor Cyan

# Get the root directory
$RootDir = Get-Location

# 2. Start Backend in a new window
Write-Host "📦 Iniciando Backend en puerto 8001..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootDir'; `$env:PYTHONPATH='backend;.' ; .venv\Scripts\python.exe backend/main.py" -WindowStyle Normal

# 3. Start Frontend in a new window
Write-Host "🌐 Iniciando Frontend en puerto 3006..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootDir/web'; pnpm dev" -WindowStyle Normal

Write-Host "✅ ¡Todo listo! Verifica las nuevas ventanas abiertas." -ForegroundColor Yellow
Write-Host "Backend: http://localhost:8001"
Write-Host "Frontend: http://localhost:3006"
