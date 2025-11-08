#!/usr/bin/env python3
"""
Script de calibración para detectar niveles de ruido y voz
"""

import pyaudio
import numpy as np
import time

def calibrate_microphone(duration=10):
    """
    Calibra el micrófono para detectar niveles de ruido y voz
    """
    audio = pyaudio.PyAudio()
    
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )
    
    print("🎤 Calibración del Micrófono")
    print("=" * 60)
    print()
    print("Instrucciones:")
    print("1. Primero: NO HABLES durante 5 segundos (detectar ruido)")
    print("2. Después: HABLA NORMAL durante 5 segundos")
    print()
    input("Presiona ENTER para empezar...")
    print()
    
    # Fase 1: Detectar ruido de fondo
    print("🔇 Fase 1: SILENCIO TOTAL (5 segundos)...")
    noise_levels = []
    
    for i in range(5):
        print(f"   {5-i}...", end=' ', flush=True)
        time.sleep(0.2)
        
        for _ in range(5):  # 5 muestras por segundo
            data = stream.read(1024)
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_data).mean()
            noise_levels.append(volume)
            time.sleep(0.2)
    
    print("\n")
    
    # Fase 2: Detectar voz
    print("🗣️  Fase 2: HABLA NORMAL (5 segundos)...")
    voice_levels = []
    
    for i in range(5):
        print(f"   {5-i}...", end=' ', flush=True)
        time.sleep(0.2)
        
        for _ in range(5):  # 5 muestras por segundo
            data = stream.read(1024)
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_data).mean()
            voice_levels.append(volume)
            time.sleep(0.2)
    
    print("\n")
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # Analizar resultados
    noise_avg = np.mean(noise_levels)
    noise_max = np.max(noise_levels)
    voice_avg = np.mean(voice_levels)
    voice_min = np.min(voice_levels)
    
    # Calcular umbrales recomendados
    # El umbral de voz debe estar entre el ruido máximo y la voz mínima
    recommended_voice_threshold = int(noise_max + (voice_min - noise_max) * 0.3)
    recommended_silence_threshold = int(noise_max * 1.5)
    
    print("=" * 60)
    print("📊 RESULTADOS DE CALIBRACIÓN")
    print("=" * 60)
    print()
    print(f"🔇 Ruido de fondo:")
    print(f"   - Promedio: {noise_avg:.0f}")
    print(f"   - Máximo:   {noise_max:.0f}")
    print()
    print(f"🗣️  Voz:")
    print(f"   - Promedio: {voice_avg:.0f}")
    print(f"   - Mínimo:   {voice_min:.0f}")
    print()
    print("=" * 60)
    print("✅ VALORES RECOMENDADOS:")
    print("=" * 60)
    print(f"   voice_threshold    = {recommended_voice_threshold}  (para detectar voz)")
    print(f"   silence_threshold  = {recommended_silence_threshold}  (para detectar silencio)")
    print()
    print("Copia estos valores en transcribe_realtime_chunks.py")
    print("en la función record_chunk_with_vad()")
    print()

if __name__ == "__main__":
    try:
        calibrate_microphone()
    except KeyboardInterrupt:
        print("\n\n❌ Calibración cancelada")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
