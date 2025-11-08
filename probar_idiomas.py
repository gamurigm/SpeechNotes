#!/usr/bin/env python3
"""Probar transcripción con diferentes códigos de idioma español."""
import os
import sys
import grpc
import riva.client

# Configuración
API_KEY = os.getenv("NGC_API_KEY")
FUNCTION_ID = os.getenv("RIVA_FUNCTION_ID", "1598d209-5e27-4d3c-8079-4751568b1081")
AUDIO_FILE = "audio/mi_audio.wav"

if not API_KEY:
    with open(".env") as f:
        for line in f:
            if line.startswith("NGC_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1]
                break

print("="*70)
print("PRUEBA DE TRANSCRIPCIÓN ASR CON DIFERENTES CÓDIGOS DE IDIOMA")
print("="*70)
print(f"Archivo: {AUDIO_FILE}")
print(f"Function ID: {FUNCTION_ID}")
print("="*70 + "\n")

# Auth
auth = riva.client.Auth(
    use_ssl=True,
    uri="grpc.nvcf.nvidia.com:443",
    metadata_args=[
        ["function-id", FUNCTION_ID],
        ["authorization", f"Bearer {API_KEY}"]
    ]
)
asr = riva.client.ASRService(auth)

# Códigos de idioma a probar
language_codes = [
    "es-US",  # Español (Estados Unidos)
    "es-ES",  # Español (España)
    "es",     # Español genérico
    "en-US",  # Inglés (como control)
]

# Leer audio
with open(AUDIO_FILE, "rb") as f:
    audio_data = f.read()

for lang_code in language_codes:
    print(f"{'─'*70}")
    print(f"Probando con language_code: {lang_code}")
    print(f"{'─'*70}")
    
    try:
        # Configuración offline
        config = riva.client.RecognitionConfig(
            language_code=lang_code,
            enable_automatic_punctuation=True,
        )
        
        # Añadir specs del audio
        riva.client.add_audio_file_specs_to_config(config, AUDIO_FILE)
        
        print(f"  Enviando solicitud...")
        response = asr.offline_recognize(audio_data, config)
        
        if response.results:
            transcript = " ".join([r.alternatives[0].transcript for r in response.results])
            print(f"  ✅ ÉXITO!")
            print(f"  Transcripción: {transcript}")
        else:
            print(f"  ⚠️  Sin resultados (respuesta vacía)")
            
    except grpc.RpcError as e:
        print(f"  ❌ Error: {e.code()}")
        print(f"     {e.details()}")
    except Exception as e:
        print(f"  ❌ Error inesperado: {type(e).__name__}: {e}")
    
    print()

print("="*70)
print("RESUMEN")
print("="*70)
print("""
Si solo funcionó en-US:
  Tu función actual solo tiene modelos en inglés.
  
Si funcionó es-US o es-ES:
  ¡Genial! Tu función soporta español.
  Usa ese código de idioma en tus scripts.

Si ninguno funcionó:
  Verifica que el audio sea válido y que la función esté activa.
""")
