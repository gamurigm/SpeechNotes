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

def transcribe_audio(audio_file: str, language: str = "es") -> dict:
    """Transcribe audio file using Whisper API"""
    
    # Load environment variables
    api_key = os.getenv("API_KEY")
    server = os.getenv("RIVA_SERVER")
    function_id = os.getenv("RIVA_FUNCTION_ID_WHISPER")
    
    if not all([api_key, server, function_id]):
        print("❌ Error: Variables de entorno no configuradas")
        print("Ejecuta primero:")
        print('  Get-Content .\\.env | ForEach-Object { ... }')
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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'  # Replace invalid UTF-8 chars instead of crashing
        )
        
        if result.returncode != 0:
            print(f"❌ Error en transcripción: {result.stderr}")
            sys.exit(1)
        
        # Parse JSON output (the script outputs JSON + final transcript)
        lines = result.stdout.strip().split('\n')
        
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
    
    # Build markdown content
    md_content = f"""# Transcripción: {audio_path.name}

## 📋 Metadata
- **Fecha de transcripción:** {timestamp}
- **Archivo de audio:** `{audio_path.name}`
- **Idioma:** {data["language"]}
- **Duración:** {duration_mins}m {duration_secs}s
- **Segmentos:** {len(data["results"])}

---

## 📝 Transcripción Completa

{data["transcript"]}

---

## 🔍 Segmentos por Tiempo

"""
    
    # Add segments (every 30 seconds)
    for i, result in enumerate(data["results"]):
        if "alternatives" in result and result["alternatives"]:
            transcript_segment = result["alternatives"][0].get("transcript", "")
            audio_time = result.get("audioProcessed", 0)
            mins = int(audio_time / 60)
            secs = int(audio_time % 60)
            
            md_content += f"### [{mins:02d}:{secs:02d}]\n\n"
            md_content += f"{transcript_segment}\n\n"
    
    md_content += f"""---

*Transcrito automáticamente con Whisper Large v3*  
*Generado: {timestamp}*
"""
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
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
