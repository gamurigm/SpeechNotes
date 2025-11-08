#!/usr/bin/env python3
"""Simple script to verify WAV file specs."""
import wave
import sys

wav_path = r'.\audio\mi_audio.wav'

try:
    with wave.open(wav_path, 'rb') as w:
        print('Channels:', w.getnchannels())
        print('Rate:', w.getframerate(), 'Hz')
        print('Sample width:', w.getsampwidth(), 'bytes')
        print('Frames:', w.getnframes())
        duration = w.getnframes() / w.getframerate()
        print(f'Duration: {duration:.2f} seconds')
except FileNotFoundError:
    print(f'ERROR: File not found: {wav_path}')
    sys.exit(1)
except wave.Error as e:
    print(f'ERROR: Not a valid WAV file: {e}')
    sys.exit(1)
