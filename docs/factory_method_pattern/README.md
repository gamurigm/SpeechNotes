# Factory Method Pattern - SpeechNotes

## 📋 Resumen

El **Factory Method Pattern** está implementado en el proyecto SpeechNotes para crear diferentes tipos de grabadores de audio (`AudioRecorder`) sin acoplar el código cliente a las clases concretas.

## 🎯 Propósito del Patrón

**Definir una interfaz para crear un objeto, pero dejar que las subclases decidan qué clase instanciar.**

### Problema que Resuelve
El sistema necesita crear diferentes tipos de grabadores (micrófono continuo, VAD, grabación continua, background) según el contexto, pero no queremos que el código cliente dependa directamente de las clases concretas.

### Solución
Usar factories que encapsulan la lógica de creación, permitiendo al cliente solicitar un tipo de grabador sin conocer los detalles de implementación.

---

## 📁 Ubicación de la Implementación

### Archivo Principal
**`src/audio/factory.py`**

Este archivo contiene:
- `RecorderFactory` (clase abstracta)
- `MicrophoneStreamRecorderFactory`
- `VADRecorderFactory`
- `ContinuousRecorderFactory`
- `BackgroundRecorderFactory`
- `AudioRecorderFactoryProvider` (provider centralizado)

### Archivos Relacionados
- `src/audio/capture.py` - Clases de productos (AudioRecorder y subclases)
- `src/audio/__init__.py` - Exporta las factories
- `src/cli/realtime.py` - Usa el patrón (3 puntos de uso)

---

## 🏗️ Estructura del Patrón

### Jerarquía de Creators (Factories)

```
RecorderFactory (Abstract)
├── MicrophoneStreamRecorderFactory
├── VADRecorderFactory
├── ContinuousRecorderFactory
└── BackgroundRecorderFactory
```

### Jerarquía de Products (Recorders)

```
AudioRecorder (Abstract)
├── MicrophoneStream
├── VADRecorder
├── ContinuousRecorder
└── BackgroundRecorder
```

---

## 📊 Diagrama UML

![Factory Method Pattern - UML Diagram](../assets/screenshots/factory_method_uml.png)

### Componentes del Diagrama

#### Creator (Factory)
- **RecorderFactory**: Clase abstracta que define el método `create_recorder()`
- **Concrete Factories**: Implementan `create_recorder()` para crear productos específicos

#### Product
- **AudioRecorder**: Clase abstracta que define la interfaz común
- **Concrete Products**: Implementaciones específicas de grabadores

#### Relaciones
- **Herencia**: Las factories concretas heredan de `RecorderFactory`
- **Herencia**: Los productos concretos heredan de `AudioRecorder`
- **Dependencia**: Cada factory crea su producto correspondiente

---

## 💻 Implementación en Código

### 1. Factory Abstracta

```python
class RecorderFactory(ABC):
    """Abstract factory for creating audio recorders"""
    
    @abstractmethod
    def create_recorder(self, config: Optional[AudioConfig] = None) -> AudioRecorder:
        """Create a recorder instance"""
        pass
```

### 2. Factories Concretas

```python
class MicrophoneStreamRecorderFactory(RecorderFactory):
    def create_recorder(self, config: Optional[AudioConfig] = None) -> MicrophoneStream:
        return MicrophoneStream(config or AudioConfig())

class VADRecorderFactory(RecorderFactory):
    def create_recorder(
        self,
        config: Optional[AudioConfig] = None,
        vad_config: Optional[VADConfig] = None
    ) -> VADRecorder:
        return VADRecorder(config or AudioConfig(), vad_config or VADConfig())

class ContinuousRecorderFactory(RecorderFactory):
    def create_recorder(self, config: Optional[AudioConfig] = None) -> ContinuousRecorder:
        return ContinuousRecorder(config or AudioConfig())

class BackgroundRecorderFactory(RecorderFactory):
    def create_recorder(self, config: Optional[AudioConfig] = None) -> BackgroundRecorder:
        return BackgroundRecorder(config or AudioConfig())
```

### 3. Provider Centralizado

```python
class AudioRecorderFactoryProvider:
    """Provider that returns the appropriate factory based on recorder type"""
    
    _factories = {
        RecorderType.MICROPHONE_STREAM: MicrophoneStreamRecorderFactory(),
        RecorderType.VAD: VADRecorderFactory(),
        RecorderType.CONTINUOUS: ContinuousRecorderFactory(),
        RecorderType.BACKGROUND: BackgroundRecorderFactory(),
    }
    
    @classmethod
    def create_recorder(
        cls,
        recorder_type: RecorderType,
        config: Optional[AudioConfig] = None,
        vad_config: Optional[VADConfig] = None
    ) -> AudioRecorder:
        """Create a recorder of the specified type"""
        factory = cls.get_factory(recorder_type)
        
        if isinstance(factory, VADRecorderFactory):
            return factory.create_recorder(config, vad_config)
        else:
            return factory.create_recorder(config)
```

