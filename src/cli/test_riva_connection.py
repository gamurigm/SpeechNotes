#!/usr/bin/env python3
"""
Test script to verify Riva connection and diagnose connectivity issues
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import grpc
from src.core import ConfigManager
from src.core.environment_factory import TranscriptionEnvironmentFactoryProvider

def test_connection():
    """Test connection to Riva server"""
    print("🔍 Diagnóstico de Conexión a Riva")
    print("=" * 60)
    
    try:
        # Load configuration
        print("\n1️⃣ Cargando configuración...")
        environment_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
        transcriber = environment_factory.create_transcriber()
        config = transcriber.config
        
        print(f"   ✅ Servidor: {config.server}")
        print(f"   ✅ Function ID: {config.function_id}")
        print(f"   ✅ API Key configurada: {'Sí' if config.api_key else 'No'}")
        
        # Test connection
        print("\n2️⃣ Probando conexión gRPC...")
        print("   ⏳ Intentando conectar (esto puede tomar unos segundos)...")
        
        # Force initialization of ASR service
        try:
            _ = transcriber.asr_service
            print("   ✅ Conexión establecida exitosamente!")
            
            # Try a simple transcription
            print("\n3️⃣ Probando transcripción de prueba...")
            import numpy as np
            
            # Create 1 second of silence as test audio
            sample_rate = 16000
            duration = 1
            silence = np.zeros(sample_rate * duration, dtype=np.int16)
            audio_bytes = silence.tobytes()
            
            print("   ⏳ Enviando audio de prueba...")
            result = transcriber.offline_transcribe(audio_bytes, language="es")
            
            if result:
                print(f"   ✅ Transcripción recibida: '{result}'")
            else:
                print("   ✅ Servidor respondió correctamente (audio en silencio)")
            
            print("\n" + "=" * 60)
            print("✅ DIAGNÓSTICO EXITOSO - Riva está funcionando correctamente")
            print("=" * 60)
            return True
            
        except grpc.RpcError as e:
            print(f"\n   ❌ Error de gRPC: {e.code()}")
            print(f"   📝 Detalles: {e.details()}")
            
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("\n💡 Soluciones sugeridas:")
                print("   1. Verifica que el servidor de Riva esté corriendo")
                print("   2. Revisa tu conexión a internet")
                print("   3. Verifica que la URL del servidor sea correcta")
                print("   4. Verifica que el firewall no esté bloqueando la conexión")
            elif e.code() == grpc.StatusCode.UNAUTHENTICATED:
                print("\n💡 Soluciones sugeridas:")
                print("   1. Verifica que tu API Key sea correcta en el archivo .env")
                print("   2. Verifica que el Function ID sea correcto")
            else:
                print(f"\n💡 Código de error gRPC: {e.code()}")
                print("   Consulta la documentación de Riva para más información")
            
            return False
            
        except Exception as e:
            print(f"\n   ❌ Error inesperado: {type(e).__name__}")
            print(f"   📝 Mensaje: {e}")
            return False
            
    except FileNotFoundError as e:
        print(f"\n❌ Error: Archivo de configuración no encontrado")
        print(f"   {e}")
        print("\n💡 Asegúrate de tener un archivo .env en el directorio raíz del proyecto")
        return False
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {type(e).__name__}")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
