# Diagrama: Abstract Factory Pattern Implementation

## 🏗️ Diagrama UML Conceptual

```
┌─────────────────────────────────────────────────────────────────────┐
│          TranscriptionEnvironmentFactory (Abstract)                 │
├─────────────────────────────────────────────────────────────────────┤
│ + create_transcriber(): Transcriber                                 │
│ + create_recorder(type): AudioRecorder                              │
│ + create_formatter(): OutputFormatter                               │
│ + get_name(): str                                                   │
└─────────────────────────────────────────────────────────────────────┘
                          △              △
                          │              │
                          │              │
        ┌─────────────────┘              └──────────────────────┐
        │                                                       │
┌───────────────────────────┐                    ┌──────────────────────────┐
│      RivaLiveFactory      │                    │   LocalBatchFactory      │
├───────────────────────────┤                    ├──────────────────────────┤
│ - config_manager          │                    │ - (future)               │
│ - _transcriber            │                    │                          │
├───────────────────────────┤                    ├──────────────────────────┤
│ + create_transcriber()    │ ─────┐             │ + create_transcriber()   │
│   → RivaTranscriber       │      │             │   → NotImplementedError  │
│ + create_recorder()       │ ─────┼─┐           │ + create_recorder()      │
│   → VAD/Continuous/BG    │      │ │           │   → VAD/Continuous/BG   │
│ + create_formatter()      │ ─────┼─┼─┐         │ + create_formatter()     │
│   → Segmented Markdown    │      │ │ │         │   → Markdown             │
│ + get_name(): "Riva Live" │      │ │ │         │ + get_name(): "Local BG" │
└───────────────────────────┘      │ │ │         └──────────────────────────┘
                                   │ │ │
                    ┌──────────────┘ │ │
                    │                │ │
                    ▼                ▼ ▼
            ┌─────────────────┐  ┌──────────────────┐
            │ RivaTranscriber │  │ AudioRecorders   │
            │ (cloud-based)   │  │ - VADRecorder    │
            └─────────────────┘  │ - Continuous     │
                                 │ - Background     │
                                 └──────────────────┘

            ┌──────────────────────────────────────┐
            │       OutputFormatter                │
            ├──────────────────────────────────────┤
            │ • SegmentedMarkdownFormatter          │
            │ • MarkdownFormatter                   │
            │ • PlainTextFormatter                  │
            └──────────────────────────────────────┘
```

## 🔗 Conexión con realtime.py

```
┌──────────────────────────────────────────────────────────────┐
│                      realtime.py                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  main()                                                      │
│    │                                                         │
│    ├─→ TranscriptionEnvironmentFactoryProvider.get_riva_live()
│    │   └─→ Returns: RivaLiveFactory instance                │
│    │                                                         │
│    ├─→ environment_factory.create_transcriber()             │
│    │   └─→ Returns: RivaTranscriber                         │
│    │                                                         │
│    ├─→ environment_factory.create_recorder(RecorderType.VAD)
│    │   └─→ Returns: VADRecorder                             │
│    │                                                         │
│    ├─→ environment_factory.create_formatter()               │
│    │   └─→ Returns: SegmentedMarkdownFormatter              │
│    │                                                         │
│    └─→ Flujo: Grabar → Transcribir → Formatear             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 📊 Ventajas del Patrón

```
ANTES (Sin Abstract Factory):
┌──────────────────────────────┐
│  Cliente (realtime.py)       │
├──────────────────────────────┤
│ Necesita:                    │
│ • ConfigManager              │
│ • RivaClientFactory          │
│ • AudioRecorderFactoryProvider
│ • FormatterFactory           │
│ • ManualComponentComposition │
└──────────────────────────────┘
     ↓ Alto acoplamiento
Difícil cambiar de ambiente

