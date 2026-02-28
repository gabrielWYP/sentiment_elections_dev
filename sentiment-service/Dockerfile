# ============== STAGE 1: BUILDER ==============
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copiamos solo lo necesario para el build
COPY requirements.txt .
RUN pip wheel --wheel-dir /build/wheels -r requirements.txt

# ============== STAGE 2: RUNTIME ==============
FROM python:3.11-slim

ENV HF_HOME=/root/.cache/huggingface \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    libpthread-stubs0-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/wheels /tmp/wheels
COPY requirements.txt .

RUN pip install --no-index --find-links /tmp/wheels -r requirements.txt \
    && rm -rf /tmp/wheels

# Estructura plana: copiamos el script y la carpeta del modelo en la raíz de /app
COPY app.py .
COPY ./modelo_onnx/ ./modelo_onnx/

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]