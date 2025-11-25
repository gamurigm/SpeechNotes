"""
Test script to verify ConfigManager Singleton implementation
"""
from src.core.config import ConfigManager


def test_singleton_pattern():
    """
    Prueba que ConfigManager es un verdadero Singleton:
    - Solo existe una instancia
    - Múltiples llamadas devuelven la misma instancia
    """
    
    print("=" * 60)
    print("PRUEBA: Patrón Singleton - ConfigManager")
    print("=" * 60)
    
    # Método 1: Usando get_instance() (recomendado)
    print("\n1. Creando primera instancia con get_instance()...")
    config1 = ConfigManager.get_instance()
    print(f"   config1 id: {id(config1)}")
    
    # Método 2: Usando get_instance() de nuevo
    print("\n2. Obteniendo segunda instancia con get_instance()...")
    config2 = ConfigManager.get_instance()
    print(f"   config2 id: {id(config2)}")
    
    # Método 3: Usando constructor directamente
    print("\n3. Intentando crear tercera instancia con constructor...")
    config3 = ConfigManager()
    print(f"   config3 id: {id(config3)}")
    
    # Verificación
    print("\n" + "=" * 60)
    print("VERIFICACIÓN:")
    print("=" * 60)
    
    if config1 is config2 is config3:
        print("✅ ÉXITO: Las tres variables apuntan a la MISMA instancia")
        print(f"   Todas tienen el mismo ID: {id(config1)}")
    else:
        print("❌ ERROR: Se crearon múltiples instancias")
        return False
    
    # Verificar que comparten el mismo estado
    print("\n4. Verificando que comparten el mismo estado...")
    riva_config1 = config1.get_riva_config()
    riva_config2 = config2.get_riva_config()
    
    print(f"   API Key desde config1: {riva_config1.api_key[:20]}...")
    print(f"   API Key desde config2: {riva_config2.api_key[:20]}...")
    
    if riva_config1.api_key == riva_config2.api_key:
        print("✅ Ambas instancias devuelven la misma configuración")
    else:
        print("❌ ERROR: Las configuraciones son diferentes")
        return False
    
    print("\n" + "=" * 60)
    print("✅ PATRÓN SINGLETON IMPLEMENTADO CORRECTAMENTE")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        test_singleton_pattern()
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
