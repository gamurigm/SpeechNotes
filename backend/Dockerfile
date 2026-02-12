# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/backend"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  ffmpeg \
  build-essential \
  curl \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirement file first for better caching
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the rest of the application
COPY backend/ /app/backend/
COPY src/ /app/src/

# Create directory for notes and knowledge base
RUN mkdir -p /app/notas /app/knowledge_base

# Add a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/docs || exit 1

# Command to run the application
CMD ["python", "backend/main.py"]
