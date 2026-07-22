$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$MainFile = Join-Path $ProjectRoot "speechnotes_sqap.tex"
$OutputDir = Join-Path $ProjectRoot "output"

if (-not (Get-Command pdflatex -ErrorAction SilentlyContinue)) {
    Write-Error "pdflatex no está disponible. Instale MiKTeX o TeX Live."
    exit 1
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

Write-Host "Compilando SQAP de SpeechNotes..." -ForegroundColor Green

# Primera pasada
pdflatex -interaction=nonstopmode -output-directory=$OutputDir $MainFile
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error en primera pasada. Revise $OutputDir\speechnotes_sqap.log"
    exit $LASTEXITCODE
}

# Segunda pasada (referencias cruzadas)
pdflatex -interaction=nonstopmode -output-directory=$OutputDir $MainFile
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error en segunda pasada. Revise $OutputDir\speechnotes_sqap.log"
    exit $LASTEXITCODE
}

$OutputFile = Join-Path $OutputDir "speechnotes_sqap.pdf"
if (Test-Path $OutputFile) {
    Write-Host "PDF generado exitosamente: $OutputFile" -ForegroundColor Green
} else {
    Write-Error "No se encontró el PDF generado."
    exit 1
}
