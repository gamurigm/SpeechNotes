# 🐳 Plan de Despliegue con Docker Hub

Este documento detalla los pasos para subir las imágenes de SpeechNotes a Docker Hub y desplegarlas en un servidor de producción o para demostración a clientes.

## 1. Preparación Local (Subida a Docker Hub)

Para que el servidor pueda descargar tus imágenes, primero debes construirlas y subirlas desde tu máquina de desarrollo.

### Requisitos:
- Tener una cuenta en [Docker Hub](https://hub.docker.com/).
- Docker instalado y corriendo en tu PC.

### Pasos:

1. **Iniciar sesión:**
   ```bash
   docker login -u TU_USUARIO_DOCKER
   ```

2. **Construir y Etiquetar (Backend):**
   ```bash
   docker build -t TU_USUARIO_DOCKER/speechnotes-backend:latest -f backend/Dockerfile .
   ```

3. **Construir y Etiquetar (Frontend):**
   ```bash
   docker build -t TU_USUARIO_DOCKER/speechnotes-frontend:latest -f web/Dockerfile ./web
   ```

4. **Subir Imágenes:**
   ```bash
   docker push TU_USUARIO_DOCKER/speechnotes-backend:latest
   docker push TU_USUARIO_DOCKER/speechnotes-frontend:latest
   ```

---

## 2. Despliegue en el Servidor (Cliente)

En el servidor del cliente **no necesitas el código fuente**. Solo necesitas los archivos de configuración.

### Archivos necesarios en el servidor:
1. `.env` (Con las API Keys de NVIDIA, Logfire, etc.)
2. `docker-compose.prod.yml` (El archivo que crearemos a continuación)

### Ejemplo de `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: speechnotes-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - speechnotes-network
    restart: unless-stopped

  backend:
    image: TU_USUARIO_DOCKER/speechnotes-backend:latest
    container_name: speechnotes-backend
    ports:
      - "8001:8001"
    environment:
      - MONGO_URI=mongodb://mongodb:27017/
      - MONGO_DB_NAME=agent_knowledge_base
      - NVIDIA_API_KEY=${NVIDIA_API_KEY}
      - NVIDIA_EMBEDDING_API_KEY=${NVIDIA_EMBEDDING_API_KEY}
      - LOGFIRE_TOKEN=${LOGFIRE_TOKEN}
    volumes:
      - ./notas:/app/notas
      - ./knowledge_base:/app/knowledge_base
    depends_on:
      - mongodb
    networks:
      - speechnotes-network
    restart: unless-stopped

  frontend:
    image: TU_USUARIO_DOCKER/speechnotes-frontend:latest
    container_name: speechnotes-frontend
    ports:
      - "3006:3006"
    environment:
      - NEXT_PUBLIC_API_URL=http://TU_IP_O_DOMINIO:8001
      - DATABASE_URL=file:./dev.db
    volumes:
      - web_prisma_data:/app/prisma
    depends_on:
      - backend
    networks:
      - speechnotes-network
    restart: unless-stopped

networks:
  speechnotes-network:
    driver: bridge

volumes:
  mongodb_data:
  web_prisma_data:
```

### Comando para ejecutar en el servidor:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 3. Beneficios de este método
- **Protección de IP:** El cliente solo recibe las imágenes compiladas, no tu código fuente original.
- **Portabilidad:** Puedes desplegar en cualquier servidor Linux (AWS, DigitalOcean, Azure) con un solo comando.
- **Mantenimiento:** Si haces una actualización, solo haces `push` de la nueva versión y el cliente solo tiene que hacer `docker-compose pull` para recibirla.
