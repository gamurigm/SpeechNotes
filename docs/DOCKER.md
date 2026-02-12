# Guía de Despliegue con Docker para SpeechNotes

Esta guía detalla cómo levantar la aplicación SpeechNotes utilizando Docker. La solución incluye:

- **Frontend**: Next.js (Puerto 3006)
- **Backend**: FastAPI (Puerto 8001)
- **Base de Datos**: MongoDB (Puerto 27017)

## Requisitos Previos

- Docker y Docker Compose instalados.
- Claves de API necesarias (NVIDIA NIM).

## Configuración

1. **Variables de Entorno**:
   Crea un archivo `.env` en la raíz del proyecto (basado en `.env.example`) y configura las siguientes variables:

   ```bash
   NVIDIA_API_KEY=nvapi-...
   NVIDIA_EMBEDDING_API_KEY=nvapi-...
   LOGFIRE_TOKEN=... (opcional)
   ```

   El archivo `docker-compose.yml` también utiliza estas variables.

## Ejecución

Para iniciar todos los servicios en segundo plano:

```bash
docker-compose up -d --build
```

### Verificación de Servicios

- **Frontend**: Accede a [http://localhost:3006](http://localhost:3006).
- **Backend Docs**: Accede a [http://localhost:8001/docs](http://localhost:8001/docs) para ver la documentación de la API.
- **MongoDB**: Accesible en `mongodb://localhost:27017`.

## Estructura de Volúmenes

- `mongodb_data`: Persistencia de datos de MongoDB.
- `web_prisma_data`: Persistencia de la base de datos SQLite del frontend (si se usa en contenedor).
- `./notas`: Mapeado a `/app/notas` en el backend para procesamiento de archivos locales.
- `./knowledge_base`: Mapeado a `/app/knowledge_base` en el backend.

## Solución de Problemas常见

### 1. Error de Conexión Frontend -> Backend
Si el frontend no puede conectar con el backend, verifica que el contenedor `speechnotes-backend` esté saludable (`docker ps`). El frontend utiliza la variable interna `API_URL=http://backend:8001` para comunicarse dentro de la red de Docker.

### 2. Base de Datos SQLite Bloqueada
Si encuentras errores de base de datos en el frontend, asegúrate de que no haya otra instancia de Prisma Studio o el servidor de desarrollo corriendo localmente que esté bloqueando el archivo `dev.db`.

### 3. Reconstrucción
Si cambias dependencias o código, reconstruye los contenedores:

```bash
docker-compose up -d --build --force-recreate
```
