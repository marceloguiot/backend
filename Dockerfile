# Usamos Python 3.10 o 3.11 (compatible con tus librerías)
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Variables de entorno para optimizar Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalamos dependencias del sistema necesarias para compilar algunas librerías
# (útil para cryptography o drivers de SQL si hiciera falta)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos primero el requirements.txt para aprovechar la caché de Docker
COPY requirements.txt .

# Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Exponemos el puerto (FastAPI usa 8000 por defecto)
EXPOSE 8000

# Comando para ejecutar la app. 
# IMPORTANTE: Cambia "main:app" por "nombre_de_tu_archivo:nombre_instancia_fastapi"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]