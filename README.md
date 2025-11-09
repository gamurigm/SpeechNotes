# SpeechNotes - Sistema de Transcripción Automática# Sistema de Transcripción Automática de Audio a Markdown



Sistema modular de transcripción de audio a texto usando NVIDIA Riva (Whisper Large v3), diseñado con principios SOLID para máxima mantenibilidad y extensibilidad.Este proyecto automatiza la transcripción de archivos de audio a texto utilizando la API de NVIDIA Riva (con el modelo Whisper Large v3) y guarda los resultados en un archivo Markdown (`.md`) limpio y bien estructurado.



## 🏗️ Arquitectura## Características Principales



El proyecto sigue una arquitectura modular con separación de responsabilidades:- **Automatización Completa:** Convierte audio a una nota en Markdown con un solo comando.

- **Carga Automática de Credenciales:** Lee las claves de API y la configuración del servidor desde un archivo `.env` para no tener que exportar variables de entorno manualmente.

```- **Corrección de Codificación:** Soluciona problemas de visualización de tildes y caracteres especiales en Windows guardando los archivos con codificación `utf-8-sig`.

src/- **Metadatos Automáticos:** El archivo Markdown generado incluye información útil como la fecha, el nombre del archivo de audio, el idioma y la duración.

├── core/           # Configuración y cliente Riva (SRP, DIP)- **Fácil de Usar:** Abstrae la complejidad del cliente de Riva en un único script amigable.

├── audio/          # Captura de audio y VAD (SRP, OCP)

├── transcription/  # Servicio y formateo de salida (Facade, Strategy)---

└── cli/            # Interfaces de línea de comandos

## Requisitos Previos

scripts/            # Scripts de infraestructura (Riva, Docker)

config/             # Configuración y ejemplos1.  **Python 3.x:** Asegúrate de tener Python instalado.

legacy/             # Scripts monolíticos antiguos (deprecados)2.  **Dependencias de Python:** Instala las librerías necesarias que se encuentran en `python-clients/requirements.txt`.

python-clients/     # SDK de Riva    ```powershell

```    pip install -r ./python-clients/requirements.txt

    ```

### Principios SOLID Aplicados3.  **Credenciales de NVIDIA Riva:** Debes tener acceso a la API de Riva, lo que incluye:

    *   Una API Key.

- **SRP (Single Responsibility)**: Cada clase tiene una única razón para cambiar    *   La URL del servidor de Riva.

  - `ConfigManager`: Solo gestiona configuración    *   El ID de la función de Whisper.

  - `RivaTranscriber`: Solo interactúa con API Riva

  - `VADRecorder`: Solo graba con detección de voz---

  

- **OCP (Open/Closed)**: Extensible sin modificar código existente## ⚙️ Configuración

  - `AudioRecorder`: Clase base abstracta para diferentes estrategias de grabación

  - `OutputFormatter`: Múltiples formatos sin cambiar lógica coreAntes de ejecutar el script por primera vez, debes configurar tus credenciales.



- **DIP (Dependency Inversion)**: Depende de abstracciones1.  **Crea un archivo `.env`** en la raíz del proyecto.

  - `TranscriptionService` usa `Protocol` para transcriber2.  **Añade tus credenciales** al archivo con el siguiente formato:

  - Inyección de dependencias en constructores

    ```env

- **Factory Pattern**: Creación centralizada de objetos    # Credenciales de NVIDIA Riva

  - `RivaClientFactory`, `FormatterFactory`    API_KEY="AQUÍ_VA_TU_API_KEY"

    RIVA_SERVER="AQUÍ_VA_LA_URL_DEL_SERVIDOR"

- **Facade Pattern**: Interfaz simplificada    RIVA_FUNCTION_ID_WHISPER="AQUÍ_VA_EL_ID_DE_LA_FUNCIÓN_WHISPER"

  - `TranscriptionService` orquesta componentes complejos    ```



## 🚀 Inicio Rápido    Reemplaza los valores de ejemplo con tus credenciales reales. El script cargará estas variables automáticamente cada vez que se ejecute.



### 1. Instalación---



```powershell## 🚀 Cómo Ejecutar el Sistema

# Clonar repositorio

git clone https://github.com/gamurigm/SpeechNotes.gitUna vez configurado, puedes transcribir un archivo de audio con el siguiente comando en tu terminal (PowerShell o CMD):

cd SpeechNotes

```powershell

# Crear entorno virtualpython transcribe_to_markdown.py <ruta_del_audio> [idioma]

python -m venv .venv```

.venv\Scripts\activate

-   `<ruta_del_audio>`: La ruta al archivo de audio que quieres transcribir (ej: `audio/mi_audio.wav`).

# Instalar dependencias-   `[idioma]`: (Opcional) El código del idioma del audio. Por defecto es `es` (español).

pip install -r python-clients/requirements.txt

```**Ejemplo:**



### 2. Configuración```powershell

# Transcribir un archivo en español

```powershellpython transcribe_to_markdown.py audio/mi_audio.wav es

# Copiar plantilla de configuración

copy config\.env.example .env# Transcribir un archivo en inglés

python transcribe_to_markdown.py audio/reunion_ingles.wav en

# Editar .env con tus credenciales de NVIDIA Riva```

notepad .env

```El resultado se guardará como un nuevo archivo `.md` dentro de la carpeta `notas/`.



### 3. Uso### 🔴 Transcripción en Tiempo Real (Streaming) desde el Micrófono



#### Transcripción en Tiempo RealEste proyecto también incluye un script para transcribir audio directamente desde tu micrófono en tiempo real.

```powershell

