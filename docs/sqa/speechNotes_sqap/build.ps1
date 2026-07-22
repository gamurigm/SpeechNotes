$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$MainFile = Join-Path $ProjectRoot "speechnotes_sqap.tex"
$OutputDir = Join-Path $ProjectRoot "output"

if (-not (Get-Command pdflatex -ErrorAction SilentlyContinue)) {
    Write-Error "pdflatex no está disponible. Instale MiKTeX o TeX Live."
    exit 1
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

Write-Host "Compilando SQAP de SpeechNotes..." -ForegroundColor Green
Set-Location $ProjectRoot

# Primera pasada
pdflatex -interaction=nonstopmode -output-directory="output" speechnotes_sqap.tex

# Segunda pasada (referencias cruzadas)
pdflatex -interaction=nonstopmode -output-directory="output" speechnotes_sqap.tex

$OutputFile = Join-Path $OutputDir "speechnotes_sqap.pdf"
if (Test-Path $OutputFile) {
    Write-Host "PDF generado exitosamente: $OutputFile" -ForegroundColor Green
} else {
    Write-Error "No se encontró el PDF generado."
    exit 1
}
