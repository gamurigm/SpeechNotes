#!/usr/bin/env python3
"""
"Real-time" transcription CLI using offline chunks (VAD).
This script simulates real-time transcription by recording audio segments
when voice is detected and transcribing them one by one.
"""
import sys
from pathlib import Path
from datetime import datetime
import argparse
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core import ConfigManager
from src.core.riva_client import RivaClientFactory
from src.core.environment_factory import (
    TranscriptionEnvironmentFactoryProvider,
    EnvironmentType
)
from src.audio import (
    AudioConfig,
    VADConfig,
    MicrophoneCalibrator,
    RecorderType,
    AudioRecorderFactoryProvider
)
import tempfile
from src.transcription import FormatterFactory, OutputWriter, TranscriptionService
import json

def calibrate_microphone(audio_config: AudioConfig) -> VADConfig:
    """Realiza la calibración del micrófono y devuelve la configuración VAD."""
    print("\n" + "="*25 + " CALIBRACIÓN " + "="*25)
    print("Vamos a calibrar el micrófono para optimizar la detección de voz.")
    
    try:
        with MicrophoneCalibrator(audio_config) as calibrator:
            input("   1. Presiona Enter y guarda silencio durante 5 segundos...")
            print("      🤫 Midiendo ruido de fondo...")
            noise_levels = calibrator._measure_levels(duration=5, phase_name="SILENCIO")
            print("      ✅ Ruido medido.\n")

            input("   2. Presiona Enter y habla con normalidad durante 5 segundos...")
            print("      🗣️  Midiendo nivel de voz...")
            voice_levels = calibrator._measure_levels(duration=5, phase_name="HABLA")
            print("      ✅ Voz medida.\n")

            vad_config = calibrator.calculate_thresholds(noise_levels, voice_levels)
            
            print("   🎉 ¡Calibración completada!")
            print(f"      - Umbral de voz recomendado: {vad_config.voice_threshold}")
            print(f"      - Umbral de silencio recomendado: {vad_config.silence_threshold}")
            print("=" * 60 + "\n")
            return vad_config

    except Exception as e:
        print(f"❌ Error durante la calibración: {e}")
        print("   Usando configuración VAD por defecto.")
        return VADConfig()

def main():
    print("🎤 Transcripción por Segmentos (Simulando Tiempo Real)")
    print("=" * 60)

    try:
        # --- 1. Environment Setup using Abstract Factory ---
        # Create the Riva Live environment factory
        environment_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
        print(f"🌍 Ambiente: {environment_factory.get_name()}")
        
        # Create transcriber using the factory
        transcriber = environment_factory.create_transcriber()
        
        # Get configuration
        riva_config = transcriber.config
        
        print(f"📡 Servidor: {riva_config.server}")
        print("⏱️  Modo: Activación por voz (VAD) - Offline Chunks")
        print("🎙️  Habla normalmente, el sistema grabará y transcribirá en pausas.")
        print("   (Presiona Ctrl+C para detener y guardar la sesión)")
        print("=" * 60)

        # --- 2. Audio Configuration ---
        audio_config = AudioConfig()
        
        # Parse CLI args
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--calibrate', action='store_true', help='Run microphone calibration interactively before starting')
        parser.add_argument('--chunk-duration', type=int, default=0, help='If >0, record fixed-duration chunks (seconds) instead of VAD')
        args, _ = parser.parse_known_args()

        # Setup VAD configuration
        vad_config = _setup_vad_config(args.calibrate, audio_config)

        # --- 3. Main Transcription Loop ---
        all_transcripts = []
        segment_count = 0
        
        # Start background recorder using environment factory
        bg_recorder = _start_background_recorder(environment_factory, audio_config)

        while True:
            segment_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] Segmento #{segment_count}: Esperando voz...")

            # Create recorder using environment factory
            audio_data = _record_audio_chunk(
                environment_factory,
                audio_config,
                vad_config,
                args.chunk_duration
            )

            if audio_data is None:
                print("   🔇 No se grabó audio válido, reintentando...")
                continue

            # Transcribe using factory-created transcriber
            print("   📝 Transcribiendo chunk...", end='', flush=True)
            transcript = transcriber.offline_transcribe(audio_data, language="es")
            print(" ✅", flush=True)

            if transcript:
                print(f"   💬 Texto reconocido: {transcript}")
                all_transcripts.append((datetime.now(), transcript))
            else:
                print("   ⚠️  (Silencio o audio no reconocible por el servidor)")
                print("   💡 Consejo: Intenta hablar más claro o aumenta el volumen del micrófono")

    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("🛑 Transcripción Detenida por el Usuario")
        print("=" * 60)
        _save_transcription_results(all_transcripts, bg_recorder)

    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ Error de Configuración: {e}")
        print("   Asegúrate de que tu archivo .env existe y es correcto.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error Inesperado: {e}")
        sys.exit(1)


