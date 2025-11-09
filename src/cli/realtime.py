#!/usr/bin/env python3
"""
Real-time transcription CLI
Transcribes microphone input in real-time using streaming
"""
import sys
from pathlib import Path

# Add project root and python-clients to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python-clients"))

from src.core import ConfigManager
from riva.client import Auth, ASRService, AudioEncoding, StreamingRecognitionConfig, RecognitionConfig
import riva.client.audio_io as audio_io


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
        
        # Create authentication and ASR service
        auth = Auth(
            uri=riva_config.server,
            use_ssl=True,
            metadata_args=[
                ["function-id", riva_config.function_id],
                ["authorization", f"Bearer {riva_config.api_key}"]
            ]
        )
        
        asr_service = ASRService(auth)
        
        # Audio configuration - use Riva objects correctly
        config = StreamingRecognitionConfig(
            config=RecognitionConfig(
                encoding=AudioEncoding.LINEAR_PCM,
                sample_rate_hertz=16000,
                language_code="es",
                max_alternatives=1,
                enable_automatic_punctuation=True,
                verbatim_transcripts=True,
                audio_channel_count=1,
            ),
            interim_results=True,
        )
        
        print("🎤 Abriendo micrófono...")
        
        # Callback to process responses
        def print_response(response):
            if not response.results:
                return
            
            for result in response.results:
                if not result.alternatives:
                    continue
                    
                transcript = result.alternatives[0].transcript
                
                if result.is_final:
                    print(f"✅ {transcript}")
                else:
                    print(f"⏳ {transcript}", end='\r')
        
        # Start streaming with Riva's MicrophoneStream
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
