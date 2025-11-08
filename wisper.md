# Whisper Large V3 - Transcription Guide

## ⚠️ Important Notes
- **Streaming mode NOT supported** - `transcribe_mic.py` will NOT work with this function
- **Only offline/batch mode** - use `transcribe_file_offline.py` for file-based transcription
- **Spanish works perfectly** in offline mode
- Authentication requires NGC API key in `.env`

## Quick Start (PowerShell)

### Using the helper script
```powershell
# Spanish transcription
.\transcribe_audio.ps1 -AudioFile "audio\mi_audio.wav" -Language "es"

# French to English translation
.\transcribe_audio.ps1 -AudioFile "audio\french_audio.wav" -Language "fr" -Translate
```

### Manual command (if you prefer)
```powershell
# Load .env first
Get-Content .\.env | ForEach-Object { $_ = $_.Trim(); if ([string]::IsNullOrWhiteSpace($_) -or $_.StartsWith("#")) { return }; $parts = $_ -split "=", 2; if ($parts.Length -eq 2) { $name = $parts[0].Trim(); $value = $parts[1].Trim(); if ($value.StartsWith('"') -and $value.EndsWith('"')) { $value = $value.Trim('"') }; if ($value.StartsWith("'") -and $value.EndsWith("'")) { $value = $value.Trim("'") }; Set-Item -Path "env:$name" -Value $value } }

# Transcribe Spanish audio
python .\python-clients\scripts\asr\transcribe_file_offline.py `
  --server $env:RIVA_SERVER `
  --use-ssl `
  --metadata function-id $env:RIVA_FUNCTION_ID_WHISPER `
  --metadata "authorization" "Bearer $env:API_KEY" `
  --language-code es `
  --input-file .\audio\mi_audio.wav
```

---

openai
whisper-large-v3
Run Anywhere
Robust Speech Recognition via Large-Scale Weak Supervision.


asr

ast

multilingual

nvidia nim

nvidia riva

openai

batch

speech-to-text

whisper
Get API Key
Experience
Model Card
Try API
Deploy
API Reference
Accelerated by DGX Cloud
Get API Key
Getting Started
Riva uses gRPC APIs. Instructions below demonstrate usage of whisper-large-v3 model using Python gRPC client.

Prerequisites
You will need a system with Git and Python 3+ installed.

Install Riva Python Client
Bash

Copy
pip install nvidia-riva-client
Download Python Client
Download Python client code by cloning Python Client Repository.

Bash

Copy
git clone https://github.com/nvidia-riva/python-clients.git
Run Python Client
Make sure you have a speech file in Mono, 16-bit audio in WAV, OPUS and FLAC formats. If you have generated the API key, it will be auto-populated in the command. Open a command terminal and execute below command to transcribe audio. Specifying --language-code as multi will enable auto language detection. If you know the source language, it is recommended to specify for better accuracy and latency. See Supported Languages for the list of all available languages and corresponding code.

Bash

Copy
python python-clients/scripts/asr/transcribe_file_offline.py \
    --server grpc.nvcf.nvidia.com:443 --use-ssl \
    --metadata function-id "b702f636-f60c-4a3d-a6f4-f3568c13bd7d" \
    --metadata "authorization" "Bearer $API_KEY_REQUIRED_IF_EXECUTING_OUTSIDE_NGC" \
    --language-code en \
    --input-file <path_to_audio_file>
Below command demonstrates translation from French (fr) to English.

Bash

Copy
python python-clients/scripts/asr/transcribe_file_offline.py \
    --server grpc.nvcf.nvidia.com:443 --use-ssl \
    --metadata function-id "b702f636-f60c-4a3d-a6f4-f3568c13bd7d" \
    --metadata "authorization" "Bearer $API_KEY_REQUIRED_IF_EXECUTING_OUTSIDE_NGC" \
    --language-code fr \
    --custom-configuration "task:translate" \
    --input-file <path_to_audio_file>
Support for gRPC clients in other languages
Riva uses gRPC APIs. Proto files can be downloaded from Riva gRPC Proto files and compiled to target language using Protoc compiler. Example Riva clients in C++ and Python languages are provided below.

Python Client Repository
C++ Client Repository
Terms of Use
Privacy Policy
Your Privacy Choices
Contact
