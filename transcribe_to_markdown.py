#!/usr/bin/env python3
"""
Transcribe audio to markdown file using Whisper API
Usage: python transcribe_to_markdown.py <audio_file> [language]
"""

import sys
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path

def load_env_file(env_path: str = ".env"):
    """Load environment variables from .env file"""
    if not os.path.exists(env_path):
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                os.environ[key] = value
    
    return True

def transcribe_audio(audio_file: str, language: str = "es") -> dict:
    """Transcribe audio file using Whisper API"""
    
    # Load .env file automatically
    if not load_env_file():
        print("⚠️  Advertencia: Archivo .env no encontrado")
    
    # Load environment variables
    api_key = os.getenv("API_KEY")
    server = os.getenv("RIVA_SERVER")
    function_id = os.getenv("RIVA_FUNCTION_ID_WHISPER")
    
    if not all([api_key, server, function_id]):
        print("❌ Error: Variables de entorno no configuradas en .env")
        print("Verifica que el archivo .env contenga:")
        print("  API_KEY=tu_api_key")
        print("  RIVA_SERVER=tu_servidor")
        print("  RIVA_FUNCTION_ID_WHISPER=tu_function_id")
        sys.exit(1)
    
    # Build command - use sys.executable to use the same Python as current script
    cmd = [
        sys.executable,  # Use current Python interpreter (from .venv if activated)
        "./python-clients/scripts/asr/transcribe_file_offline.py",
        "--server", server,
        "--use-ssl",
        "--metadata", "function-id", function_id,
        "--metadata", "authorization", f"Bearer {api_key}",
        "--language-code", language,
        "--input-file", audio_file
    ]
    
    print(f"🎤 Transcribiendo: {audio_file}")
    print(f"📝 Idioma: {language}")
    
    # Execute transcription
    try:
        # Forzar UTF-8 en el subproceso para Windows
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=False,  # Get bytes instead of text
            env=env
        )
        
        if result.returncode != 0:
            stderr_text = result.stderr.decode('utf-8', errors='replace')
            print(f"❌ Error en transcripción: {stderr_text}")
            sys.exit(1)
        
        # Decode output with proper UTF-8 handling
        stdout_text = result.stdout.decode('utf-8', errors='ignore')
        
        # Parse JSON output (the script outputs JSON + final transcript)
        lines = stdout_text.strip().split('\n')
        
        # Find JSON part
        json_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break
        
        if json_start == -1:
            print("❌ No se encontró respuesta JSON")
            sys.exit(1)
        
        # Extract final transcript (last line after "Final transcript:")
        final_transcript = ""
        for i, line in enumerate(lines):
            if line.startswith("Final transcript:"):
                final_transcript = line.replace("Final transcript:", "").strip()
                break
        
        # Parse JSON
        json_text = '\n'.join(lines[json_start:])
        # Find where JSON ends (before "Final transcript:")
        if "Final transcript:" in json_text:
            json_text = json_text.split("Final transcript:")[0].strip()
        
        data = json.loads(json_text)
        
        return {
            "transcript": final_transcript,
            "results": data.get("results", []),
            "language": language,
            "audio_file": audio_file
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def save_to_markdown(data: dict, output_file: str = None):
    """Save transcription to markdown file"""
    
    audio_path = Path(data["audio_file"])
    
    # Generate output filename if not provided
    if output_file is None:
        output_file = f"notas/{audio_path.stem}_transcripcion.md"
    
    # Create output directory if needed
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get metadata
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    audio_duration = data["results"][-1].get("audioProcessed", 0) if data["results"] else 0
    duration_mins = int(audio_duration / 60)
    duration_secs = int(audio_duration % 60)
    
    # Build markdown content (sin segmentos por tiempo)
    md_content = f"""# Transcripción: {audio_path.name}

## 📋 Metadata
- **Fecha de transcripción:** {timestamp}
- **Archivo de audio:** `{audio_path.name}`
- **Idioma:** {data["language"]}
- **Duración:** {duration_mins}m {duration_secs}s

---

## 📝 Transcripción Completa

{data["transcript"]}

---

*Transcrito automáticamente con Whisper Large v3*  
*Generado: {timestamp}*
"""
    
    # Save to file with BOM for proper Windows encoding
    with open(output_path, 'w', encoding='utf-8-sig') as f:
        f.write(md_content)
    
    print(f"\n✅ Transcripción guardada en: {output_path}")
    print(f"📄 Tamaño: {len(data['transcript'])} caracteres")
    print(f"⏱️  Duración: {duration_mins}m {duration_secs}s")

def main():
    if len(sys.argv) < 2:
        print("Uso: python transcribe_to_markdown.py <audio_file> [language] [output_file]")
        print("\nEjemplo:")
        print("  python transcribe_to_markdown.py audio/mi_audio.wav es")
        print("  python transcribe_to_markdown.py audio/mi_audio.wav es notas/mi_nota.md")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "es"
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Check audio file exists
    if not os.path.exists(audio_file):
        print(f"❌ Error: Archivo no encontrado: {audio_file}")
        sys.exit(1)
    
    # Transcribe
    data = transcribe_audio(audio_file, language)
    
    # Save to markdown
    save_to_markdown(data, output_file)

if __name__ == "__main__":
    main()
