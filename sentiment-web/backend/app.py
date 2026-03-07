"""
Termómetro Político - Backend API
Análisis de sentimientos en comentarios de YouTube sobre elecciones

Estructura:
- app.py: Inicialización minimal
- config.py: Configuración centralizada
- routes/: Endpoints
- services/: Lógica de negocio
- scrapers/: YouTube scraping + sentiment analysis
- database/: Conexión Oracle + modelos
- utils/: Utilidades y helpers
"""
#ci/cd


import logging
import os
import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv

# Importar routers
from backend.api.routes import router as scraper_router

# Importar cliente de sentiment service
from backend.sentiment_analysis.sentiment_client import get_sentiment_client

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Determinar modo de ejecución
APP_MODE = os.getenv('APP_MODE', 'DEVELOPMENT').upper()
IS_DEVELOPMENT = APP_MODE == 'DEVELOPMENT'

logger.info(f"🚀 Iniciando Termómetro Político en modo {APP_MODE}")

# ==================== LIFESPAN ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    # Startup
    logger.info("⚙️  Inicializando dependencias...")
    
    # Verificar sentiment service
    sentiment_client = get_sentiment_client()
    logger.info(f"🔌 Conectando con Sentiment Service: {sentiment_client.service_url}")
    
    # Intentar conectar (máximo 3 intentos con timeout)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            is_healthy = await sentiment_client.check_health()
            if is_healthy:
                logger.info("✅ Sentiment Service conectado y listo")
                break
            else:
                logger.warning(f"⚠️  Intento {attempt + 1}/{max_retries}: Sentiment Service no respondió")
        except Exception as e:
            logger.warning(f"⚠️  Intento {attempt + 1}/{max_retries}: {str(e)}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(2)  # Esperar 2 segundos antes de reintentar
    
    if not sentiment_client.is_healthy:
        logger.warning("⚠️  Sentiment Service no disponible - usando análisis local")
    
    logger.info("✅ Backend inicializado correctamente")
    
    yield
    
    # Shutdown
    logger.info("🛑 Deteniendo backend...")

# Crear instancia de FastAPI CON lifespan
app = FastAPI(
    title="Termómetro Político Perú 2026",
    description="API para análisis de sentimientos en comentarios de YouTube",
    version="1.0.0",
    debug=IS_DEVELOPMENT,
    lifespan=lifespan
)

# CORS Configuration
if IS_DEVELOPMENT:
    logger.info("⚙️  Modo DEVELOPMENT - Hot reload activado, CORS permisivo")
    # Desarrollo: permitir todos los orígenes
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    logger.info("⚙️  Modo PRODUCTION - CORS restrictivo")
    # Producción: solo localhost
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["localhost", "127.0.0.1"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )


# ==================== MIDDLEWARE CONFIGURATION ====================


@app.get("/api/v1/info")
async def root():
    """Endpoint raíz - información de la API"""
    return {
        "name": "Termómetro Político Perú 2026",
        "version": "1.0.0",
        "mode": APP_MODE,
        "status": "online",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "info": "/api/v1/info",
            "trends": "/api/v1/trends",
            "parties": "/api/v1/parties",
            "comments": "/api/v1/comments",
            "sentiment": "/api/v1/sentiment",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": APP_MODE
    }


# ==================== ROUTER CONFIGURATION ====================
# Incluir routers de módulos específicos
app.include_router(scraper_router, prefix="/api/v1", tags=["Scraper"])

# ==================== ERROR HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler para excepciones HTTP"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": exc.status_code,
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handler para excepciones no controladas"""
    logger.error(f"Error no controlado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "status": 500,
            "detail": str(exc) if IS_DEVELOPMENT else "Error interno"
        }
    )


# ==================== STATIC FILES CONFIGURATION ====================
# Servir el frontend React (en producción)
# El Dockerfile copia los archivos compilados a /app/static
frontend_dist = Path("/app/static")

if frontend_dist.exists():
    logger.info(f"📁 Sirviendo frontend React desde: {frontend_dist}")
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
else:
    logger.warning(f"⚠️  Directorio de frontend no encontrado: {frontend_dist}")
    logger.info("   En desarrollo, ejecuta: cd frontend && npm run dev")