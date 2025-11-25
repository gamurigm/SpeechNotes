#!/usr/bin/env python3
"""
Example: Using the Factory Method Pattern with Audio Recorders
Demonstrates how to use AudioRecorderFactoryProvider to create different recorder types
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.audio import (
    RecorderType,
    AudioConfig,
    VADConfig,
    AudioRecorderFactoryProvider
)


def example_microphone_stream():
    """Example: Create a continuous microphone stream recorder"""
    print("\n=== Ejemplo 1: Microphone Stream Recorder ===")
    print("Use case: Grabación continua de micrófono para streaming en tiempo real\n")
    
    config = AudioConfig(sample_rate=16000)
    
    # Create using the provider
    recorder = AudioRecorderFactoryProvider.create_recorder(
        RecorderType.MICROPHONE_STREAM,
        config=config
    )
    
    print(f"✅ Recorder created: {type(recorder).__name__}")
    print(f"   Config: Sample rate={recorder.config.sample_rate}, Channels={recorder.config.channels}")
    

def example_vad_recorder():
    """Example: Create a VAD-based recorder"""
    print("\n=== Ejemplo 2: VAD Recorder ===")
    print("Use case: Grabación activada por voz (Voice Activity Detection)\n")
    
    audio_config = AudioConfig(sample_rate=16000)
    vad_config = VADConfig(
        voice_threshold=1200,
        silence_threshold=800,
        silence_duration=2.0
    )
    
    # Create using the provider
    recorder = AudioRecorderFactoryProvider.create_recorder(
        RecorderType.VAD,
        config=audio_config,
        vad_config=vad_config
    )
    
    print(f"✅ Recorder created: {type(recorder).__name__}")
    print(f"   Audio Config: Sample rate={recorder.config.sample_rate}")
    print(f"   VAD Config: voice_threshold={recorder.vad_config.voice_threshold}, "
          f"silence_threshold={recorder.vad_config.silence_threshold}")


def example_continuous_recorder():
    """Example: Create a continuous fixed-duration recorder"""
    print("\n=== Ejemplo 3: Continuous Recorder ===")
    print("Use case: Grabación de chunks de duración fija (ej. 5 segundos)\n")
    
    config = AudioConfig(sample_rate=16000)
    
    # Create using the provider
    recorder = AudioRecorderFactoryProvider.create_recorder(
        RecorderType.CONTINUOUS,
        config=config
    )
    
    print(f"✅ Recorder created: {type(recorder).__name__}")
    print(f"   Config: Sample rate={recorder.config.sample_rate}, Channels={recorder.config.channels}")


def example_background_recorder():
    """Example: Create a background recorder"""
    print("\n=== Ejemplo 4: Background Recorder ===")
    print("Use case: Grabación continua en background mientras se transcribe\n")
    
    config = AudioConfig(sample_rate=16000)
    
    # Create using the provider
    recorder = AudioRecorderFactoryProvider.create_recorder(
        RecorderType.BACKGROUND,
        config=config
    )
    
    print(f"✅ Recorder created: {type(recorder).__name__}")
    print(f"   Config: Sample rate={recorder.config.sample_rate}")


def example_using_factory_directly():
    """Example: Using individual factories directly"""
    print("\n=== Ejemplo 5: Usar Factories Directamente ===")
    print("Use case: Si necesitas más control, puedes usar las factories individuales\n")
    
    from src.audio import VADRecorderFactory
    
    config = AudioConfig(sample_rate=16000)
    vad_config = VADConfig()
    
    # Create factory
    factory = VADRecorderFactory()
    
    # Create recorder using the factory
    recorder = factory.create_recorder(config, vad_config)
    
    print(f"✅ Recorder created using VADRecorderFactory: {type(recorder).__name__}")


def example_switching_recorders():
    """Example: Switch between different recorder types easily"""
    print("\n=== Ejemplo 6: Cambiar entre tipos de grabadores ===")
    print("Use case: Cambiar dinámicamente el tipo de grabador según el contexto\n")
    
    config = AudioConfig(sample_rate=16000)
    
    # Simulate switching based on user choice
    recorder_types = [
        RecorderType.MICROPHONE_STREAM,
        RecorderType.VAD,
        RecorderType.CONTINUOUS,
    ]
    
    for rec_type in recorder_types:
        recorder = AudioRecorderFactoryProvider.create_recorder(rec_type, config=config)
        print(f"✅ {rec_type.value:20} -> {type(recorder).__name__}")


if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════════╗")
    print("║ Factory Method Pattern - Audio Recorder Examples           ║")
    print("║ Demuestra cómo usar el patrón Factory Method               ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Run examples
    example_microphone_stream()
    example_vad_recorder()
    example_continuous_recorder()
    example_background_recorder()
    example_using_factory_directly()
    example_switching_recorders()
    
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║ VENTAJAS DEL FACTORY METHOD PATTERN                        ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print("║ ✓ Desacoplamiento: El cliente no conoce clases concretas   ║")
    print("║ ✓ Extensibilidad: Agregar nuevos recorders es fácil        ║")
    print("║ ✓ SRP: Cada factory tiene una única responsabilidad        ║")
    print("║ ✓ OCP: Abierto para extensión, cerrado para modificación   ║")
    print("║ ✓ Cambio dinámico: Cambiar recorders en runtime            ║")
    print("╚════════════════════════════════════════════════════════════╝")