def _setup_vad_config(should_calibrate: bool, audio_config: AudioConfig) -> VADConfig:
    """
    Setup VAD configuration based on user preferences
    
    Args:
        should_calibrate: Whether to run calibration
        audio_config: Audio configuration object
        
    Returns:
        VADConfig instance configured and ready to use
    """
    if should_calibrate:
        vad_config = calibrate_microphone(audio_config)
        vad_config.silence_duration = 2.0
        vad_config.min_voice_duration = 0.4
    else:
        print("⚙️ Calibración omitida. Usando configuración VAD por defecto o guardada.")
        vad_config = VADConfig()
        
        # Try to load saved VAD config if present
        vad_file = project_root / 'temporal_docs' / 'configuracion' / '.vad_config.json'
        if vad_file.exists():
            try:
                data = json.loads(vad_file.read_text())
                vt = int(data.get('voice_threshold', vad_config.voice_threshold))
                st = int(data.get('silence_threshold', vad_config.silence_threshold))
                vad_config.voice_threshold = vt
                vad_config.silence_threshold = st
                print(f"   Umbrales cargados desde {vad_file}: voice={vt}, silence={st}")
            except Exception as e:
                print(f"   ⚠️ No se pudo leer {vad_file}: {e}")

        vad_config.silence_duration = 2.0
        vad_config.min_voice_duration = 0.4
        print(f"   Umbral de voz: {vad_config.voice_threshold}, Umbral de silencio: {vad_config.silence_threshold}")
    
    return vad_config


def _start_background_recorder(environment_factory, audio_config: AudioConfig):
    """
    Start background recorder for session recording using Abstract Factory
    
    Args:
        environment_factory: TranscriptionEnvironmentFactory instance
        audio_config: Audio configuration
        
    Returns:
        BackgroundRecorder instance or None if failed
    """
    try:
        bg_recorder = environment_factory.create_recorder(
            RecorderType.BACKGROUND,
            audio_config=audio_config
        )
        bg_recorder.start()
        print("   🔴 Grabando sesión completa en background...")
        return bg_recorder
    except Exception as e:
        print(f"   ⚠️ No se pudo iniciar grabación en background: {e}")
        return None


def _record_audio_chunk(
    environment_factory,
    audio_config: AudioConfig,
    vad_config: VADConfig,
    chunk_duration: int
) -> Optional[bytes]:
    """
    Record an audio chunk using the environment factory
    
    Args:
        environment_factory: TranscriptionEnvironmentFactory instance
        audio_config: Audio configuration
        vad_config: VAD configuration
        chunk_duration: Duration for fixed chunks (0 = use VAD)
        
    Returns:
        Audio data as bytes or None if failed
    """
    if chunk_duration and chunk_duration > 0:
        print(f"   ⏱️  Grabando chunk fijo de {chunk_duration}s...")
        recorder = environment_factory.create_recorder(
            RecorderType.CONTINUOUS,
            audio_config=audio_config
        )
        with recorder as rec:
            def stop_cb(frames_count):
                elapsed = frames_count * audio_config.chunk_size / audio_config.sample_rate
                return elapsed >= chunk_duration

            audio_data = rec.record(stop_callback=stop_cb)
            if audio_data and len(audio_data) > 0:
                print(f"   ✅ Chunk grabado: {len(audio_data)} bytes")
                return audio_data
            else:
                print("   ❌ No se capturó audio en el chunk")
                return None
    else:
        recorder = environment_factory.create_recorder(
            RecorderType.VAD,
            audio_config=audio_config,
            vad_config=vad_config
        )
        with recorder as rec:
            print("   👂 Escuchando... (detectará automáticamente cuando hables)")
            
            def on_voice_detected_callback():
                print("   🗣️  ¡Voz detectada! Grabando...", flush=True)
            
            audio_data = rec.record(
                on_voice_detected=on_voice_detected_callback,
            )
            
            if audio_data and len(audio_data) > 0:
                print(f"   ✅ Audio grabado: {len(audio_data)} bytes")
                return audio_data
            else:
                print("   ❌ No se capturó audio (intenta hablar más fuerte o cerca del micrófono)")
                return None


def _save_transcription_results(all_transcripts, bg_recorder):
    """
    Save transcription results and background recording
    
    Args:
        all_transcripts: List of (timestamp, transcript) tuples
        bg_recorder: Background recorder instance or None
    """
    if all_transcripts:
        print("\n💾 Guardando transcripción completa...")
        
        try:
            segmented_formatter = FormatterFactory.create('segmented_markdown')
            writer = OutputWriter()
            service = TranscriptionService(None, segmented_formatter, writer)  # transcriber param not used here

            output_path = service.transcribe_segments(
                all_transcripts, 
                method="VAD (Real-time simulation)"
            )
            
            print(f"✅ Transcripción guardada en: {output_path}")
        except Exception as e:
            print(f"⚠️ Error al guardar transcripción: {e}")
    else:
        print("⚠️ No hay transcripciones para guardar.")

    # Stop background recorder
    if bg_recorder:
        try:
            # Ensure directory exists
            recordings_dir = project_root / 'temporal_docs' / 'grabaciones'
            recordings_dir.mkdir(parents=True, exist_ok=True)

            tmp_path = recordings_dir / f"realtime_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            bg_recorder.stop_and_save(str(tmp_path))
            print(f"✅ Grabación de sesión guardada en: {tmp_path}")

            # Use TranscriptionService to transcribe the full recording
            try:
                from src.core.environment_factory import TranscriptionEnvironmentFactoryProvider
                environment_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
                transcriber = environment_factory.create_transcriber()
                
                file_formatter = FormatterFactory.create('markdown')
                file_writer = OutputWriter()
                file_service = TranscriptionService(transcriber, file_formatter, file_writer)
                print("🎯 Transcribiendo la grabación completa...")
                file_output = file_service.transcribe_audio_file(tmp_path, language='es')
                print(f"✅ Transcripción de la grabación guardada en: {file_output}")
            except Exception as e:
                print(f"⚠️ Error al transcribir la grabación completa: {e}")

        except Exception as e:
            print(f"⚠️ Error al detener/guardar la grabación background: {e}")


if __name__ == "__main__":
    main()
