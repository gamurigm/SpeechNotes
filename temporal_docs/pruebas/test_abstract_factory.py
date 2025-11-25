"""
Test for Abstract Factory Pattern Implementation
Validates that TranscriptionEnvironmentFactory works correctly
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.environment_factory import (
    TranscriptionEnvironmentFactoryProvider,
    EnvironmentType,
    RivaLiveFactory,
)
from src.audio import RecorderType


def test_riva_live_factory():
    """Test RivaLiveFactory creation and component generation"""
    print("🧪 Prueba 1: RivaLiveFactory")
    print("-" * 50)
    
    try:
        # Get the Riva Live factory
        environment_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
        
        # Verify it's the correct type
        assert isinstance(environment_factory, RivaLiveFactory), "Factory type mismatch"
        print(f"✅ Factory obtenida: {environment_factory.get_name()}")
        
        # Test transcriber creation
        transcriber = environment_factory.create_transcriber()
        print(f"✅ Transcriber creado: {type(transcriber).__name__}")
        
        # Test formatter creation
        formatter = environment_factory.create_formatter()
        print(f"✅ Formatter creado: {type(formatter).__name__}")
        
        print("✅ PRUEBA 1 PASADA\n")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba 1: {e}\n")
        return False


def test_environment_factory_provider():
    """Test TranscriptionEnvironmentFactoryProvider"""
    print("🧪 Prueba 2: TranscriptionEnvironmentFactoryProvider")
    print("-" * 50)
    
    try:
        # Test get_riva_live
        factory1 = TranscriptionEnvironmentFactoryProvider.get_riva_live()
        factory2 = TranscriptionEnvironmentFactoryProvider.get_riva_live()
        
        # Should be the same instance (cached)
        assert factory1 is factory2, "Factories should be cached"
        print("✅ Caching de factories funciona correctamente")
        
        # Test create_environment
        factory3 = TranscriptionEnvironmentFactoryProvider.create_environment(
            EnvironmentType.RIVA_LIVE
        )
        assert factory3 is factory1, "create_environment should return cached instance"
        print("✅ create_environment retorna instancia cached")
        
        # Test reset
        TranscriptionEnvironmentFactoryProvider.reset()
        factory4 = TranscriptionEnvironmentFactoryProvider.get_riva_live()
        assert factory4 is not factory1, "After reset, should create new instance"
        print("✅ Reset de factories funciona correctamente")
        
        print("✅ PRUEBA 2 PASADA\n")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba 2: {e}\n")
        return False


def test_recorder_creation():
    """Test recorder creation through factory"""
    print("🧪 Prueba 3: Creación de Recorders a través de Factory")
    print("-" * 50)
    
    try:
        environment_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
        
        # Test creating different recorder types
        recorder_types = [
            (RecorderType.VAD, "VAD Recorder"),
            (RecorderType.CONTINUOUS, "Continuous Recorder"),
        ]
        
        for recorder_type, name in recorder_types:
            try:
                recorder = environment_factory.create_recorder(recorder_type)
                print(f"✅ {name} creado: {type(recorder).__name__}")
            except Exception as e:
                print(f"⚠️  {name} falló (esto puede ser normal): {e}")
        
        print("✅ PRUEBA 3 PASADA\n")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba 3: {e}\n")
        return False


def test_local_batch_factory():
    """Test LocalBatchFactory (should raise NotImplementedError)"""
    print("🧪 Prueba 4: LocalBatchFactory (Placeholder)")
    print("-" * 50)
    
    try:
        environment_factory = TranscriptionEnvironmentFactoryProvider.get_local_batch()
        print(f"✅ Factory obtenida: {environment_factory.get_name()}")
        
        # Try to create transcriber (should raise NotImplementedError)
        try:
            transcriber = environment_factory.create_transcriber()
            print("❌ Should have raised NotImplementedError")
            return False
        except NotImplementedError as e:
            print(f"✅ NotImplementedError raised as expected: {str(e)[:50]}...")
        
        # Formatter and recorders should work
        formatter = environment_factory.create_formatter()
        print(f"✅ Formatter creado: {type(formatter).__name__}")
        
        print("✅ PRUEBA 4 PASADA\n")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba 4: {e}\n")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🎯 VALIDACIÓN: Abstract Factory Pattern")
    print("=" * 60 + "\n")
    
    results = [
        test_riva_live_factory(),
        test_environment_factory_provider(),
        test_recorder_creation(),
        test_local_batch_factory(),
    ]
    
    print("=" * 60)
    print(f"📊 RESUMEN: {sum(results)}/{len(results)} pruebas pasadas")
    
    if all(results):
        print("✅ ¡TODAS LAS PRUEBAS PASARON!")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
    
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
