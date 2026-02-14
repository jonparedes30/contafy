# Multi-stage build para producción eficiente
FROM python:3.11-slim as builder

# Variables de compilación
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Imagen final de producción
FROM python:3.11-slim

# Metadata
LABEL maintainer="contafy" \
      description="CONTAFY Web App - Django 5.2 + PostgreSQL"

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    DOCKER_RUNNING=true

# Instalar solo runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 app && \
    mkdir -p /app /app/media /app/staticfiles && \
    chown -R app:app /app

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias compiladas desde builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código del proyecto
COPY --chown=app:app . /app/

# Cambiar a usuario no-root
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python manage.py check --databases default || exit 1

# Puerto
EXPOSE 8000

# Comando por defecto: gunicorn con configuración production-ready
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"] 