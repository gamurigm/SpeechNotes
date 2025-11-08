#!/bin/bash
# Script simplificado para iniciar NVIDIA Riva ASR Server
# Optimizado para GTX 1650 (4GB VRAM)

set -e

# Configuración
RIVA_DIR="$HOME/riva_quickstart"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cargar NGC_API_KEY desde .env
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | grep NGC_API_KEY | xargs)
fi

echo "🚀 Iniciando NVIDIA Riva ASR Server (GTX 1650)"
echo "=============================================="
echo ""

# Verificar requisitos
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

if ! docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "❌ nvidia-docker no está configurado"
    exit 1
fi

echo "✅ Docker y GPU verificados"
echo ""

# Crear directorio
mkdir -p "$RIVA_DIR"
cd "$RIVA_DIR"

# Descargar scripts oficiales de Riva
echo "📦 Descargando Riva QuickStart..."

if [ ! -f "riva_quickstart.sh" ]; then
    wget -q --show-progress https://raw.githubusercontent.com/nvidia-riva/riva-quickstart/main/riva_quickstart.sh
    chmod +x riva_quickstart.sh
fi

# Ejecutar quickstart para descargar archivos base
if [ ! -f "riva_init.sh" ]; then
    echo "Inicializando estructura de Riva..."
    bash riva_quickstart.sh 2>/dev/null || true
fi

# Si aún no existen los scripts, descargarlos manualmente
for script in riva_init.sh riva_start.sh riva_stop.sh riva_clean.sh; do
    if [ ! -f "$script" ]; then
        echo "Descargando $script..."
        wget -q https://raw.githubusercontent.com/nvidia-riva/riva-quickstart/main/$script
        chmod +x $script
    fi
done

echo "✅ Scripts descargados"
echo ""

# Crear config.sh optimizado
echo "⚙️  Configurando para GTX 1650 (4GB VRAM)..."

cat > config.sh << 'EOF'
# Riva Configuration - GTX 1650 Optimized

# NGC API Key
riva_ngc_org="nvidia"
riva_ngc_team="riva"
riva_ngc_image_version="2.22.0"

# Servicios
service_enabled_asr=true
service_enabled_nlp=false
service_enabled_tts=false
service_enabled_nmt=false

# Modelos ASR (ligero para 4GB VRAM)
# Usar modelo Conformer en inglés (más ligero que Parakeet)
models_asr=("rmir_asr_conformer_en_us_streaming")

# GPU
gpus_to_use="device=0"
riva_target_gpu_family="turing"

# Optimizaciones de memoria
triton_max_batch_size="4"
triton_instance_count="1"

# Puertos
riva_speech_api_port="50051"
EOF

echo "✅ Configuración creada"
echo ""

# Verificar NGC_API_KEY
if [ -z "$NGC_API_KEY" ]; then
    echo "❌ NGC_API_KEY no está configurada en .env"
    echo ""
    echo "Agrega esta línea a tu archivo .env:"
    echo "NGC_API_KEY=tu_api_key_aqui"
    echo ""
    echo "Obtén tu API key en: https://ngc.nvidia.com/setup/api-key"
    exit 1
fi

echo "✅ NGC_API_KEY configurada"
echo ""

# Inicializar modelos
echo "📥 Descargando modelos de ASR..."
echo "   Esto puede tardar 5-10 minutos (~1.5GB)"
echo ""

export NGC_API_KEY
bash riva_init.sh config.sh

echo ""
echo "🚀 Iniciando servidor Riva..."
echo ""

# Iniciar servidor
bash riva_start.sh config.sh

echo ""
echo "✅ Servidor Riva iniciado!"
echo ""
echo "📍 Endpoint: localhost:50051"
echo ""
echo "🧪 Para probar:"
echo "   cd /mnt/c/Users/gamur/OneDrive\\ -\\ UNIVERSIDAD\\ DE\\ LAS\\ FUERZAS\\ ARMADAS\\ ESPE/ESPE\\ VI\\ NIVEL\\ SII2025/Analisis\\ y\\ Diseño/p"
echo "   python python-clients/scripts/asr/transcribe_file.py \\"
echo "     --input-file python-clients/data/examples/en-US_sample.wav \\"
echo "     --server localhost:50051"
echo ""
echo "🛑 Para detener:"
echo "   cd ~/riva_quickstart && bash riva_stop.sh"
