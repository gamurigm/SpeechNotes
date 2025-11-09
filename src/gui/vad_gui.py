#!/usr/bin/env python3
"""Small minimal GUI to tweak VAD thresholds and save them for realtime use.

Usage: python -m src.gui.vad_gui
"""
import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

# Project root is two levels up from this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
VAD_FILE = PROJECT_ROOT / '.vad_config.json'

DEFAULTS = {
    'voice_threshold': 300,
    'silence_threshold': 150,
}


def load_values():
    if VAD_FILE.exists():
        try:
            data = json.loads(VAD_FILE.read_text())
            return {
                'voice_threshold': int(data.get('voice_threshold', DEFAULTS['voice_threshold'])),
                'silence_threshold': int(data.get('silence_threshold', DEFAULTS['silence_threshold']))
            }
        except Exception:
            return DEFAULTS.copy()
    return DEFAULTS.copy()


def save_values(voice_val, silence_val):
    payload = {
        'voice_threshold': int(voice_val),
        'silence_threshold': int(silence_val)
    }
    VAD_FILE.write_text(json.dumps(payload, indent=2))


def run_gui():
    vals = load_values()

    root = tk.Tk()
    root.title('VAD Thresholds — Minimal')
    root.geometry('360x200')
    root.resizable(False, False)

    tk.Label(root, text='Voice Threshold').pack(anchor='w', padx=12, pady=(12,0))
    voice_scale = tk.Scale(root, from_=0, to=10000, orient='horizontal')
    voice_scale.set(vals['voice_threshold'])
    voice_scale.pack(fill='x', padx=12)

    tk.Label(root, text='Silence Threshold').pack(anchor='w', padx=12, pady=(8,0))
    silence_scale = tk.Scale(root, from_=0, to=10000, orient='horizontal')
    silence_scale.set(vals['silence_threshold'])
    silence_scale.pack(fill='x', padx=12)

    def on_save():
        v = voice_scale.get()
        s = silence_scale.get()
        if v <= s:
            if not messagebox.askyesno('Confirmar', 'El umbral de voz es menor o igual al de silencio. Guardar de todos modos?'):
                return
        save_values(v, s)
        messagebox.showinfo('Guardado', f'Umbrales guardados:\nvoice={v}\nsilence={s}\nArchivo: {VAD_FILE}')

    btn = tk.Button(root, text='Guardar', command=on_save)
    btn.pack(pady=12)

    root.mainloop()


if __name__ == '__main__':
    run_gui()
