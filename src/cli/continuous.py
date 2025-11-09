#!/usr/bin/env python3
"""
Continuous recording and transcription CLI
Records continuously until stopped, then transcribes
"""
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    ConfigManager,
    RivaClientFactory,
    AudioConfig,
    ContinuousRecorder,
    FormatterFactory,
    OutputWriter,
    TranscriptionService
)


def main():
    print("🎙️  Grabación Continua con Transcripción Final")
    print("=" * 60)
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        riva_config = config_manager.get_riva_config()
        
        print(f"📡 Servidor: {riva_config.server}")
        print(f"🔑 API Key: {riva_config.api_key[:20]}...")
        print()
        
        # Setup service
        transcriber = RivaClientFactory.create_transcriber(riva_config)
        formatter = FormatterFactory.create('markdown')
        writer = OutputWriter()
        service = TranscriptionService(transcriber, formatter, writer)
        
        # Record audio
        print("🎤 Iniciando grabación continua...")
        print("   Presiona Ctrl+C para detener y transcribir")
        print()
        
        audio_config = AudioConfig()
        start_time = datetime.now()
        
        with ContinuousRecorder(audio_config) as recorder:
            print("🔴 GRABANDO... (habla todo lo que necesites)\n")
            
            try:
                audio_data = recorder.record()
            except KeyboardInterrupt:
                print("\n⏸️  Grabación detenida\n")
                audio_data = None
        
        if audio_data:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("📝 Transcribiendo audio completo...")
            print("   (Esto puede tardar un momento)\n")
            
            # Transcribe (need to save temporarily)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = Path(tmp.name)
            
            try:
                output_path = service.transcribe_audio_file(
                    tmp_path,
                    language="es"
                )
                
                print("✅ Transcripción completada")
                print(f"📄 Archivo: {output_path}")
                print(f"⏱️  Duración: {int(duration//60)}m {int(duration%60)}s")
            finally:
                tmp_path.unlink(missing_ok=True)
    
    except KeyboardInterrupt:
        print("\n🛑 Proceso cancelado")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Crea un archivo .env con tus credenciales")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
