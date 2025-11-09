#!/usr/bin/env python3
"""
Microphone calibration CLI
Calibrates microphone for optimal VAD thresholds
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import AudioConfig, MicrophoneCalibrator


def main():
    print("🎤 Calibración del Micrófono")
    print("=" * 60)
    print()
    print("Instrucciones:")
    print("1. Primero: NO HABLES durante 5 segundos (detectar ruido)")
    print("2. Después: HABLA NORMAL durante 5 segundos")
    print()
    input("Presiona ENTER para empezar...")
    print()
    
    try:
        audio_config = AudioConfig()
        calibrator = MicrophoneCalibrator(audio_config)
        
        print("🔇 Fase 1: SILENCIO TOTAL (5 segundos)...")
        print("🗣️  Fase 2: HABLA NORMAL (5 segundos)...")
        print()
        
        vad_config = calibrator.calibrate(duration=5)
        
        print("=" * 60)
        print("✅ VALORES RECOMENDADOS:")
        print("=" * 60)
        print(f"   voice_threshold    = {vad_config.voice_threshold}")
        print(f"   silence_threshold  = {vad_config.silence_threshold}")
        print()
        print("Usa estos valores al crear VADConfig en tus scripts")
        print()
    
    except KeyboardInterrupt:
        print("\n\n❌ Calibración cancelada")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
