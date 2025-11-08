# Guía rápida para iniciar NVIDIA Riva Server

## ⚠️ Requisitos previos
- ✅ Docker instalado (tienes: 28.3.2)
- ✅ GPU NVIDIA (tienes: GTX 1650 con 4GB)
- ✅ NVIDIA drivers (tienes: 577.03)
- ⚠️ NGC API Key (necesitas obtenerla)

## 🔑 Paso 1: Obtener NGC API Key

1. Ve a: https://ngc.nvidia.com/setup/api-key
2. Crea cuenta o inicia sesión (usa email institucional o personal)
3. Genera una API Key
4. Copia la key (la necesitarás en el siguiente paso)

## 📥 Paso 2: Descargar Riva Quick Start

```bash
# En WSL o terminal Linux
cd ~
mkdir -p riva_quickstart
cd riva_quickstart

# Descargar script de inicio
wget https://raw.githubusercontent.com/nvidia-riva/riva-quickstart/main/riva_quickstart_v2.22.0.sh
bash riva_quickstart_v2.22.0.sh
```

## ⚙️ Paso 3: Configurar Riva

Edita el archivo `config.sh`:

```bash
nano config.sh
```

Configura solo ASR (Speech Recognition):

```bash
# Services to enable
service_enabled_asr=true
service_enabled_nlp=false
service_enabled_tts=false
service_enabled_nmt=false

# ASR models - solo español e inglés
models_asr=("rivas_asr_spanish_us_streaming" "rivas_asr_english_us_streaming")

# GPU
gpus_to_use="device=0"

# NGC API Key (pega tu key aquí)
NGC_API_KEY="tu_api_key_aqui"
```

## 📦 Paso 4: Descargar modelos

```bash
# Esto descarga ~3-5GB de modelos
bash riva_init.sh
```

⏳ Esto tomará 10-30 minutos dependiendo de tu conexión.

## 🚀 Paso 5: Iniciar servidor

```bash
bash riva_start.sh
```

Espera a ver:
```
Riva server is ready...
```

## ✅ Paso 6: Verificar que funciona

```bash
# Ver contenedores corriendo
docker ps | grep riva

# Debería mostrar algo como:
# riva-speech    Up 2 minutes    0.0.0.0:50050-50051->50050-50051/tcp
```

## 🧪 Paso 7: Probar con tu script

```powershell
# Desde PowerShell en Windows
python .\python-clients\scripts\asr\simple_streaming_demo.py --input-file .\python-clients\data\examples\en-US_AntiBERTa_for_word_boosting_testing.wav --server localhost:50051 --show-intermediate
```

## 🛑 Para detener el servidor

```bash
bash riva_stop.sh
```

## 📊 Monitoreo de GPU

Mientras Riva corre:
```bash
watch -n 1 nvidia-smi
```

## ⚠️ Notas importantes

**Memoria GPU:** Tu GTX 1650 tiene 4GB. Los modelos de Riva necesitan ~2-3GB.
- ✅ Suficiente para ASR básico
- ⚠️ Si tienes problemas, cierra otras aplicaciones que usen GPU

**Puerto:** Riva usa puerto 50051 (gRPC) y 50050 (HTTP)

**Primera ejecución:** Los modelos se cargan en GPU, puede tardar 1-2 minutos

## 🐛 Solución de problemas

**Error: "Out of memory"**
```bash
# Edita config.sh y reduce modelos
models_asr=("rivas_asr_english_us_streaming")  # Solo inglés
```

**Error: "NGC API Key invalid"**
- Verifica que copiaste la key completa
- No debe tener espacios al inicio/final

**Puerto en uso:**
```bash
# Ver qué usa el puerto 50051
lsof -i :50051
# Matar proceso si es necesario
kill -9 PID
```

## 📝 Comandos rápidos

```bash
# Ver logs del servidor
docker logs riva-speech -f

# Reiniciar servidor
bash riva_stop.sh && bash riva_start.sh

# Ver uso de GPU en tiempo real
watch -n 1 nvidia-smi
```

## 🎯 Siguiente paso

Una vez que Riva esté corriendo, podrás usar todos los scripts de streaming que creamos con transcripción REAL.
