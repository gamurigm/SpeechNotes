#!/usr/bin/env python3
"""
Transcripción "casi en tiempo real" usando chunks de audio
Como Whisper en NVIDIA Cloud solo soporta modo offline,
grabamos segmentos de audio y los transcribimos uno por uno.

Detecta pausas/silencios para evitar cortar palabras a la mitad.
"""

import pyaudio
import wave
import sys
import os
import tempfile
import numpy as np
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

def record_chunk_with_vad(max_duration=30, sample_rate=16000, channels=1, chunk_size=1024, 
                          voice_threshold=1200, silence_threshold=800, 
                          silence_duration=3.0, min_voice_duration=1.0):
    """
    Graba audio solo cuando detecta VOZ, ignorando ruido de fondo.
    
    Args:
        max_duration: Duración máxima del chunk en segundos
        sample_rate: Frecuencia de muestreo
        channels: Número de canales
        chunk_size: Tamaño del buffer
        voice_threshold: Umbral para detectar voz (más alto que ruido de fondo)
        silence_threshold: Umbral de silencio después de voz
        silence_duration: Segundos de silencio para terminar
        min_voice_duration: Duración mínima de voz antes de grabar
    
    Returns:
        bytes: Audio grabado en formato WAV, o None si no hay voz
    """
    audio = pyaudio.PyAudio()
    
    try:
        # Abrir stream de micrófono
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size
        )
        
        # Fase 1: Esperar a detectar VOZ
        print("🎤 Esperando voz...", end='', flush=True)
        
        voice_detected = False
        max_wait_chunks = int(sample_rate / chunk_size * 60)  # Máximo 60 segundos esperando
        
        for i in range(max_wait_chunks):
            data = stream.read(chunk_size)
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_data).mean()
            
            if volume > voice_threshold:
                voice_detected = True
                print(" 🗣️  (voz detectada!)")
                break
        
        if not voice_detected:
            print(" ⏰ (timeout)")
            stream.stop_stream()
            stream.close()
            return None
        
        # Fase 2: Grabar mientras hay voz
        print("📼 Grabando...", end='', flush=True)
        
        frames = []
        max_chunks = int(sample_rate / chunk_size * max_duration)
        silence_chunks_needed = int(sample_rate / chunk_size * silence_duration)
        min_voice_chunks = int(sample_rate / chunk_size * min_voice_duration)
        silence_chunks_count = 0
        
        for i in range(max_chunks):
            data = stream.read(chunk_size)
            frames.append(data)
            
            # Detectar volumen
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_data).mean()
            
            # Detectar fin de voz (silencio prolongado)
            if volume < silence_threshold:
                silence_chunks_count += 1
                if silence_chunks_count >= silence_chunks_needed and len(frames) >= min_voice_chunks:
                    duration = len(frames) * chunk_size / sample_rate
                    print(f" ✅ ({duration:.1f}s)")
                    break
            else:
                silence_chunks_count = 0
        
        if silence_chunks_count < silence_chunks_needed:
            print(f" ⏱️  (máx {max_duration}s)")
        
        # Cerrar stream
        stream.stop_stream()
        stream.close()
        
        # Verificar que tengamos suficiente audio
        if len(frames) < min_voice_chunks:
            return None
        
        # Convertir a WAV
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                
                with wave.open(tmp_path, 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(sample_rate)
                    wf.writeframes(b''.join(frames))
            
            with open(tmp_path, 'rb') as f:
                wav_data = f.read()
            
            return wav_data
        
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    
    finally:
        audio.terminate()

def transcribe_chunk(asr_service, audio_data, language="es"):
    """
    Transcribe un chunk de audio usando Whisper offline
    
    Args:
        asr_service: Servicio ASR de Riva
        audio_data: Audio en formato WAV (bytes)
        language: Código de idioma
    
    Returns:
        str: Transcripción del audio
    """
    config = RecognitionConfig(
        language_code=language,
        max_alternatives=1,
        enable_automatic_punctuation=True,
        verbatim_transcripts=True,
        audio_channel_count=1,
    )
    
    # Agregar especificaciones de audio desde los datos WAV
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
        print(f"\n❌ Error en transcripción: {e}")
        return ""

def save_transcription_to_markdown(transcripts, output_file=None):
    """
    Guarda todas las transcripciones en un archivo markdown
    
    Args:
        transcripts: Lista de tuplas (timestamp, texto)
        output_file: Ruta del archivo de salida (opcional)
    """
    if not transcripts:
        print("⚠️  No hay transcripciones para guardar")
        return
    
    # Generar nombre de archivo si no se proporciona
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"notas/transcripcion_realtime_{timestamp}.md"
    
    # Crear directorio si no existe
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calcular duración total
    start_time = transcripts[0][0]
    end_time = transcripts[-1][0]
    duration = (end_time - start_time).total_seconds()
    duration_mins = int(duration / 60)
    duration_secs = int(duration % 60)
    
    # Construir contenido markdown
    md_content = f"""# Transcripción en Tiempo Real

## 📋 Metadata
- **Fecha:** {start_time.strftime("%Y-%m-%d %H:%M:%S")}
- **Duración:** {duration_mins}m {duration_secs}s
- **Segmentos:** {len(transcripts)}
- **Método:** Voice Activity Detection (VAD)

---

## 📝 Transcripción Completa

"""
    
    # Agregar texto completo (sin timestamps)
    full_text = " ".join([text for _, text in transcripts])
    md_content += f"{full_text}\n\n"
    
    md_content += "---\n\n"
    md_content += "## 🕐 Transcripción por Segmentos\n\n"
    
    # Agregar segmentos con timestamps
    for timestamp, text in transcripts:
        time_str = timestamp.strftime("%H:%M:%S")
        md_content += f"**[{time_str}]** {text}\n\n"
    
    md_content += "---\n\n"
    md_content += f"*Transcrito automáticamente con Whisper Large v3*  \n"
    md_content += f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    # Guardar archivo
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✅ Transcripción guardada en: {output_path}")
    print(f"📄 Total caracteres: {len(full_text)}")
    print(f"📊 Segmentos: {len(transcripts)}")
    print(f"⏱️  Duración: {duration_mins}m {duration_secs}s")

def main():
    load_env()
    
    # Configuración del servidor
    server = os.getenv("RIVA_SERVER", "grpc.nvcf.nvidia.com:443")
    api_key = os.getenv("API_KEY")
    function_id = os.getenv("RIVA_FUNCTION_ID_WHISPER")
    
    if not api_key or not function_id:
        print("❌ Error: API_KEY y RIVA_FUNCTION_ID_WHISPER deben estar en .env")
        sys.exit(1)
    
    print("🎤 Transcripción por Segmentos con Whisper")
    print("=" * 60)
    print(f"📡 Servidor: {server}")
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"⚡ Function ID: {function_id}")
    print()
    print("⏱️  Modo: Activación por voz (VAD)")
    print("🎤 Solo graba cuando detecta tu voz, ignora ruido de fondo")
    print("� Habla normalmente, pausa 3 segundos para finalizar segmento")
    print()
    print("🎙️  Listo para escuchar... (Ctrl+C para detener)")
    print("=" * 60)
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
    
    # Variables para estadísticas y transcripciones
    segment_count = 0
    start_time = datetime.now()
    all_transcripts = []  # Lista de tuplas (timestamp, texto)
    
    try:
        while True:
            segment_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n[{timestamp}] Segmento #{segment_count}")
            print("-" * 60)
            
            # Grabar con activación por voz
            audio_data = record_chunk_with_vad(
                max_duration=30,
                voice_threshold=50,      # Valor más bajo para micrófono sensible
                silence_threshold=20,    # Valor bajo para detectar pausas
                silence_duration=3.0,    # 3 segundos de silencio para terminar
                min_voice_duration=1.0   # Mínimo 1 segundo de voz
            )
            
            # Si no hay audio válido, continuar esperando
            if audio_data is None:
                print("🔇 No se detectó voz, esperando...\n")
                continue
            
            # Transcribir
            print("📝 Transcribiendo...", end='', flush=True)
            transcript = transcribe_chunk(asr_service, audio_data, language="es")
            print(" ✅")
            
            # Mostrar resultado
            if transcript:
                print(f"\n💬 {transcript}\n")
                # Guardar transcripción con timestamp
                all_transcripts.append((datetime.now(), transcript))
            else:
                print(f"\n🔇 (Silencio o audio no reconocible)\n")
    
    except KeyboardInterrupt:
        print("\n")
        print("=" * 60)
        print("🛑 Transcripción detenida")
        print("=" * 60)
        print()
        
        # Mostrar estadísticas
        duration = (datetime.now() - start_time).total_seconds()
        duration_mins = int(duration / 60)
        duration_secs = int(duration % 60)
        
        print(f"📊 Estadísticas:")
        print(f"   - Segmentos procesados: {segment_count}")
        print(f"   - Segmentos con texto: {len(all_transcripts)}")
        print(f"   - Duración total: {duration_mins}m {duration_secs}s")
        print()
        
        # Guardar a markdown
        if all_transcripts:
            print("💾 Guardando transcripción...")
            save_transcription_to_markdown(all_transcripts)
        else:
            print("⚠️  No hay transcripciones para guardar")
        print()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nVerifica:")
        print("  1. Tu API_KEY en .env es válida")
        print("  2. Tu micrófono está conectado")
        print("  3. Tienes conexión a internet")

if __name__ == "__main__":
    main()
