# Dockerfile para Sentiment Service - Optimizado
# Multi-stage para minimizar tamaño

# ============== STAGE 1: BUILDER ==============
FROM python:3.12-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY sentiment-service/requirements.txt .

# Instalar en wheels para reutilizar
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# ============== STAGE 2: RUNTIME ==============
FROM python:3.12-slim

ENV TRANSFORMERS_CACHE=/root/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar wheels del builder (SIN build-essential)
COPY --from=builder /build/wheels /tmp/wheels
COPY sentiment-service/requirements.txt .

# Instalar desde wheels (rápido y sin compilación)
RUN pip install --no-cache-dir --no-index --find-links /tmp/wheels -r requirements.txt \
    && rm -rf /tmp/wheels

# Copiar código
COPY sentiment-service/ .

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8001/health')"

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
