#!/usr/bin/env python3
"""
Transcripción de micrófono en tiempo real usando NVIDIA Riva Cloud
Usa el servidor grpc.nvcf.nvidia.com:443 directamente
"""

import pyaudio
import sys
import os
from pathlib import Path

# Agregar python-clients al path
sys.path.insert(0, str(Path(__file__).parent / "python-clients"))

from riva.client import Auth, ASRService, AudioEncoding, StreamingRecognitionConfig, RecognitionConfig
import riva.client.audio_io as audio_io

def load_env():
    """Cargar variables de .env"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip()

def main():
    load_env()
    
    # Configuración del servidor
    server = os.getenv("RIVA_SERVER", "grpc.nvcf.nvidia.com:443")
    api_key = os.getenv("API_KEY")
    function_id = os.getenv("RIVA_FUNCTION_ID_WHISPER")
    
    if not api_key or not function_id:
        print("❌ Error: API_KEY y RIVA_FUNCTION_ID_WHISPER deben estar en .env")
        sys.exit(1)
    
    print("🎤 Transcripción en Tiempo Real con Whisper")
    print("=" * 50)
    print(f"📡 Servidor: {server}")
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"⚡ Function ID: {function_id}")
    print()
    print("🎙️  Habla ahora... (Ctrl+C para detener)")
    print("=" * 50)
    print()
    
    # Crear autenticación y servicio ASR
    auth = Auth(
        uri=server,
        use_ssl=True,
        metadata_args=[
            ["function-id", function_id],
            ["authorization", f"Bearer {api_key}"]
        ]
    )
    
    asr_service = ASRService(auth)
    
    # Configuración de audio - usar objetos de Riva correctamente
    config = StreamingRecognitionConfig(
        config=RecognitionConfig(
            encoding=AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=16000,
            language_code="es",  # Español - usar código simple
            max_alternatives=1,
            enable_automatic_punctuation=True,
            verbatim_transcripts=True,
            audio_channel_count=1,
        ),
        interim_results=True,
    )
    
    # Iniciar captura de micrófono
    try:
        print("🎤 Abriendo micrófono...")
        
        # Callback para procesar respuestas
        def print_response(response):
            if not response.results:
                return
            
            for result in response.results:
                if not result.alternatives:
                    continue
                    
                transcript = result.alternatives[0].transcript
                
                if result.is_final:
                    # Resultado final (definitivo)
                    print(f"✅ {transcript}")
                else:
                    # Resultado intermedio (mientras hablas)
                    print(f"⏳ {transcript}", end='\r')
        
        # Iniciar streaming
        with audio_io.MicrophoneStream(
            rate=16000,
            chunk=1600,
            device=None
        ) as audio_stream:
            print("✅ Micrófono activo")
            print()
            
            responses = asr_service.streaming_response_generator(
                audio_chunks=audio_stream,
                streaming_config=config
            )
            
            for response in responses:
                print_response(response)
    
    except KeyboardInterrupt:
        print("\n")
        print("🛑 Transcripción detenida")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nVerifica:")
        print("  1. Tu API_KEY en .env es válida")
        print("  2. Tu micrófono está conectado")
        print("  3. Tienes conexión a internet")

if __name__ == "__main__":
    main()
