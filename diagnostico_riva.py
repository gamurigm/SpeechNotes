#!/usr/bin/env python3
"""Diagnóstico completo de conectividad Riva Cloud Function."""
import os
import sys
import grpc
import riva.client

# Configuración
SERVER = "grpc.nvcf.nvidia.com:443"
FUNCTION_ID = os.getenv("RIVA_FUNCTION_ID", "1598d209-5e27-4d3c-8079-4751568b1081")
API_KEY = os.getenv("NGC_API_KEY", "")

print("=" * 60)
print("DIAGNÓSTICO RIVA CLOUD FUNCTION")
print("=" * 60)
print(f"Server: {SERVER}")
print(f"Function ID: {FUNCTION_ID}")
print(f"API Key: {'✓ configurada' if API_KEY else '✗ FALTA'}")
print("=" * 60)

if not API_KEY:
    print("\n❌ ERROR: NGC_API_KEY no está configurada")
    print("   Ejecuta: $env:NGC_API_KEY = 'tu-api-key'")
    sys.exit(1)

# Intentar conexión básica
print("\n1️⃣  Probando conexión gRPC básica...")
try:
    auth = riva.client.Auth(
        use_ssl=True,
        uri=SERVER,
        metadata_args=[
            ["function-id", FUNCTION_ID],
            ["authorization", f"Bearer {API_KEY}"]
        ]
    )
    print("   ✓ Auth object creado")
    
    asr = riva.client.ASRService(auth)
    print("   ✓ ASRService inicializado")
    
    # Intentar GetRivaSpeechRecognitionConfig
    print("\n2️⃣  Intentando listar modelos ASR...")
    try:
        cfg = asr.stub.GetRivaSpeechRecognitionConfig(
            riva.client.proto.riva_asr_pb2.RivaSpeechRecognitionConfigRequest()
        )
        print("   ✓ GetRivaSpeechRecognitionConfig exitoso!")
        
        online = {}
        offline = {}
        for mc in cfg.model_config:
            lang = mc.parameters.get("language_code", "unknown")
            model_type = mc.parameters.get("type", "unknown")
            model_name = mc.model_name
            
            if model_type == "online":
                online.setdefault(lang, []).append(model_name)
            elif model_type == "offline":
                offline.setdefault(lang, []).append(model_name)
        
        print("\n   📊 MODELOS DISPONIBLES:")
        print("\n   Online (streaming):")
        if online:
            for lang, models in sorted(online.items()):
                print(f"     • {lang}:")
                for m in models:
                    print(f"       - {m}")
        else:
            print("     (ninguno)")
        
        print("\n   Offline (batch):")
        if offline:
            for lang, models in sorted(offline.items()):
                print(f"     • {lang}:")
                for m in models:
                    print(f"       - {m}")
        else:
            print("     (ninguno)")
        
        print("\n" + "=" * 60)
        print("✅ DIAGNÓSTICO EXITOSO")
        print("=" * 60)
        
        # Recomendación
        if not any(lang.startswith("es") for lang in online.keys() | offline.keys()):
            print("\n⚠️  NOTA: No se encontraron modelos en español (es-ES).")
            print("   Para transcribir en español, necesitas:")
            print("   1. Desplegar una Cloud Function con modelo español, o")
            print("   2. Usar el modelo inglés disponible para probar la pipeline.")
        
    except grpc.RpcError as e:
        print(f"   ❌ Error al listar modelos:")
        print(f"      Status: {e.code()}")
        print(f"      Details: {e.details()}")
        print(f"      Debug: {e.debug_error_string() if hasattr(e, 'debug_error_string') else 'N/A'}")
        
        if e.code() == grpc.StatusCode.INTERNAL:
            print("\n   🔍 ANÁLISIS DEL ERROR INTERNAL:")
            if "failed to open stateful work request" in e.details():
                print("   ❌ La Cloud Function tiene un problema de configuración.")
                print("\n   📋 PASOS PARA RESOLVER:")
                print("   1. Verifica en NGC Portal que la función esté 'Active':")
                print("      https://catalog.ngc.nvidia.com/")
                print(f"      Busca function-id: {FUNCTION_ID}")
                print("   2. Confirma que el deployment use un container/NIM de ASR")
                print("      (ej: nvidia/parakeet, nvidia/riva-speech)")
                print("   3. Revisa los logs del deployment en el portal")
                print("   4. Si persiste, intenta re-deploy o crea nueva función")
            else:
                print(f"   Detalles: {e.details()}")
        
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Error inesperado: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
