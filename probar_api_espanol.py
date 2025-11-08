#!/usr/bin/env python3
"""
Probar API de NVIDIA Build para ASR en español.
Busca modelos disponibles y prueba transcripción.
"""
import os
import requests
import json

# Cargar API key
API_KEY = os.getenv("NGC_API_KEY")
if not API_KEY:
    with open(".env") as f:
        for line in f:
            if line.startswith("NGC_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1]
                break

if not API_KEY:
    print("❌ No se encontró NGC_API_KEY")
    exit(1)

print("🔍 Buscando endpoints de ASR en NVIDIA API...")
print(f"🔑 API Key: {API_KEY[:10]}...{API_KEY[-4:]}\n")

# Endpoints a probar
endpoints = [
    "https://integrate.api.nvidia.com/v1/audio/transcriptions",
    "https://ai.api.nvidia.com/v1/audio/transcriptions",
    "https://api.nvcf.nvidia.com/v2/nvcf/audio/transcriptions",
]

audio_file = "audio/mi_audio.wav"

if not os.path.exists(audio_file):
    print(f"❌ Archivo de audio no encontrado: {audio_file}")
    print("   Asegúrate de que audio/mi_audio.wav existe")
    exit(1)

print(f"📁 Archivo de audio: {audio_file}")
print(f"📊 Tamaño: {os.path.getsize(audio_file) / 1024:.2f} KB\n")

# Probar cada endpoint
for endpoint in endpoints:
    print(f"{'='*70}")
    print(f"Probando: {endpoint}")
    print(f"{'='*70}")
    
    try:
        with open(audio_file, "rb") as f:
            # Intentar diferentes formatos de request
            configs = [
                {
                    "name": "Básico con language=es",
                    "files": {"file": f},
                    "data": {"language": "es"},
                },
            ]
            
            for config in configs:
                print(f"\n  Configuración: {config['name']}")
                
                f.seek(0)  # Reset file pointer
                
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                }
                
                response = requests.post(
                    endpoint,
                    headers=headers,
                    files=config.get("files"),
                    data=config.get("data"),
                    timeout=30
                )
                
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"  ✅ ÉXITO!")
                    try:
                        result = response.json()
                        print(f"  Transcripción:")
                        print(f"  {json.dumps(result, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"  Respuesta: {response.text[:500]}")
                    break
                else:
                    print(f"  ❌ Error: {response.text[:200]}")
                    
    except requests.exceptions.Timeout:
        print(f"  ⏱️  Timeout (servidor no respondió)")
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {e}")
    
    print()

print("\n" + "="*70)
print("CONCLUSIÓN")
print("="*70)
print("""
Si ningún endpoint funcionó, significa que NVIDIA no tiene una API REST
pública para ASR en español actualmente.

Tus opciones son:
1. Desplegar Cloud Function con modelo español (Opción 2 de la guía)
2. Usar Riva container localmente con GPU (Opción 3)
3. Usar servicio alternativo (Whisper API, Google, Azure)

Para validar tu pipeline actual, puedes probar con el modelo inglés
que ya tienes disponible.
""")