---

## 🔧 Uso del Patrón

### Antes (Sin Factory Method)

```python
from src.audio import VADRecorder, ContinuousRecorder, BackgroundRecorder

# Cliente acoplado a clases concretas
bg_recorder = BackgroundRecorder(audio_config)
recorder = ContinuousRecorder(audio_config)
recorder = VADRecorder(audio_config, vad_config)
```

### Después (Con Factory Method)

```python
from src.audio import RecorderType, AudioRecorderFactoryProvider

# ✨ Factory Method Pattern - Cliente desacoplado
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

## 📍 Puntos de Uso en el Proyecto

### `src/cli/realtime.py`

El patrón se usa en **3 lugares** marcados con comentarios ✨:

1. **Línea ~117**: Creación de `BackgroundRecorder`
2. **Línea ~136**: Creación de `ContinuousRecorder`
3. **Línea ~149**: Creación de `VADRecorder`

---

## ✅ Ventajas del Patrón

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Acoplamiento** | Fuerte (5 clases importadas) | Débil (1 factory) |
| **Cambiar tipo** | Buscar/reemplazar múltiples lugares | Cambiar `RecorderType` |
| **Agregar nuevo tipo** | Modificar `realtime.py` | Solo modificar `factory.py` |
| **Testing** | Difícil mockear | Fácil mockear factory |
| **Mantenibilidad** | Baja | Alta |

---

## 🎨 Principios SOLID Aplicados

### ✅ Single Responsibility Principle (SRP)
Cada factory tiene una única responsabilidad: crear un tipo específico de recorder.

### ✅ Open/Closed Principle (OCP)
Abierto para extensión (agregar nuevas factories), cerrado para modificación (no cambiar código existente).

### ✅ Liskov Substitution Principle (LSP)
Todos los recorders son intercambiables ya que implementan la misma interfaz `AudioRecorder`.

### ✅ Interface Segregation Principle (ISP)
`RecorderFactory` es una interfaz limpia con un solo método abstracto.

### ✅ Dependency Inversion Principle (DIP)
El cliente depende de abstracciones (`RecorderType`, `RecorderFactory`) no de implementaciones concretas.

---

## 🔄 Extensibilidad

### Agregar un Nuevo Tipo de Recorder

Para agregar, por ejemplo, un `CloudRecorder`:

1. **En `capture.py`**: Crear `class CloudRecorder(AudioRecorder)`
2. **En `factory.py`**: Crear `class CloudRecorderFactory(RecorderFactory)`
3. **En `factory.py`**: Agregar `RecorderType.CLOUD = "cloud"`
4. **En `factory.py`**: Registrar en `_factories`

**Resultado**: `realtime.py` NO necesita modificarse ✨

---

## 🧪 Testing

### Ejecutar Tests

```bash
python test_factory_method.py
```

**Tests incluidos (7/7 pasando):**
- ✅ Factory crea el tipo correcto
- ✅ Factories individuales funcionan
- ✅ Configuración se propaga correctamente
- ✅ VAD config se propaga correctamente
- ✅ Tipos inválidos se detectan
- ✅ Todos heredan de AudioRecorder

---

## 📚 Ejemplos de Uso

### Ver Ejemplos Ejecutables

```bash
python examples_factory_method.py
```

**6 ejemplos incluidos:**
1. Microphone Stream Recorder
2. VAD Recorder
3. Continuous Recorder
4. Background Recorder
5. Usar Factories Directamente
6. Cambiar entre tipos dinámicamente

---

## 🔍 Diferencia con Abstract Factory

| Factory Method | Abstract Factory |
|----------------|------------------|
| Crea **un** producto | Crea **familias** de productos |
| Una jerarquía de factories | Múltiples productos relacionados |
| `RecorderFactory` | `TranscriptionEnvironmentFactory` |
| Ejemplo: Crear un recorder | Ejemplo: Crear transcriber + recorder + formatter |

---

## 📖 Referencias

- **Código fuente**: `src/audio/factory.py`
- **Tests**: `test_factory_method.py`
- **Ejemplos**: `examples_factory_method.py`
- **Documentación general**: `docs/design_patterns.md`

---

## 📊 Estado de Implementación

✅ Pattern implementado en `src/audio/factory.py`  
✅ Refactorizado en `src/cli/realtime.py` (3 puntos)  
✅ Tests creados y pasando (7/7)  
✅ Ejemplos funcionales ejecutables  
✅ SOLID principles aplicados  
✅ Desacoplamiento logrado  
✅ Extensibilidad lograda  

**El Factory Method Pattern está COMPLETAMENTE FUNCIONAL en SpeechNotes.**
