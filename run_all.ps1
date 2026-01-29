# Script to run both Backend and Frontend for SpeechNotes

# 1. Kill potentially hanging processes (Optional, uncomment if needed)
# Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*p\backend*" } | Stop-Process -Force
# Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*p\web*" } | Stop-Process -Force

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
