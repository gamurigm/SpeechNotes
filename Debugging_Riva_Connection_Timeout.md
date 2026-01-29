# Debugging Session: Riva Connection Timeout Error

**Date**: 2026-01-15  
**Issue**: RPC Connection Timeout during real-time transcription  
**Status**: ✅ Resolved

## Problem

During real-time transcription (`realtime.py`), the application crashed with:

```
❌ Error Inesperado: <_InactiveRpcError of RPC that terminated with:
        status = StatusCode.UNAVAILABLE
        details = "IOCP/Socket: Connection timed out"
```

Error occurred at segment #16 while transcribing an audio chunk.

## Root Cause

1. **Missing gRPC channel configuration**: No timeout settings or keepalive options
2. **No retry logic**: Single failure caused complete crash
3. **Default timeouts too short**: For slower networks or busy servers

## Solution Implemented

### 1. Added gRPC Channel Options ([riva_client.py](../../src/core/riva_client.py#L46-L56))

```python
channel_options = [
    ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
    ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
    ('grpc.keepalive_time_ms', 30000),  # 30 seconds
    ('grpc.keepalive_timeout_ms', 10000),  # 10 seconds
    ('grpc.keepalive_permit_without_calls', 1),
    ('grpc.http2.max_pings_without_data', 0),
    ('grpc.http2.min_time_between_pings_ms', 10000),
]

auth = Auth(
    uri=self.config.server,
    use_ssl=True,
    metadata_args=[...],
    options=channel_options  # Correct parameter name
)
```

**Important**: The parameter is `options`, not `channel_opts` (initial mistake corrected).

### 2. Added Automatic Retry Logic ([riva_client.py](../../src/core/riva_client.py#L127-L186))

- Maximum 3 retry attempts
- Exponential backoff: 1s, 2s, 4s
- Automatic service reconnection on timeout
- User-friendly error messages

### 3. Created Diagnostic Tool

New script: [test_riva_connection.py](../../src/cli/test_riva_connection.py)

Usage:
```bash
python src/cli/test_riva_connection.py
```

Tests:
- Configuration loading
- gRPC connection establishment
- Simple transcription request
- Provides specific error messages and solutions

## Testing

Run the diagnostic tool before using realtime transcription:

```bash
cd src/cli
python test_riva_connection.py
```

Expected output on success:
```
🔍 Diagnóstico de Conexión a Riva
==============================================================

1️⃣ Cargando configuración...
   ✅ Servidor: grpc.nvcf.nvidia.com:443
   ✅ Function ID: ...
   ✅ API Key configurada: Sí

2️⃣ Probando conexión gRPC...
   ⏳ Intentando conectar (esto puede tomar unos segundos)...
   ✅ Conexión establecida exitosamente!

3️⃣ Probando transcripción de prueba...
   ⏳ Enviando audio de prueba...
   ✅ Servidor respondió correctamente (audio en silencio)

==============================================================
✅ DIAGNÓSTICO EXITOSO - Riva está funcionando correctamente
==============================================================
```

## Prevention

For users experiencing connection issues:

1. **Check server status first**:
   ```bash
   python src/cli/test_riva_connection.py
   ```

2. **Verify configuration**:
   - `.env` file exists
   - `RIVA_SERVER`, `RIVA_API_KEY`, `RIVA_FUNCTION_ID` are set correctly

3. **Network issues**:
   - Check internet connectivity
   - Verify firewall isn't blocking gRPC (port 443)
   - Consider using a more stable network

## Related Files

- [riva_client.py](../../src/core/riva_client.py) - Main client with timeout fixes
- [realtime.py](../../src/cli/realtime.py) - Real-time transcription script
- [test_riva_connection.py](../../src/cli/test_riva_connection.py) - Diagnostic tool

## Lessons Learned

1. Always configure gRPC channels with appropriate timeouts
2. Implement retry logic for network operations
3. Provide clear diagnostic tools for connection issues
4. Use exponential backoff for retries
5. Reset connections on timeout errors
