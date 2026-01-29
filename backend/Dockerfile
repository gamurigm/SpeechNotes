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
RUN pip install --no-cache-dir pydantic-ai logfire

# Copy the rest of the application
# We copy everything because backend imports from 'src' which is in root
COPY backend/ /app/backend/
COPY src/ /app/src/

# Create directory for notes
RUN mkdir -p /app/notas /app/knowledge_base

# Expose port
EXPOSE 8001

# Command to run the application
CMD ["python", "backend/main.py"]
