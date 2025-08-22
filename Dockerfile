# Dockerfile para Visor de Inventario Pro
FROM python:3.9-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorio para templates si no existe
RUN mkdir -p templates

# Exponer puertos
EXPOSE 8000 8501 8050

# Script de inicio que permite elegir qué aplicación ejecutar
COPY start.sh .
RUN chmod +x start.sh

# Comando por defecto (FastAPI)
CMD ["python", "fastapi_app.py"]