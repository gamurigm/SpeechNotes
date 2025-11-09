#!/bin/bash
# Script para iniciar NVIDIA Riva ASR Server
# Optimizado para GTX 1650 (4GB VRAM)
# Requiere: Docker, NVIDIA GPU, nvidia-docker en WSL

set -e  # Salir si hay errores

# Configuración
RIVA_VERSION="2.22.0"
RIVA_DIR="$HOME/riva_quickstart"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cargar NGC_API_KEY desde .env si existe
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | grep NGC_API_KEY | xargs)
    echo "✅ NGC_API_KEY cargada desde .env"
fi

echo "🚀 Iniciando NVIDIA Riva Server (GTX 1650 Optimizado)"
echo "====================================================="
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi
echo "✅ Docker encontrado: $(docker --version)"

# Verificar NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA drivers no están instalados"
    exit 1
fi
echo "✅ GPU encontrada:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo ""

# Verificar nvidia-docker
if ! docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "❌ nvidia-docker no está configurado correctamente"
    echo "   Instalar con: sudo apt install nvidia-container-toolkit"
    exit 1
fi
echo "✅ nvidia-docker funcional"
echo ""

# Crear directorio si no existe
mkdir -p "$RIVA_DIR"
cd "$RIVA_DIR"

echo "📦 Descargando Riva Quick Start scripts..."

# Descargar script principal
if [ ! -f "riva_quickstart_v${RIVA_VERSION}.sh" ]; then
    wget -q --show-progress https://raw.githubusercontent.com/nvidia-riva/riva-quickstart/main/riva_quickstart_v${RIVA_VERSION}.sh
    bash riva_quickstart_v${RIVA_VERSION}.sh
    echo "✅ Scripts descargados"
else
    echo "✅ Scripts ya descargados"
fi
echo ""

echo "⚙️  Configurando para GTX 1650 (4GB VRAM)..."

# Crear config.sh optimizado para GTX 1650
cat > config.sh << 'EOF'
# ====================================================
# Riva Quick Start Configuration
# Optimizado para GTX 1650 (4GB VRAM)
# ====================================================

# Servicios a habilitar
service_enabled_asr=true
service_enabled_nlp=false
service_enabled_tts=false
service_enabled_nmt=false

# Modelo ASR ligero para 4GB VRAM
# Parakeet es un modelo compacto (~1.5GB) ideal para GPUs pequeñas
models_asr=("rmir_asr_parakeet_riva_1.18.0.riva")

# Configuración de GPU
gpus_to_use="device=0"
riva_target_gpu_family="Turing"        # GTX 1650 es arquitectura Turing

# Optimizaciones de memoria para 4GB VRAM
triton_max_batch_size="4"               # Batch pequeño
triton_instance_count="1"               # Una instancia
triton_memory_pool_byte_size="536870912" # 512MB pool

# Opciones de Triton
triton_use_model_store=true
triton_model_store="$(pwd)/models"

# Configuración de red
riva_speech_api_port="50051"
riva_speech_api_http_port="50050"

# Logging
riva_log_level="WARNING"                # Reducir logging

EOF

echo "✅ config.sh creado (GTX 1650 optimizado)"
echo ""

# Mostrar configuración
echo "📋 Configuración actual:"
echo "   - Servicio: ASR (Speech Recognition)"
echo "   - Modelo: Parakeet (ligero, ~1.5GB)"
echo "   - GPU: GTX 1650 (Turing, 4GB VRAM)"
echo "   - Batch size: 4"
echo "   - Instancias: 1"
echo "   - Puerto gRPC: 50051"
echo "   - Puerto HTTP: 50050"
echo ""

echo "🔑 Configuración de NGC API Key"
echo "================================"
echo ""

if [ -z "$NGC_API_KEY" ]; then
    echo "❌ NGC_API_KEY no está configurada"
    echo ""
    echo "El archivo .env no se encontró o no contiene NGC_API_KEY."
    echo ""
    echo "Para configurarla:"
    echo "1. Ve a: https://ngc.nvidia.com/setup/api-key"
    echo "2. Agrega NGC_API_KEY=tu_api_key en el archivo .env"
    echo ""
    exit 1
else
    echo "✅ NGC_API_KEY configurada: ${NGC_API_KEY:0:20}..."
    echo ""
    echo "📥 Descargando modelo Parakeet (~1.5GB)..."
    echo "   Esto puede tardar varios minutos..."
    
    # Inicializar modelos
    if [ ! -d "models" ] || [ -z "$(ls -A models)" ]; then
        bash riva_init.sh
    else
        echo "✅ Modelos ya descargados"
    fi
fi
echo ""

echo "🚀 Iniciando servidor Riva..."
echo ""

# Verificar si ya está corriendo
if docker ps | grep -q riva-speech; then
    echo "⚠️  Riva ya está corriendo. Deteniéndolo primero..."
    bash riva_stop.sh 2>/dev/null || true
    sleep 2
fi

# Iniciar servidor
bash riva_start.sh

echo ""
echo "✅ Servidor Riva iniciado!"
echo ""
echo "📍 Endpoints disponibles:"
echo "   gRPC: localhost:50051"
echo "   HTTP: localhost:50050"
echo ""
echo "🔍 Verificar estado:"
echo "   docker ps | grep riva"
echo "   docker logs riva-speech"
echo ""
echo "📊 Monitorear GPU:"
echo "   watch -n 1 nvidia-smi"
echo ""
echo "🧪 Probar con tu script:"
echo "   python python-clients/scripts/asr/simple_streaming_demo.py \\"
echo "     --input-file python-clients/data/examples/en-US_AntiBERTa_for_word_boosting_testing.wav \\"
echo "     --server localhost:50051"
echo ""
echo "🛑 Para detener:"
echo "   bash riva_stop.sh"
echo ""
