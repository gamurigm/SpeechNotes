# Sistema de Transcripción Automática de Audio a Markdown



Sistema modular de transcripción de audio a texto usando NVIDIA Riva (Whisper Large v3), diseñado con principios SOLID para máxima mantenibilidad y extensibilidad.Este proyecto automatiza la transcripción de archivos de audio a texto utilizando la API de NVIDIA Riva (con el modelo Whisper Large v3) y guarda los resultados en un archivo Markdown (`.md`) limpio y bien estructurado.



## 🏗️ Arquitectura - Características Principales



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

# SpeechNotes — Transcribe audio a Markdown ✨🎧

Un pequeño toolkit para convertir audio (archivos o micrófono) en notas Markdown legibles y con metadatos.

Principio: fácil de usar, configurable y pensado para trabajar en entornos con ruido.

---

## 🚀 Inicio rápido (3 pasos)

1) Crear entorno e instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r python-clients/requirements.txt
```

2) Configurar credenciales (NVIDIA Riva):

```powershell
copy config\.env.example .env
notepad .env
# Rellena API_KEY, RIVA_SERVER y RIVA_FUNCTION_ID_WHISPER
```

3) Transcribir (archivo o micrófono):

```powershell
# Archivo de audio
python src/cli/file.py audio/mi_audio.wav es

# Tiempo real (VAD)
python src/cli/realtime.py

# Tiempo real: grabar chunks fijos (ej. 30 s)
python src/cli/realtime.py --chunk-duration 30

# Calibración interactiva (opcional)
python src/cli/realtime.py --calibrate
```

---

## 🎛️ Ajustes rápidos

- Edita umbrales VAD con la GUI mínima (Tkinter):

```powershell
python -m src.gui.vad_gui
```

La GUI guarda en `.vad_config.json` en la raíz (está en `.gitignore`).

---

## � Qué genera

- Archivos Markdown en `notas/` con encabezado + metadatos (fecha, duración, idioma).
- Codificación: `utf-8-sig` para compatibilidad con Windows.

---

## 🛠️ Notas técnicas (breve)

- VAD: el sistema usa `voice_threshold` y `silence_threshold` para cortar segmentos.
- Si las transcripciones salen fragmentadas, usa `--chunk-duration` para obtener fragmentos más largos.
- `python-clients/` contiene el cliente Riva y los protobufs. Si no están los archivos `.proto` en `python-clients/common/`, ejecuta:

```powershell
cd python-clients
git submodule update --init --remote --recursive
pip install -r requirements.txt
pip install .
```


