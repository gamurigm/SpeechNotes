"""
Ejemplos de uso del Abstract Factory Pattern en SpeechNotes
Demuestra cómo utilizar TranscriptionEnvironmentFactory en diferentes escenarios
"""

from src.core.environment_factory import (
    TranscriptionEnvironmentFactoryProvider,
    EnvironmentType,
)
from src.audio import RecorderType, AudioConfig, VADConfig


# ============================================================================
# EJEMPLO 1: Usar Riva Live para transcripción en tiempo real (realtime.py)
# ============================================================================

def ejemplo_riva_live_basic():
    """Ejemplo básico: Obtener ambiente Riva Live y crear componentes"""
    print("\n" + "="*70)
    print("EJEMPLO 1: Riva Live - Transcripción en Tiempo Real (Básico)")
    print("="*70)
    
    # Obtener factory para ambiente Riva Live
    env_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
    print(f"✅ Ambiente: {env_factory.get_name()}")
    
    # Crear componentes
    transcriber = env_factory.create_transcriber()
    print(f"✅ Transcriber: {type(transcriber).__name__}")
    
    formatter = env_factory.create_formatter()
    print(f"✅ Formatter: {type(formatter).__name__}")
    
    # Usar componentes
    print(f"   Config del servidor: {transcriber.config.server}")


def ejemplo_riva_live_vad():
    """Ejemplo avanzado: Riva Live con VAD y configuración personalizada"""
    print("\n" + "="*70)
    print("EJEMPLO 2: Riva Live - VAD Personalizado")
    print("="*70)
    
    # Obtener factory
    env_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
    
    # Crear configuración personalizada
    audio_config = AudioConfig(
        sample_rate=16000,
        channels=1,
        chunk_size=256
    )
    
    vad_config = VADConfig(
        voice_threshold=100,
        silence_threshold=30,
        silence_duration=2.0,
        min_voice_duration=0.4
    )
    
    # Crear recorder VAD personalizado
    vad_recorder = env_factory.create_recorder(
        RecorderType.VAD,
        audio_config=audio_config,
        vad_config=vad_config
    )
    print(f"✅ VAD Recorder creado: {type(vad_recorder).__name__}")
    print(f"   - Voice threshold: {vad_config.voice_threshold}")
    print(f"   - Silence threshold: {vad_config.silence_threshold}")


def ejemplo_riva_live_background():
    """Ejemplo: Grabar sesión completa en background"""
    print("\n" + "="*70)
    print("EJEMPLO 3: Riva Live - Grabación de Sesión Completa")
    print("="*70)
    
    env_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
    
    audio_config = AudioConfig()
    
    # Crear recorder de background para grabar sesión completa
    bg_recorder = env_factory.create_recorder(
        RecorderType.BACKGROUND,
        audio_config=audio_config
    )
    print(f"✅ Background Recorder creado: {type(bg_recorder).__name__}")
    print("   Uso: bg_recorder.start() -> ... -> bg_recorder.stop_and_save()")


def ejemplo_riva_live_continuous():
    """Ejemplo: Chunks de duración fija"""
    print("\n" + "="*70)
    print("EJEMPLO 4: Riva Live - Chunks de Duración Fija")
    print("="*70)
    
    env_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
    
    # Crear recorder de chunks continuos
    continuous_recorder = env_factory.create_recorder(
        RecorderType.CONTINUOUS,
        audio_config=AudioConfig()
    )
    print(f"✅ Continuous Recorder creado: {type(continuous_recorder).__name__}")
    print("   Uso: recorder.record(stop_callback=lambda frames: elapsed >= duration)")


# ============================================================================
# EJEMPLO 5: Local Batch (Futuro) - Placeholder
# ============================================================================

def ejemplo_local_batch_placeholder():
    """Ejemplo: Estructura de Local Batch para procesamiento batch local"""
    print("\n" + "="*70)
    print("EJEMPLO 5: Local Batch - Placeholder (Futuro)")
    print("="*70)
    
    env_factory = TranscriptionEnvironmentFactoryProvider.get_local_batch()
    print(f"✅ Ambiente: {env_factory.get_name()}")
    
    # El transcriber lanzaría NotImplementedError
    try:
        transcriber = env_factory.create_transcriber()
    except NotImplementedError as e:
        print(f"⚠️  Transcriber no implementado (esperado): {str(e)[:60]}...")
    
    # Pero formatters y recorders funcionan
    formatter = env_factory.create_formatter()
    print(f"✅ Formatter: {type(formatter).__name__} (MarkdownFormatter)")


# ============================================================================
# EJEMPLO 6: Factory Caching - Eficiencia
# ============================================================================

def ejemplo_factory_caching():
    """Ejemplo: Las factories se cachean para reutilización eficiente"""
    print("\n" + "="*70)
    print("EJEMPLO 6: Factory Caching - Instancias Reutilizadas")
    print("="*70)
    
    # Primera llamada: crea factory
    factory1 = TranscriptionEnvironmentFactoryProvider.get_riva_live()
    print(f"Factory 1 (primera llamada): {id(factory1)}")
    
    # Segunda llamada: retorna la misma instancia cacheada
    factory2 = TranscriptionEnvironmentFactoryProvider.get_riva_live()
    print(f"Factory 2 (segunda llamada): {id(factory2)}")
    
    if factory1 is factory2:
        print("✅ ¡Misma instancia! Caching funciona correctamente")
    
    # También funciona con create_environment
    factory3 = TranscriptionEnvironmentFactoryProvider.create_environment(
        EnvironmentType.RIVA_LIVE
    )
    print(f"Factory 3 (create_environment): {id(factory3)}")
    
    if factory1 is factory3:
        print("✅ Caching consistente entre métodos")


