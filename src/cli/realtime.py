#!/usr/bin/env python3
"""
Real-time transcription CLI
Transcribes microphone input in real-time using streaming
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    ConfigManager,
    RivaClientFactory,
    AudioConfig,
    MicrophoneStream
)


def print_response(transcript: str, is_final: bool):
    """Print transcription response"""
    if is_final:
        print(f"✅ {transcript}")
    else:
        print(f"⏳ {transcript}", end='\r')


def main():
    print("🎤 Transcripción en Tiempo Real con Whisper")
    print("=" * 60)
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        riva_config = config_manager.get_riva_config()
        
        print(f"📡 Servidor: {riva_config.server}")
        print(f"🔑 API Key: {riva_config.api_key[:20]}...")
        print(f"⚡ Function ID: {riva_config.function_id}")
        print()
        print("🎙️  Habla ahora... (Ctrl+C para detener)")
        print("=" * 60)
        print()
        
        # Create transcriber
        transcriber = RivaClientFactory.create_transcriber(riva_config)
        
        # Create audio stream
        audio_config = AudioConfig(sample_rate=16000, chunk_size=1600)
        
        with MicrophoneStream(audio_config) as mic_stream:
            print("✅ Micrófono activo\n")
            
            # Stream transcription
            for transcript, is_final in transcriber.streaming_transcribe(
                mic_stream.record(),
                language="es"
            ):
                print_response(transcript, is_final)
    
    except KeyboardInterrupt:
        print("\n")
        print("🛑 Transcripción detenida")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Crea un archivo .env con tus credenciales")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nVerifica:")
        print("  1. Tu API_KEY en .env es válida")
        print("  2. Tu micrófono está conectado")
        print("  3. Tienes conexión a internet")
        sys.exit(1)


if __name__ == "__main__":
    main()
