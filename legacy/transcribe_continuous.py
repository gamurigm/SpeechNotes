#!/usr/bin/env python3
"""
Grabación continua de audio con transcripción al finalizar
Graba todo el audio y lo transcribe cuando se detiene (Ctrl+C)
"""

import pyaudio
import wave
import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Agregar python-clients al path
sys.path.insert(0, str(Path(__file__).parent / "python-clients"))

from riva.client import Auth, ASRService, RecognitionConfig
import riva.client

def load_env():
    """Cargar variables de .env"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip()

def record_audio_continuous(sample_rate=16000, channels=1, chunk_size=1024):
    """
    Graba audio continuamente hasta que se presione Ctrl+C
    
    Returns:
        str: Ruta al archivo WAV temporal
    """
    audio = pyaudio.PyAudio()
    
    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    print("🎤 Iniciando grabación continua...")
    print("   Presiona Ctrl+C para detener y transcribir")
    print()
    
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk_size
    )
    
    frames = []
    start_time = datetime.now()
    
    try:
        print("🔴 GRABANDO... (habla todo lo que necesites)")
        print()
        
        chunk_count = 0
        while True:
            data = stream.read(chunk_size)
            frames.append(data)
            chunk_count += 1
            
            # Mostrar progreso cada segundo
            if chunk_count % (sample_rate // chunk_size) == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                mins = int(elapsed // 60)
                secs = int(elapsed % 60)
                print(f"\r⏱️  Tiempo grabado: {mins:02d}:{secs:02d}", end='', flush=True)
    
    except KeyboardInterrupt:
        print("\n")
        print("⏸️  Grabación detenida")
        
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Guardar en archivo WAV
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
        
        duration = (datetime.now() - start_time).total_seconds()
        mins = int(duration // 60)
        secs = int(duration % 60)
        
        print(f"✅ Audio guardado ({mins}m {secs}s)")
        print()
        
        return temp_path, start_time, duration

def transcribe_audio_file(asr_service, audio_path, language="es"):
    """
    Transcribe un archivo de audio completo
    
    Args:
        asr_service: Servicio ASR de Riva
        audio_path: Ruta al archivo de audio
        language: Código de idioma
    
    Returns:
        str: Transcripción completa
    """
    print("📝 Transcribiendo audio completo...")
    print("   (Esto puede tardar un momento)")
    print()
    
    # Leer archivo de audio
    with open(audio_path, 'rb') as f:
        audio_data = f.read()
    
    # Configurar transcripción
    config = RecognitionConfig(
        language_code=language,
        max_alternatives=1,
        enable_automatic_punctuation=True,
        verbatim_transcripts=True,
        audio_channel_count=1,
    )
    
    # Agregar especificaciones de audio desde el archivo WAV
    riva.client.add_audio_file_specs_to_config(config, audio_data)
    
    try:
        response = asr_service.offline_recognize(audio_data, config)
        
        # Extraer transcripción
        if response.results:
            transcript = " ".join([
                alt.transcript 
                for result in response.results 
                for alt in result.alternatives
            ])
            return transcript.strip()
        return ""
    
    except Exception as e:
        print(f"❌ Error en transcripción: {e}")
        return ""

def save_to_markdown(transcript, start_time, duration, output_file=None):
    """
    Guarda la transcripción en un archivo markdown
    
    Args:
        transcript: Texto transcrito
        start_time: Hora de inicio de la grabación
        duration: Duración en segundos
        output_file: Ruta del archivo de salida (opcional)
    """
    if not transcript:
        print("⚠️  No hay transcripción para guardar")
        return
    
    # Generar nombre de archivo si no se proporciona
    if output_file is None:
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        output_file = f"notas/grabacion_{timestamp}.md"
    
    # Crear directorio si no existe
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calcular duración
    duration_mins = int(duration // 60)
    duration_secs = int(duration % 60)
    
    # Construir contenido markdown
    md_content = f"""# Grabación de Audio Transcrita

## 📋 Metadata
- **Fecha:** {start_time.strftime("%Y-%m-%d %H:%M:%S")}
- **Duración:** {duration_mins}m {duration_secs}s
- **Palabras:** ~{len(transcript.split())} palabras
- **Caracteres:** {len(transcript)}

---

## 📝 Transcripción

{transcript}

---

*Transcrito automáticamente con Whisper Large v3*  
*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # Guardar archivo
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print()
    print("=" * 60)
    print("✅ TRANSCRIPCIÓN COMPLETADA")
    print("=" * 60)
    print(f"📄 Archivo: {output_path}")
    print(f"📊 Palabras: ~{len(transcript.split())}")
    print(f"📏 Caracteres: {len(transcript)}")
    print(f"⏱️  Duración: {duration_mins}m {duration_secs}s")
    print()

def main():
    load_env()
    
    # Configuración del servidor
    server = os.getenv("RIVA_SERVER", "grpc.nvcf.nvidia.com:443")
    api_key = os.getenv("API_KEY")
    function_id = os.getenv("RIVA_FUNCTION_ID_WHISPER")
    
    if not api_key or not function_id:
        print("❌ Error: API_KEY y RIVA_FUNCTION_ID_WHISPER deben estar en .env")
        sys.exit(1)
    
    print("🎙️  Grabación Continua con Transcripción Final")
    print("=" * 60)
    print(f"📡 Servidor: {server}")
    print(f"🔑 API Key: {api_key[:20]}...")
    print()
    
    # Paso 1: Grabar audio
    audio_path = None
    try:
        audio_path, start_time, duration = record_audio_continuous()
        
        # Paso 2: Crear conexión con servidor
        print("🔗 Conectando con servidor de transcripción...")
        auth = Auth(
            uri=server,
            use_ssl=True,
            metadata_args=[
                ["function-id", function_id],
                ["authorization", f"Bearer {api_key}"]
            ]
        )
        
        asr_service = ASRService(auth)
        print("✅ Conectado")
        print()
        
        # Paso 3: Transcribir
        transcript = transcribe_audio_file(asr_service, audio_path, language="es")
        
        if transcript:
            print("✅ Transcripción completada")
            print()
            print("💬 Vista previa:")
            print("-" * 60)
            preview = transcript[:200] + "..." if len(transcript) > 200 else transcript
            print(preview)
            print("-" * 60)
            print()
            
            # Paso 4: Guardar a markdown
            save_to_markdown(transcript, start_time, duration)
        else:
            print("❌ No se pudo transcribir el audio")
            print("   Verifica que hayas hablado durante la grabación")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nVerifica:")
        print("  1. Tu API_KEY en .env es válida")
        print("  2. Tu micrófono está conectado")
        print("  3. Tienes conexión a internet")
    
    finally:
        # Limpiar archivo temporal
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except:
                pass

if __name__ == "__main__":
    main()
