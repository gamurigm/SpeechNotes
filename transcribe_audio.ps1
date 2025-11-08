# transcribe_audio.ps1 - Helper script for Whisper transcription
# Usage:
#   .\transcribe_audio.ps1 -AudioFile "audio\mi_audio.wav" -Language "es"
#   .\transcribe_audio.ps1 -AudioFile "audio\mi_audio.wav" -Language "fr" -Translate

param(
    [Parameter(Mandatory=$true)]
    [string]$AudioFile,
    
    [Parameter(Mandatory=$false)]
    [string]$Language = "es",
    
    [Parameter(Mandatory=$false)]
    [switch]$Translate
)

# Load .env if not already loaded
if (-not $env:API_KEY -or -not $env:RIVA_SERVER) {
    Write-Host "Loading .env..." -ForegroundColor Yellow
    Get-Content .\.env | ForEach-Object {
        $_ = $_.Trim()
        if ([string]::IsNullOrWhiteSpace($_) -or $_.StartsWith("#")) { return }
        $parts = $_ -split "=", 2
        if ($parts.Length -eq 2) {
            $name = $parts[0].Trim()
            $value = $parts[1].Trim()
            if ($value.StartsWith('"') -and $value.EndsWith('"')) { $value = $value.Trim('"') }
            if ($value.StartsWith("'") -and $value.EndsWith("'")) { $value = $value.Trim("'") }
            Set-Item -Path "env:$name" -Value $value
        }
    }
}

# Verify env vars
if (-not $env:API_KEY) {
    Write-Error "API_KEY not set. Please check your .env file."
    exit 1
}

if (-not $env:RIVA_SERVER) {
    Write-Error "RIVA_SERVER not set. Please check your .env file."
    exit 1
}

if (-not $env:RIVA_FUNCTION_ID_WHISPER) {
    Write-Error "RIVA_FUNCTION_ID_WHISPER not set. Please check your .env file."
    exit 1
}

# Build command
$cmd = @(
    "python",
    ".\python-clients\scripts\asr\transcribe_file_offline.py",
    "--server", $env:RIVA_SERVER,
    "--use-ssl",
    "--metadata", "function-id", $env:RIVA_FUNCTION_ID_WHISPER,
    "--metadata", "authorization", "Bearer $env:API_KEY",
    "--language-code", $Language,
    "--input-file", $AudioFile
)

if ($Translate) {
    $cmd += "--custom-configuration"
    $cmd += "task:translate"
}

Write-Host "Transcribing: $AudioFile (language: $Language)" -ForegroundColor Cyan
if ($Translate) {
    Write-Host "Translation mode: ON (translating to English)" -ForegroundColor Cyan
}

# Execute with venv python
$venvPython = ".\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython $cmd[1..($cmd.Length-1)]
} else {
    Write-Warning "Virtual environment not found. Using system python."
    & $cmd[0] $cmd[1..($cmd.Length-1)]
}
