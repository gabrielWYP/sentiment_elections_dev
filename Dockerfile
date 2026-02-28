# ============== STAGE 1: BUILD REACT ==============
FROM node:22-slim AS react-build

WORKDIR /react-build

COPY frontend/package*.json ./

RUN npm install --frozen-lockfile

COPY frontend/ .

RUN npm run build

# ============== STAGE 2: PYTHON BUILDER (wheels) ==============
FROM python:3.12-slim AS python-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# ============== STAGE 3: RUNTIME (Backend + React) ==============
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    APP_MODE=PRODUCTION

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libffi8 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar wheels del builder Python
COPY --from=python-builder /build/wheels /tmp/wheels
COPY requirements.txt .

# Instalar dependencias Python desde wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links /tmp/wheels -r requirements.txt

# Copiar código backend
COPY backend/ ./backend/

# Copiar React compilado a /app/static (FastAPI lo servará)
COPY --from=react-build /react-build/dist ./static/

# Usuario no-root (Debian syntax)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2"]
