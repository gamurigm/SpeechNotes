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

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core import ConfigManager
from src.core.riva_client import RivaClientFactory
from src.audio import AudioConfig, VADRecorder, VADConfig, MicrophoneCalibrator, ContinuousRecorder, BackgroundRecorder
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
        # --- 1. Configuration ---
        config_manager = ConfigManager()
        riva_config = config_manager.get_riva_config()

        print(f"📡 Servidor: {riva_config.server}")
        print("⏱️  Modo: Activación por voz (VAD) - Offline Chunks")
        print("🎙️  Habla normalmente, el sistema grabará y transcribirá en pausas.")
        print("   (Presiona Ctrl+C para detener y guardar la sesión)")
        print("=" * 60)

        # --- 2. Service Initialization ---
        transcriber = RivaClientFactory.create_transcriber(riva_config)
        
        # VAD and Audio configurations
        audio_config = AudioConfig()

        # Parse CLI args to decide whether to run calibration or fixed-duration chunks
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--calibrate', action='store_true', help='Run microphone calibration interactively before starting')
        parser.add_argument('--chunk-duration', type=int, default=0, help='If >0, record fixed-duration chunks (seconds) instead of VAD')
        args, _ = parser.parse_known_args()

        if args.calibrate:
            # Calibrate microphone for VAD
            vad_config = calibrate_microphone(audio_config)
            # Update other VAD parameters if needed
            vad_config.silence_duration = 2.0
            vad_config.min_voice_duration = 0.4
        else:
            print("⚙️ Calibración omitida. Usando configuración VAD por defecto o guardada.")
            vad_config = VADConfig()
            # Try to load saved VAD config if present
            vad_file = project_root / '.vad_config.json'
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

            # Keep the tuned runtime silence and min voice durations
            vad_config.silence_duration = 2.0
            vad_config.min_voice_duration = 0.4
            print(f"   Umbral de voz: {vad_config.voice_threshold}, Umbral de silencio: {vad_config.silence_threshold}")

        all_transcripts = []
        segment_count = 0

        # Start background recording of the whole session (system/mix if device configured)
        try:
            bg_recorder = BackgroundRecorder(audio_config)
            bg_recorder.start()
            print("   🔴 Grabando sesión completa en background...")
        except Exception as e:
            print(f"   ⚠️ No se pudo iniciar grabación en background: {e}")
            bg_recorder = None

        # --- 3. Main Loop ---
        while True:
            segment_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] Segmento #{segment_count}: Esperando voz...")

            # If user requested fixed-duration chunks, use ContinuousRecorder
            if args.chunk_duration and args.chunk_duration > 0:
                print(f"   ⏱️  Grabando chunk fijo de {args.chunk_duration}s...")
                with ContinuousRecorder(audio_config) as recorder:
                    # stop_callback receives number of frames appended
                    def stop_cb(frames_count):
                        elapsed = frames_count * audio_config.chunk_size / audio_config.sample_rate
                        return elapsed >= args.chunk_duration

                    audio_data = recorder.record(stop_callback=stop_cb)
            else:
                # Record a chunk using VAD
                with VADRecorder(audio_config, vad_config) as recorder:
                    audio_data = recorder.record(
                        on_voice_detected=lambda: print("   🗣️  Voz detectada, grabando..."),
                    )

            if audio_data is None:
                print("   🔇 No se grabó audio válido, reintentando...")
                continue

            # Transcribe the recorded chunk
            print("   📝 Transcribiendo chunk...", end='', flush=True)
            transcript = transcriber.offline_transcribe(audio_data, language="es")
            print(" ✅")

            if transcript:
                print(f"   💬 {transcript}")
                all_transcripts.append((datetime.now(), transcript))
            else:
                print("   🔇 (Silencio o audio no reconocible)")

    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("🛑 Transcripción Detenida por el Usuario")
        print("=" * 60)
        if all_transcripts:
            print("\n💾 Guardando transcripción completa...")
            
            # Use Formatter and Writer to save the final file
            segmented_formatter = FormatterFactory.create('segmented_markdown')
            writer = OutputWriter()
            service = TranscriptionService(transcriber, segmented_formatter, writer)

            output_path = service.transcribe_segments(
                all_transcripts, 
                method="VAD (Real-time simulation)"
            )
            
            print(f"✅ Transcripción guardada en: {output_path}")
        else:
            print("⚠️ No hay transcripciones para guardar.")

        # Stop background recorder (if started) and save whole-session WAV
        try:
            if bg_recorder:
                tmp_path = project_root / f"realtime_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                bg_recorder.stop_and_save(str(tmp_path))
                print(f"✅ Grabación de sesión guardada en: {tmp_path}")

                # Use the same TranscriptionService flow as file.py to transcribe the full recording
                try:
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

    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ Error de Configuración: {e}")
        print("   Asegúrate de que tu archivo .env existe y es correcto.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error Inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
