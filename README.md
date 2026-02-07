# Termómetro Político Perú 2026

Aplicación para análisis de sentimientos en comentarios de YouTube sobre elecciones políticas peruanas.

## 🚀 Inicio Rápido

### Modo Desarrollo (localhost:5000 - Hot Reload)

```bash
# 1. Crear entorno virtual o usar conda
conda activate pruebas_env

# 2. Instalar dependencias
pip install -r requirements-dev.txt

# 3. Crear archivo .env (copiar de .env.example)
cp .env.example .env

# 4. Ejecutar en localhost
cd sentiment_elections_dev
python -m backend.app

# 5. Acceder
# API: http://localhost:5000
# Docs: http://localhost:5000/docs
# Redoc: http://localhost:5000/redoc
```

### Modo Producción (puerto 8000)

```bash
# Cambiar APP_MODE en .env
APP_MODE=PRODUCTION

python -m backend.app
```

### Docker Producción

```bash
cd sentiment_elections_dev
docker build -t sentiment-api .
docker run -p 8001:8000 sentiment-api
```

---

## 📁 Estructura del Proyecto

```
sentiment_elections_dev/
├── backend/
│   ├── __init__.py
│   ├── app.py                 # 🔴 APP PRINCIPAL - Puerto 5000 (dev) / 8000 (prod)
│   ├── config.py              # Configuración centralizada
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api_routes.py      # (Por crear) Endpoints API
│   │   └── health_routes.py   # (Por crear) Health checks
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sentiment_service.py    # (Por crear) Análisis de sentimientos
│   │   ├── scraper_service.py      # (Por crear) YouTube scraping
│   │   └── analysis_service.py     # (Por crear) Análisis de datos
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── youtube_scraper.py      # (Por crear) Scraper de YT
│   │   └── comment_processor.py    # (Por crear) Procesar comentarios
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── db_config.py            # (Por crear) Conexión Oracle
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py               # (Por crear) Logging
│       └── validators.py           # (Por crear) Validadores
│
├── frontend/
│   ├── templates/
│   └── static/
│
├── .env                       # Variables de entorno (local)
├── .env.example              # Plantilla de .env
├── requirements-base.txt     # Dependencias producción
├── requirements-dev.txt      # Dependencias desarrollo
├── requirements.txt          # Apunta a requirements-base.txt
├── Dockerfile                # Docker multi-stage
├── docker-compose.yml        # (Próximamente)
├── README.md                 # Este archivo
└── OPTIMIZATIONS.md          # Notas de optimización (ARM64)
```

---

## 📊 Endpoints Disponibles

### Health

```
GET /health
```

Respuesta:
```json
{
  "status": "healthy",
  "mode": "DEVELOPMENT"
}
```

### Trends (Placeholder)

```
GET /api/v1/trends
```

### Parties (Placeholder)

```
GET /api/v1/parties
```

### Comments (Placeholder)

```
GET /api/v1/comments?limit=10&party=fujimorismo
```

### Sentiment Analysis (Placeholder)

```
POST /api/v1/sentiment
{
  "text": "Me encanta Perú"
}
```

---

## 🔧 Variables de Entorno

Ver `.env.example` para todas las opciones.

Principales:

```env
# Modo: DEVELOPMENT o PRODUCTION
APP_MODE=DEVELOPMENT

# Oracle Autonomous DB
ORACLE_USER=admin
ORACLE_PASSWORD=your_password
ORACLE_CONNECTION_STRING=your_connection

# Scraper
SCRAPER_ENABLED=True
SCRAPER_SCHEDULE_HOURS=6
```

---

## 📈 Próximos Pasos

✅ **Backend base creado**

⏭️ **Próximo:**
1. Crear rutas de API completas
2. Servicio de análisis de sentimientos con ONNX
3. Scraper de YouTube con yt-dlp
4. Conexión Oracle Autonomous DB
5. Job scheduler (cada 6h)
6. Frontend dashboard

---

## 🐳 Development vs Production

| Aspecto | Development | Production |
|---------|------------|------------|
| **URL** | localhost:5000 | 0.0.0.0:8000 |
| **Hot Reload** | ✅ Sí | ❌ No |
| **Debug** | ✅ Enabled | ❌ Disabled |
| **CORS** | ⭐ Todos | 🔒 Restricted |
| **Workers** | 1 | 4 |
| **Modo** | APP_MODE=DEVELOPMENT | APP_MODE=PRODUCTION |

---

## 📚 Documentación API (Automática)

Una vez iniciado, accede a:

- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

---

**Versión:** 1.0.0  
**Actualizado:** Febrero 2026  
**Plataforma:** ARM64 Linux
