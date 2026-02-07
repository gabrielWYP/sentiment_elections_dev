# Dockerfile optimizado para ARM64
# Multi-stage build para minimizar tamaño final
# Reducción: torch (2GB) → onnxruntime (50MB)

# Stage 1: Builder
FROM python:3.11-slim as builder

# Instalar dependencias de compilación (solo en builder)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copiar requirements OPTIMIZADOS
COPY requirements.txt .

# Crear wheel files en /build/wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime (mucho más pequeño)
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# Instalar solo dependencias de runtime necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libffi8 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar wheels del builder
COPY --from=builder /build/wheels /tmp/wheels
COPY requirements.txt .

# Instalar desde wheels (sin compilar)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links /tmp/wheels -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Usuario no-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

# Exponer puerto
EXPOSE 8888

# Comando de inicio (con variables de entorno)
CMD ["uvicorn", "backend.app:app", \
     "--host", "0.0.0.0", \
     "--port", "8888", \
     "--workers", "2"]
