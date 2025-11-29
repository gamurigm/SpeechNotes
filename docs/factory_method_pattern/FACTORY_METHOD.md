# Factory Method Pattern - SpeechNotes

## Resumen rápido

Se implementó el **Factory Method Pattern** en `src/cli/realtime.py` usando `AudioRecorderFactoryProvider` para desacoplar la creación de grabadores de audio.

**3 puntos de uso en realtime.py** (marcados con ✨):
- Línea ~117: BackgroundRecorder
- Línea ~136: ContinuousRecorder  
- Línea ~149: VADRecorder

---

## ¿Qué es el patrón?

**Problema:** realtime.py necesita crear diferentes tipos de recorders (VAD, Continuous, Background) sin acoplarse a sus clases concretas.

**Solución:** Usar una factory que se encarga de la creación.

**Analógía:** 
- SIN pattern: Dices "necesito un VADRecorder" → Tienes que saber cómo crearlo
- CON pattern: Dices "necesito RecorderType.VAD" → La factory te lo crea sin que sepas qué clase es

---

## Implementación

### 1. Factory Pattern (src/audio/factory.py)

```python
RecorderFactory (Interfaz abstracta)
├── MicrophoneStreamRecorderFactory
├── VADRecorderFactory
├── ContinuousRecorderFactory
└── BackgroundRecorderFactory

AudioRecorderFactoryProvider (Provider centralizado)
└── Selecciona la factory correcta según RecorderType
```

### 2. Cambios en realtime.py

**ANTES:**
```python
from src.audio import VADRecorder, ContinuousRecorder, BackgroundRecorder

bg_recorder = BackgroundRecorder(audio_config)
recorder = ContinuousRecorder(audio_config)
recorder = VADRecorder(audio_config, vad_config)
```

**AHORA:**
```python
from src.audio import RecorderType, AudioRecorderFactoryProvider

# ✨ Factory Method Pattern
bg_recorder = AudioRecorderFactoryProvider.create_recorder(
    RecorderType.BACKGROUND, config=audio_config
)

recorder = AudioRecorderFactoryProvider.create_recorder(
    RecorderType.CONTINUOUS, config=audio_config
)

recorder = AudioRecorderFactoryProvider.create_recorder(
    RecorderType.VAD, config=audio_config, vad_config=vad_config
)
```

---

## Ventajas

| Antes | Después |
|-------|---------|
| Acoplamiento fuerte (5 clases) | Desacoplado (1 factory) |
| Cambiar tipo = buscar/reemplazar múltiples lugares | Cambiar tipo = cambiar RecorderType |
| Agregar nuevo tipo = modificar realtime.py | Agregar nuevo tipo = solo factory.py |
| Difícil de testear | Fácil mockear factory |

---

## Cómo usar

### Ver ejemplos
```bash
python examples_factory_method.py
```

### Correr tests
```bash
python test_factory_method.py
# Resultado: ✅ ALL TESTS PASSED (7/7)
```

### Ejecutar realtime.py
```bash
python src/cli/realtime.py
# Verás comentarios ✨ mostrando dónde se usa el patrón
```

---

## Archivos del proyecto

| Archivo | Tipo | Propósito |
|---------|------|----------|
| `src/audio/factory.py` | ✨ Nuevo | Factory Method Pattern |
| `src/audio/__init__.py` | ✏️ Modificado | Exporta factories |
| `src/cli/realtime.py` | ✏️ Modificado | Usa factory (comentarios ✨) |
| `examples_factory_method.py` | ✨ Nuevo | 6 ejemplos ejecutables |
| `test_factory_method.py` | ✨ Nuevo | Tests completos |

---

## Tipos de recorders disponibles

| Tipo | Clase | Uso |
|------|-------|-----|
| `RecorderType.MICROPHONE_STREAM` | `MicrophoneStream` | Streaming continuo |
| `RecorderType.VAD` | `VADRecorder` | Activación por voz |
| `RecorderType.CONTINUOUS` | `ContinuousRecorder` | Chunks de duración fija |
| `RecorderType.BACKGROUND` | `BackgroundRecorder` | Grabación en background |

---

## SOLID Principles

✅ **Single Responsibility:** Cada factory solo crea un tipo
✅ **Open/Closed:** Abierto para extensión, cerrado para modificación
✅ **Liskov Substitution:** Todos los recorders son compatibles
✅ **Interface Segregation:** RecorderFactory es interfaz limpia
✅ **Dependency Inversion:** Depende de abstracciones, no de concretos

---

## Ejemplo: Agregar nuevo tipo

Si quieres agregar `CloudRecorder`:

1. **capture.py:** Crear `class CloudRecorder(AudioRecorder)`
2. **factory.py:** Crear `class CloudRecorderFactory(RecorderFactory)`
3. **factory.py:** Agregar `RecorderType.CLOUD = "cloud"`
4. **factory.py:** Registrar en `_factories`

**Resultado:** realtime.py NO se modifica ✨

---

## Flujo de ejecución

```
realtime.py pide: RecorderType.VAD
        ↓
AudioRecorderFactoryProvider.create_recorder()
        ↓
Selecciona: VADRecorderFactory
        ↓
Crea: new VADRecorder()
        ↓
Devuelve a realtime.py
        ↓
realtime.py NUNCA sabe que usó VADRecorder
```

---

## Tests

```bash
python test_factory_method.py
```

**7 tests pasando:**
- Factory crea tipo correcto
- Factories individuales funcionan
- Configuración se propaga
- VAD config se propaga
- Tipos inválidos se detectan
- Todos heredan de AudioRecorder

---

## Documentación adicional

Véase también:
- `docs/design_patterns.md` - Documentación oficial del proyecto
- `DIAGRAMA_UML.md` - Diagrama UML del patrón
- Código comentado en `src/audio/factory.py`
- Ejemplos en `examples_factory_method.py`

---

## Conceptos clave

**Factory Method Pattern responde:**
> ¿Cómo creo objetos de diferentes tipos sin acoplar el cliente?

**Respuesta:** 
1. Define interfaz abstracta (`RecorderFactory`)
2. Implementa factories específicas para cada tipo
3. Cliente solo conoce tipos abstractos (`RecorderType`)
4. Factory se encarga de crear la instancia correcta

**Beneficio tangible:** 
Agregar nuevo tipo de recorder no requiere cambios en realtime.py. Solo trabajas en factory.py.

---

## Estado

✅ Pattern implementado en `src/audio/factory.py`
✅ Refactorizado en `src/cli/realtime.py` (3 puntos)
✅ Tests creados y pasando (7/7)
✅ Ejemplos funcionales ejecutables
✅ SOLID principles aplicados
✅ Desacoplamiento logrado
✅ Extensibilidad lograda
✅ Diagrama UML creado

**El Factory Method Pattern está COMPLETAMENTE FUNCIONAL en SpeechNotes.**
