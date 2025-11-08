#!/bin/bash
# Script para instalar NVIDIA Container Toolkit en WSL
# Esto permite que Docker acceda a la GPU NVIDIA

set -e

echo "🔧 Instalando NVIDIA Container Toolkit"
echo "======================================="
echo ""

# Verificar si estamos en WSL
if ! grep -qi microsoft /proc/version; then
    echo "⚠️  Este script está diseñado para WSL"
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Paso 1: Configurando repositorio de NVIDIA..."

# Agregar clave GPG
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Agregar repositorio
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

echo "✅ Repositorio configurado"
echo ""

echo "📦 Paso 2: Actualizando paquetes..."
sudo apt-get update

echo ""
echo "📦 Paso 3: Instalando nvidia-container-toolkit..."
sudo apt-get install -y nvidia-container-toolkit

echo "✅ Instalación completada"
echo ""

echo "⚙️  Paso 4: Configurando Docker..."
sudo nvidia-ctk runtime configure --runtime=docker

echo "✅ Docker configurado"
echo ""

echo "🔄 Paso 5: Reiniciando Docker..."
sudo systemctl restart docker 2>/dev/null || sudo service docker restart

echo "✅ Docker reiniciado"
echo ""

echo "🧪 Paso 6: Verificando instalación..."
echo ""

if docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi; then
    echo ""
    echo "✅ ¡NVIDIA Container Toolkit instalado correctamente!"
    echo ""
    echo "🚀 Ahora puedes ejecutar:"
    echo "   ./start_riva_optimized.sh"
else
    echo ""
    echo "❌ La verificación falló."
    echo ""
    echo "Pasos de solución:"
    echo "1. Reinicia WSL: wsl --shutdown (desde PowerShell)"
    echo "2. Vuelve a abrir WSL"
    echo "3. Ejecuta este script de nuevo"
fi
