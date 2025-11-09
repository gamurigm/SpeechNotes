# SpeechNotes - Sistema de Transcripción Automática# Sistema de Transcripción Automática de Audio a Markdown



Sistema modular de transcripción de audio a texto usando NVIDIA Riva (Whisper Large v3), diseñado con principios SOLID para máxima mantenibilidad y extensibilidad.Este proyecto automatiza la transcripción de archivos de audio a texto utilizando la API de NVIDIA Riva (con el modelo Whisper Large v3) y guarda los resultados en un archivo Markdown (`.md`) limpio y bien estructurado.



## 🏗️ Arquitectura## Características Principales



El proyecto sigue una arquitectura modular con separación de responsabilidades:- **Automatización Completa:** Convierte audio a una nota en Markdown con un solo comando.

- **Carga Automática de Credenciales:** Lee las claves de API y la configuración del servidor desde un archivo `.env` para no tener que exportar variables de entorno manualmente.

```- **Corrección de Codificación:** Soluciona problemas de visualización de tildes y caracteres especiales en Windows guardando los archivos con codificación `utf-8-sig`.

src/- **Metadatos Automáticos:** El archivo Markdown generado incluye información útil como la fecha, el nombre del archivo de audio, el idioma y la duración.

├── core/           # Configuración y cliente Riva (SRP, DIP)- **Fácil de Usar:** Abstrae la complejidad del cliente de Riva en un único script amigable.
# SpeechNotes — Transcribe audio a Markdown ✍️🎧

Ligero, modular y listo para transcribir: convierte audio (archivos o micrófono) a notas en Markdown.

## ✅ Qué hace (en una línea)
Transcribe audio usando el cliente Riva (Whisper) y genera `.md` limpias con metadatos (fecha, duración, idioma).

## 🚀 Rápido — cómo arrancar
1. Crea un entorno y instala dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r python-clients/requirements.txt
```

2. Copia el ejemplo de configuración y edita `.env` con tus credenciales de Riva:

```powershell
copy config\.env.example .env
notepad .env
```

3. Transcribir un archivo de audio:

```powershell
python src/cli/file.py <ruta_audio> [idioma]
# ejemplo
python src/cli/file.py audio/mi_audio.wav es
```

4. Transcripción en “tiempo real” desde el micrófono (VAD o chunks fijos):

```powershell
# VAD (usa umbrales guardados o por defecto)
python src/cli/realtime.py

# Grabar y transcribir cada 30 segundos (sin VAD)
python src/cli/realtime.py --chunk-duration 30

# Ejecutar calibración interactiva antes de arrancar
python src/cli/realtime.py --calibrate
```

5. Ajustar umbrales fácilmente (GUI mínima):

```powershell
python -m src.gui.vad_gui
```
Guarda en `.vad_config.json` (se ignora en Git).

## 🧩 Notas técnicas esenciales
- VAD: `voice_threshold` / `silence_threshold` (se pueden calibrar o editar con la GUI).
- Grabación por chunks: `--chunk-duration N` graba fragmentos fijos de N segundos.
- Salida: archivos `.md` en la carpeta `notas/` (codificación utf-8-sig).

## 🔒 Seguridad
- No subas tu `.env` ni las notas. `.gitignore` ya incluye `notas/` y `.vad_config.json`.

## 🛠️ Estructura (rápida)
- `src/core/` — configuración y cliente Riva
- `src/audio/` — captura, VAD y calibración
- `src/transcription/` — formateo y servicios
- `src/cli/` — scripts de uso: `file.py`, `realtime.py`, etc.
- `src/gui/` — GUI mínima para thresholds

## � Siguientes pasos sugeridos
- Ajusta thresholds con la GUI si tienes ruido de fondo.
- Usa `--chunk-duration 30` si quieres transcripciones largas (ej. reuniones).

¿Quieres que añada una sección de ejemplos o un badge con instrucciones rápidas al principio? ✨

---
_Versión ligera del README — creada para ser clara y útil. Última actualización: Nov 2025_