# ============================================================================
# EJEMPLO 7: Usar Abstract Factory en contexto real (como en realtime.py)
# ============================================================================

def ejemplo_context_real():
    """Ejemplo: Uso en contexto real similar a realtime.py"""
    print("\n" + "="*70)
    print("EJEMPLO 7: Contexto Real - Flujo Completo Simplificado")
    print("="*70)
    
    # 1. Obtener ambiente
    environment_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
    print(f"1️⃣  Ambiente inicializado: {environment_factory.get_name()}")
    
    # 2. Crear transcriber
    transcriber = environment_factory.create_transcriber()
    print(f"2️⃣  Transcriber: {type(transcriber).__name__}")
    
    # 3. Configurar audio
    audio_config = AudioConfig()
    vad_config = VADConfig()
    
    # 4. Crear recorder VAD
    vad_recorder = environment_factory.create_recorder(
        RecorderType.VAD,
        audio_config=audio_config,
        vad_config=vad_config
    )
    print(f"3️⃣  Recorder VAD: {type(vad_recorder).__name__}")
    
    # 5. Crear formatter
    formatter = environment_factory.create_formatter()
    print(f"4️⃣  Formatter: {type(formatter).__name__}")
    
    print("\n✅ Todos los componentes son compatibles y listos para usar")
    print("   Flujo: Grabar(VAD) → Transcribir(Riva) → Formatear(Segmented)")


# ============================================================================
# EJEMPLO 8: Extensibilidad - Agregar nuevo ambiente
# ============================================================================

def ejemplo_extensibilidad():
    """Ejemplo teórico: Cómo extender con un nuevo ambiente"""
    print("\n" + "="*70)
    print("EJEMPLO 8: Extensibilidad - Cómo Agregar Nuevo Ambiente")
    print("="*70)
    
    print("""
Para agregar un nuevo ambiente (ej: GoogleCloudSpeech):

1. Crear nueva factory concreta:
   ────────────────────────────────
   class GoogleCloudSpeechFactory(TranscriptionEnvironmentFactory):
       def create_transcriber(self):
           return GoogleCloudTranscriber()
       
       def create_recorder(self, recorder_type, **kwargs):
           # Reutilizar recorders existentes
           return AudioRecorderFactoryProvider.create_recorder(...)
       
       def create_formatter(self):
           return GoogleCloudFormatter()
       
       def get_name(self):
           return "Google Cloud Speech"

2. Extender EnvironmentType enum:
   ───────────────────────────────
   class EnvironmentType(Enum):
       RIVA_LIVE = "riva_live"
       LOCAL_BATCH = "local_batch"
       GOOGLE_CLOUD = "google_cloud"  # ← NUEVO

3. Registrar en provider:
   ──────────────────────
   @classmethod
   def create_environment(cls, environment_type):
       if environment_type == EnvironmentType.GOOGLE_CLOUD:
           cls._factories[environment_type] = GoogleCloudSpeechFactory()
       # ... resto del código

4. ¡Usar sin cambios en realtime.py!:
   ────────────────────────────────
   env = TranscriptionEnvironmentFactoryProvider.create_environment(
       EnvironmentType.GOOGLE_CLOUD
   )
    """)


# ============================================================================
# EJEMPLO 9: Testing - Crear Mocks
# ============================================================================

def ejemplo_testing():
    """Ejemplo teórico: Cómo usar para testing"""
    print("\n" + "="*70)
    print("EJEMPLO 9: Testing - Crear Mocks y Stubs")
    print("="*70)
    
    print("""
Para testing, es fácil crear mocks:

class MockTranscriber:
    def offline_transcribe(self, audio_data, language):
        return "Mock transcription result"

class MockFactory(TranscriptionEnvironmentFactory):
    def create_transcriber(self):
        return MockTranscriber()
    
    def create_recorder(self, recorder_type, **kwargs):
        return MockRecorder()
    
    def create_formatter(self):
        return MarkdownFormatter()
    
    def get_name(self):
        return "Mock Environment"

# En tus tests:
@patch('src.core.environment_factory.TranscriptionEnvironmentFactoryProvider.get_riva_live')
def test_realtime(mock_factory):
    mock_factory.return_value = MockFactory()
    # ... tu test aquí
    """)


# ============================================================================
# MAIN - Ejecutar todos los ejemplos
# ============================================================================

def main():
    """Ejecutar todos los ejemplos"""
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  EJEMPLOS DE USO: Abstract Factory Pattern".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    ejemplos = [
        ejemplo_riva_live_basic,
        ejemplo_riva_live_vad,
        ejemplo_riva_live_background,
        ejemplo_riva_live_continuous,
        ejemplo_local_batch_placeholder,
        ejemplo_factory_caching,
        ejemplo_context_real,
        ejemplo_extensibilidad,
        ejemplo_testing,
    ]
    
    for ejemplo in ejemplos:
        try:
            ejemplo()
        except Exception as e:
            print(f"\n❌ Error en {ejemplo.__name__}: {e}")
    
    print("\n" + "="*70)
    print("✅ TODOS LOS EJEMPLOS COMPLETADOS")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