DESPUÉS (Con Abstract Factory):
┌──────────────────────────────┐
│  Cliente (realtime.py)       │
├──────────────────────────────┤
│ Solo necesita:               │
│ • TranscriptionEnvironment   │
│   FactoryProvider            │
│ • environment_factory.       │
│   create_*()                 │
└──────────────────────────────┘
     ↓ Bajo acoplamiento
Fácil cambiar de ambiente
```

## 🔄 Flujo de Ejecución en realtime.py

```
START
  │
  ├─ 1. Obtener ambiente
  │   TranscriptionEnvironmentFactoryProvider.get_riva_live()
  │   └─→ ✅ RivaLiveFactory (cached)
  │
  ├─ 2. Crear transcriber
  │   environment_factory.create_transcriber()
  │   └─→ ✅ RivaTranscriber (lazy init)
  │
  ├─ 3. Configurar VAD
  │   _setup_vad_config()
  │   └─→ ✅ VADConfig (guardada o por defecto)
  │
  ├─ 4. Iniciar grabación de background
  │   environment_factory.create_recorder(RecorderType.BACKGROUND)
  │   └─→ ✅ BackgroundRecorder
  │
  ├─ 5. Loop principal
  │   │
  │   ├─→ Crear recorder VAD
  │   │   environment_factory.create_recorder(RecorderType.VAD)
  │   │   └─→ ✅ VADRecorder
  │   │
  │   ├─→ Grabar audio (esperar voz detectada)
  │   │   recorder.record(on_voice_detected=callback)
  │   │   └─→ ✅ Audio bytes
  │   │
  │   ├─→ Transcribir
  │   │   transcriber.offline_transcribe(audio_data)
  │   │   └─→ ✅ Transcript string
  │   │
  │   └─→ Agregar a lista de transcripciones
  │       all_transcripts.append((timestamp, transcript))
  │
  ├─ 6. Al presionar Ctrl+C
  │   _save_transcription_results()
  │   │
  │   ├─→ Crear formatter
  │   │   environment_factory.create_formatter()
  │   │   └─→ ✅ SegmentedMarkdownFormatter
  │   │
  │   ├─→ Guardar transcripciones segmentadas
  │   │   service.transcribe_segments()
  │   │   └─→ ✅ .md file
  │   │
  │   ├─→ Detener grabación background
  │   │   bg_recorder.stop_and_save()
  │   │   └─→ ✅ .wav file
  │   │
  │   └─→ Transcribir grabación completa
  │       file_service.transcribe_audio_file()
  │       └─→ ✅ .md file
  │
  END
```

## 🎯 Extensibilidad: Agregar Nuevo Ambiente

```python
# 1. Crear nueva factory concreta
class CustomTranscriptionFactory(TranscriptionEnvironmentFactory):
    def create_transcriber(self):
        return CustomTranscriber()
    
    def create_recorder(self, type, **kwargs):
        return CustomRecorder(type, **kwargs)
    
    def create_formatter(self):
        return CustomFormatter()
    
    def get_name(self):
        return "Custom Environment"

# 2. Registrar en provider
class TranscriptionEnvironmentFactoryProvider:
    @classmethod
    def create_environment(cls, environment_type):
        if environment_type == EnvironmentType.CUSTOM:
            cls._factories[environment_type] = CustomTranscriptionFactory()
        # ... resto del código

# 3. Usar en la aplicación
factory = TranscriptionEnvironmentFactoryProvider.create_environment(
    EnvironmentType.CUSTOM
)
# ¡Listo! Sin cambios en realtime.py
```

---

## 📌 Conclusión

El **Abstract Factory Pattern** permite que `realtime.py` sea:
- ✅ **Flexible**: Cambiar de ambiente sin modificar código
- ✅ **Mantenible**: Separación clara de responsabilidades
- ✅ **Testeable**: Fácil crear mocks y stubs
- ✅ **Escalable**: Agregar nuevos ambientes sin afectar existentes
- ✅ **Confiable**: Garantiza compatibilidad de componentes
