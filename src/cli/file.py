#!/usr/bin/env python3
"""
File transcription CLI
Transcribes audio files to markdown
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core import ConfigManager
from src.core.riva_client import RivaClientFactory
from src.transcription import FormatterFactory, OutputWriter, TranscriptionService


def main():
    if len(sys.argv) < 2:
        print("Uso: python file.py <audio_file> [language] [output_file]")
        print("\nEjemplo:")
        print("  python file.py audio/mi_audio.wav es")
        print("  python file.py audio/mi_audio.wav es notas/mi_nota.md")
        sys.exit(1)
    
    audio_file = Path(sys.argv[1])
    language = sys.argv[2] if len(sys.argv) > 2 else "es"
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not audio_file.exists():
        print(f"❌ Error: Archivo no encontrado: {audio_file}")
        sys.exit(1)
    
    print(f"🎤 Transcribiendo: {audio_file}")
    print(f"📝 Idioma: {language}")
    print()
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        riva_config = config_manager.get_riva_config()
        
        # Setup service
        transcriber = RivaClientFactory.create_transcriber(riva_config)
        formatter = FormatterFactory.create('markdown')
        writer = OutputWriter()
        service = TranscriptionService(transcriber, formatter, writer)
        
        # Transcribe
        output_path = service.transcribe_audio_file(audio_file, language, output_file)
        
        print(f"✅ Transcripción guardada en: {output_path}")
    
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
