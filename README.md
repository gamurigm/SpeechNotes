# Sistema de Transcripción Automática de Audio a Markdown

Este proyecto automatiza la transcripción de archivos de audio a texto utilizando la API de NVIDIA Riva (con el modelo Whisper Large v3) y guarda los resultados en un archivo Markdown (`.md`) limpio y bien estructurado.

## Características Principales

- **Automatización Completa:** Convierte audio a una nota en Markdown con un solo comando.
- **Carga Automática de Credenciales:** Lee las claves de API y la configuración del servidor desde un archivo `.env` para no tener que exportar variables de entorno manualmente.
- **Corrección de Codificación:** Soluciona problemas de visualización de tildes y caracteres especiales en Windows guardando los archivos con codificación `utf-8-sig`.
- **Metadatos Automáticos:** El archivo Markdown generado incluye información útil como la fecha, el nombre del archivo de audio, el idioma y la duración.
- **Fácil de Usar:** Abstrae la complejidad del cliente de Riva en un único script amigable.

---

## Requisitos Previos

1.  **Python 3.x:** Asegúrate de tener Python instalado.
2.  **Dependencias de Python:** Instala las librerías necesarias que se encuentran en `python-clients/requirements.txt`.
    ```powershell
    pip install -r ./python-clients/requirements.txt
    ```
3.  **Credenciales de NVIDIA Riva:** Debes tener acceso a la API de Riva, lo que incluye:
    *   Una API Key.
    *   La URL del servidor de Riva.
    *   El ID de la función de Whisper.

---

## ⚙️ Configuración

Antes de ejecutar el script por primera vez, debes configurar tus credenciales.

1.  **Crea un archivo `.env`** en la raíz del proyecto.
2.  **Añade tus credenciales** al archivo con el siguiente formato:

    ```env
    # Credenciales de NVIDIA Riva
    API_KEY="AQUÍ_VA_TU_API_KEY"
    RIVA_SERVER="AQUÍ_VA_LA_URL_DEL_SERVIDOR"
    RIVA_FUNCTION_ID_WHISPER="AQUÍ_VA_EL_ID_DE_LA_FUNCIÓN_WHISPER"
    ```

    Reemplaza los valores de ejemplo con tus credenciales reales. El script cargará estas variables automáticamente cada vez que se ejecute.

---

## 🚀 Cómo Ejecutar el Sistema

Una vez configurado, puedes transcribir un archivo de audio con el siguiente comando en tu terminal (PowerShell o CMD):

```powershell
python transcribe_to_markdown.py <ruta_del_audio> [idioma]
```

-   `<ruta_del_audio>`: La ruta al archivo de audio que quieres transcribir (ej: `audio/mi_audio.wav`).
-   `[idioma]`: (Opcional) El código del idioma del audio. Por defecto es `es` (español).

**Ejemplo:**

```powershell
# Transcribir un archivo en español
python transcribe_to_markdown.py audio/mi_audio.wav es

# Transcribir un archivo en inglés
python transcribe_to_markdown.py audio/reunion_ingles.wav en
```

El resultado se guardará como un nuevo archivo `.md` dentro de la carpeta `notas/`.

### 🔴 Transcripción en Tiempo Real (Streaming) desde el Micrófono

Este proyecto también incluye un script para transcribir audio directamente desde tu micrófono en tiempo real.

```powershell
python transcribe_mic_to_markdown.py [duracion] [idioma] [archivo_salida]
```

-   `[duracion]`: (Opcional) Segundos que durará la grabación. Por defecto es `10`.
-   `[idioma]`: (Opcional) Código del idioma. Por defecto es `es`.
-   `[archivo_salida]`: (Opcional) Ruta del archivo Markdown de salida. Por defecto se genera un nombre automático en `notas/`.

**Ejemplo:**

```powershell
# Grabar y transcribir durante 30 segundos en español
python transcribe_mic_to_markdown.py 30 es
```
---

## 🛠️ ¿Cómo Funciona?

El flujo de trabajo se divide en los siguientes pasos:

1.  **Inicio y Carga de Entorno:** El script `transcribe_to_markdown.py` se inicia y lee automáticamente el archivo `.env` para cargar las credenciales.
2.  **Llamada a la API:** Prepara y ejecuta una llamada al script `python-clients/scripts/asr/transcribe_file_offline.py`, pasándole las credenciales, el idioma y el archivo de audio.
3.  **Procesamiento de la Respuesta:** Captura la salida del transcriptor de Riva, que viene en formato JSON, y extrae el texto completo.
4.  **Generación de Markdown:** Crea el contenido del archivo `.md`, añadiendo un encabezado, metadatos (fecha, duración, etc.) y la transcripción completa.
5.  **Guardado con Codificación Correcta:** Guarda el archivo en la carpeta `notas/` usando la codificación `utf-8-sig` para asegurar que todos los caracteres especiales se muestren correctamente en cualquier editor de texto.
