"""
GUÍA: Cómo obtener transcripción ASR en ESPAÑOL con NVIDIA Riva

PROBLEMA ACTUAL:
Tu Cloud Function (1598d209-5e27-4d3c-8079-4751568b1081) solo tiene modelos en inglés:
- parakeet-1.1b-en-US-asr-streaming-silero-vad-sortformer
- parakeet-1.1b-en-US-asr-offline-silero-vad-sortformer

SOLUCIONES DISPONIBLES:

═══════════════════════════════════════════════════════════════════════════════
OPCIÓN 1: Usar NVIDIA NIM API (Build.NVIDIA.com) - MÁS RÁPIDO ⚡
═══════════════════════════════════════════════════════════════════════════════

NVIDIA Build ofrece modelos de ASR multilingües vía API REST simple.

Pasos:
1. Ve a: https://build.nvidia.com/explore/discover
2. Busca "Canary" o "Parakeet" con soporte español
3. Selecciona el modelo y ve a "Get API Key"
4. Usa el endpoint HTTP (no requiere gRPC)

Ejemplo con Python (requests):
```python
import requests
import os

url = "https://integrate.api.nvidia.com/v1/audio/transcriptions"
api_key = os.getenv("NGC_API_KEY")

with open("audio/mi_audio.wav", "rb") as f:
    files = {"file": f}
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"language": "es"}  # Español
    
    response = requests.post(url, headers=headers, files=files, data=data)
    print(response.json())
```

═══════════════════════════════════════════════════════════════════════════════
OPCIÓN 2: Desplegar nueva Cloud Function con modelo español
═══════════════════════════════════════════════════════════════════════════════

Pasos detallados:

1. ACCEDE AL CATÁLOGO NGC
   URL: https://catalog.ngc.nvidia.com/

2. BUSCA MODELOS ASR CON ESPAÑOL
   Busca: "riva spanish" o "parakeet multilingual" o "canary"
   
   Modelos recomendados:
   - Canary-1B (multilingüe, incluye español)
   - Parakeet (si hay versión es-ES)

3. DESPLIEGA COMO CLOUD FUNCTION
   a) Selecciona el modelo en el catálogo
   b) Click en "Deploy" o "Create Cloud Function"
   c) Configura:
      - Name: "riva-asr-spanish"
      - Region: Selecciona la más cercana
      - Instance: GPU (T4 o superior)
   d) Variables de entorno (si las solicita):
      - LANGUAGE_CODE=es-ES
      - MODEL_NAME=<el que seleccionaste>
   e) Click "Deploy"

4. OBTÉN EL NUEVO FUNCTION-ID
   Cuando el deployment termine, copia el UUID de la función
   (ej: a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6)

5. ACTUALIZA TU .env
   Añade:
   RIVA_FUNCTION_ID_ES=<nuevo-uuid>

6. PRUEBA TRANSCRIPCIÓN
   PowerShell:
   ```powershell
   $env:RIVA_FUNCTION_ID = '<nuevo-uuid>'
   
   .\.venv\Scripts\python.exe .\python-clients\scripts\asr\transcribe_file.py `
     --server grpc.nvcf.nvidia.com:443 --use-ssl `
     --metadata "function-id" "$env:RIVA_FUNCTION_ID" `
     --metadata "authorization" "Bearer $env:NGC_API_KEY" `
     --language-code es-ES `
     --input-file .\audio\mi_audio.wav
   ```

═══════════════════════════════════════════════════════════════════════════════
OPCIÓN 3: Riva Container Local (requiere GPU NVIDIA)
═══════════════════════════════════════════════════════════════════════════════

Si tienes una GPU NVIDIA con 8GB+ VRAM:

1. INSTALA NVIDIA GPU CLOUD (NGC) CLI
   https://ngc.nvidia.com/setup/installers/cli

2. DESCARGA RIVA QUICKSTART
   ```bash
   ngc registry resource download-version nvidia/riva/riva_quickstart:2.14.0
   ```

3. CONFIGURA IDIOMA ESPAÑOL
   Edita config.sh:
   ```bash
   service_enabled_asr=true
   language_code="es-ES"
   ```

4. INICIA RIVA
   ```bash
   bash riva_init.sh
   bash riva_start.sh
   ```

5. USA SERVIDOR LOCAL
   ```powershell
   python .\python-clients\scripts\asr\transcribe_file.py `
     --server localhost:50051 `
     --language-code es-ES `
     --input-file .\audio\mi_audio.wav
   ```

═══════════════════════════════════════════════════════════════════════════════
ALTERNATIVA TEMPORAL: Usar otro servicio de ASR español
═══════════════════════════════════════════════════════════════════════════════

Mientras despliegas Riva español, puedes usar:

1. OpenAI Whisper API
2. Google Cloud Speech-to-Text
3. Azure Speech Services
4. AssemblyAI

Todos tienen buenos modelos en español.

═══════════════════════════════════════════════════════════════════════════════
RECOMENDACIÓN
═══════════════════════════════════════════════════════════════════════════════

Para tu caso (proyecto universitario), recomiendo:

1. CORTO PLAZO: Prueba la función actual con inglés para validar tu pipeline
2. MEDIANO PLAZO: Despliega Cloud Function con Canary-1B (multilingüe)
3. Si no encuentras modelo español en NGC: Usa Whisper API como alternativa

¿Quieres que te ayude con alguna de estas opciones?
"""

print(__doc__)
