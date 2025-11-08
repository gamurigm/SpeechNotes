# Whisper Setup - Working Configuration ✅

## Problem Solved
- ✅ Authentication working (API_KEY from NGC now in `.env`)
- ✅ Spanish transcription working perfectly
- ⚠️ Streaming mode (mic) NOT supported by this function
- ✅ Offline/batch transcription works great

## What Works

### ✅ Offline Transcription (File-based)
```powershell
# Using helper script (recommended)
.\transcribe_audio.ps1 -AudioFile "audio\mi_audio.wav" -Language "es"

# Manual command
python .\python-clients\scripts\asr\transcribe_file_offline.py `
  --server $env:RIVA_SERVER `
  --use-ssl `
  --metadata function-id $env:RIVA_FUNCTION_ID_WHISPER `
  --metadata "authorization" "Bearer $env:API_KEY" `
  --language-code es `
  --input-file .\audio\mi_audio.wav
```

### ✅ Translation (e.g., French → English)
```powershell
# Using helper script
.\transcribe_audio.ps1 -AudioFile "audio\french.wav" -Language "fr" -Translate

# Manual
python .\python-clients\scripts\asr\transcribe_file_offline.py `
  --server $env:RIVA_SERVER `
  --use-ssl `
  --metadata function-id $env:RIVA_FUNCTION_ID_WHISPER `
  --metadata "authorization" "Bearer $env:API_KEY" `
  --language-code fr `
  --custom-configuration "task:translate" `
  --input-file .\audio\french.wav
```

## What Doesn't Work

### ❌ Streaming from Microphone
```powershell
# This will FAIL with: "Unavailable model requested... type=online"
python .\python-clients\scripts\asr\transcribe_mic.py ... # ❌ NOT SUPPORTED
```

**Reason:** The Whisper function `b702f636-f60c-4a3d-a6f4-f3568c13bd7d` only supports offline/batch mode, not real-time streaming.

**Workaround:** Record audio to a file first, then transcribe with `transcribe_file_offline.py`.

## Environment Variables (in `.env`)

```properties
# NGC API Key (required)
API_KEY=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
NGC_API_KEY=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

# Function ID for Whisper
RIVA_FUNCTION_ID_WHISPER=b702f636-f60c-4a3d-a6f4-f3568c13bd7d

# Server endpoint
RIVA_SERVER=grpc.nvcf.nvidia.com:443
```

## Load .env in PowerShell

Run this once per session to load environment variables:

```powershell
Get-Content .\.env | ForEach-Object {
  $line = $_.Trim()
  if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) { return }
  $parts = $line -split "=", 2
  if ($parts.Length -eq 2) {
    $name = $parts[0].Trim()
    $value = $parts[1].Trim()
    if ($value.StartsWith('"') -and $value.EndsWith('"')) { $value = $value.Trim('"') }
    if ($value.StartsWith("'") -and $value.EndsWith("'")) { $value = $value.Trim("'") }
    Set-Item -Path "env:$name" -Value $value
  }
}
Write-Host "✓ Loaded .env" -ForegroundColor Green
```

## Supported Languages

According to NVIDIA docs, Whisper supports:
- `en` - English
- `es` - Spanish ✅ tested
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ja` - Japanese
- `ko` - Korean
- `zh` - Chinese
- `multi` - Auto-detect (use if source language unknown)

## Audio Requirements

- **Format:** WAV, OPUS, or FLAC
- **Channels:** Mono (single channel)
- **Bit depth:** 16-bit
- **Sample rate:** 16000 Hz recommended

### Check your audio file
```powershell
python .\check_wav.py .\audio\mi_audio.wav
```

## Example Output

The successful transcription of `audio\mi_audio.wav` returned a full Spanish transcript (1362 seconds / ~23 minutes) about reported speech in English grammar lessons.

## Troubleshooting

### Error: UNAUTHENTICATED
- Check `$env:API_KEY` length: should be ~70 chars, not 15
- Reload `.env` with the command above
- Verify key at https://org.ngc.nvidia.com/setup/api-key

### Error: INVALID_ARGUMENT "Unavailable model... type=online"
- You tried streaming mode (`transcribe_mic.py`) — not supported
- Use `transcribe_file_offline.py` instead

### Error: DNS resolution failed
- Check `$env:RIVA_SERVER` is set to `grpc.nvcf.nvidia.com:443`
- Don't use placeholder `<RIVA_SERVER_HOST:PORT>`

## Next Steps

If you want to transcribe live mic input:
1. Record audio to a file (use Windows Voice Recorder or similar)
2. Transcribe the recorded file with `transcribe_file_offline.py`

Or look for a different Riva function that supports streaming (check NVIDIA's function catalog).

---

✅ **Current status:** Offline Spanish transcription working perfectly!