python src/cli/realtime.py```powershell

```python transcribe_mic_to_markdown.py [duracion] [idioma] [archivo_salida]

Transcribe tu micrófono en tiempo real con resultados instantáneos.```



#### Grabación Continua-   `[duracion]`: (Opcional) Segundos que durará la grabación. Por defecto es `10`.

```powershell-   `[idioma]`: (Opcional) Código del idioma. Por defecto es `es`.

python src/cli/continuous.py-   `[archivo_salida]`: (Opcional) Ruta del archivo Markdown de salida. Por defecto se genera un nombre automático en `notas/`.

```

Graba todo, presiona Ctrl+C para detener y transcribir.**Ejemplo:**



#### Transcribir Archivo```powershell

```powershell# Grabar y transcribir durante 30 segundos en español

python src/cli/file.py audio/grabacion.wav espython transcribe_mic_to_markdown.py 30 es

``````

Transcribe cualquier archivo de audio existente.---



#### Calibrar Micrófono## 🛠️ ¿Cómo Funciona?

```powershell

python src/cli/calibrate.pyEl flujo de trabajo se divide en los siguientes pasos:

```

Obtén umbrales óptimos de VAD para tu micrófono.1.  **Inicio y Carga de Entorno:** El script `transcribe_to_markdown.py` se inicia y lee automáticamente el archivo `.env` para cargar las credenciales.

2.  **Llamada a la API:** Prepara y ejecuta una llamada al script `python-clients/scripts/asr/transcribe_file_offline.py`, pasándole las credenciales, el idioma y el archivo de audio.

## 📁 Estructura Detallada3.  **Procesamiento de la Respuesta:** Captura la salida del transcriptor de Riva, que viene en formato JSON, y extrae el texto completo.

4.  **Generación de Markdown:** Crea el contenido del archivo `.md`, añadiendo un encabezado, metadatos (fecha, duración, etc.) y la transcripción completa.

### `src/core/`5.  **Guardado con Codificación Correcta:** Guarda el archivo en la carpeta `notas/` usando la codificación `utf-8-sig` para asegurar que todos los caracteres especiales se muestren correctamente en cualquier editor de texto.

- **config.py**: Gestión centralizada de configuración
- **riva_client.py**: Cliente abstracto y implementación Riva

### `src/audio/`
- **capture.py**: 
  - `MicrophoneStream`: Stream continuo para tiempo real
  - `ContinuousRecorder`: Grabación hasta interrupción
  - `VADRecorder`: Grabación activada por voz
  - `MicrophoneCalibrator`: Calibración automática

### `src/transcription/`
- **service.py**: Orquestación de flujo de transcripción
- **formatters.py**: 
  - `MarkdownFormatter`: Salida en Markdown
  - `SegmentedMarkdownFormatter`: Con timestamps
  - `PlainTextFormatter`: Texto plano

### `src/cli/`
CLIs independientes que componen los módulos core.

## 🧪 Extensibilidad

### Agregar Nuevo Formato de Salida

```python
from src.transcription import OutputFormatter

class JSONFormatter(OutputFormatter):
    def format(self, transcript: str, metadata: dict) -> str:
        import json
        return json.dumps({"text": transcript, "meta": metadata})
    
    def get_file_extension(self) -> str:
        return ".json"

# Registrar en FormatterFactory
FormatterFactory._formatters['json'] = JSONFormatter
```

### Agregar Nueva Fuente de Audio

```python
from src.audio import AudioRecorder

class FileAudioRecorder(AudioRecorder):
    def __init__(self, file_path, config=None):
        super().__init__(config)
        self.file_path = file_path
    
    def record(self) -> bytes:
        with open(self.file_path, 'rb') as f:
            return f.read()
```

## 🔧 Migración desde Scripts Legacy

Los scripts monolíticos antiguos están en `legacy/` para referencia. Para migrar:

```python
# Antes (legacy/transcribe_realtime.py)
load_env()
auth = Auth(...)
asr_service = ASRService(auth)
# ... código mezclado ...

# Ahora (src/cli/realtime.py)
config = ConfigManager().get_riva_config()
transcriber = RivaClientFactory.create_transcriber(config)
# Componentes desacoplados y testeables
```

## 📊 Comparación: Antes vs Después

| Aspecto | Legacy | Modular |
|---------|--------|---------|
| **Archivos Python** | 5 monolíticos | 12 especializados |
| **Duplicación** | `load_env()` x5 | 1 `ConfigManager` |
| **Testabilidad** | Imposible | Inyección dependencias |
| **Extensión** | Copiar/pegar | Herencia/composición |
| **Acoplamiento** | Alto (Riva hardcoded) | Bajo (abstracciones) |

## 🛠️ Desarrollo

### Ejecutar Tests (futuro)
```powershell
pytest tests/
```

### Estructura para Tests
```
tests/
├── unit/
│   ├── test_config.py
│   ├── test_transcriber.py
│   └── test_formatters.py
└── integration/
    └── test_end_to_end.py
```

## 📝 Licencia

Este proyecto utiliza NVIDIA Riva SDK. Ver `python-clients/LICENSE`.

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/NuevaCaracteristica`)
3. Commit cambios (`git commit -m 'Agrega nueva característica'`)
4. Push al branch (`git push origin feature/NuevaCaracteristica`)
5. Abre Pull Request

---

**Versión:** 2.0.0 (Refactorización SOLID)  
**Autor:** gamurigm  
**Última actualización:** Noviembre 2025
