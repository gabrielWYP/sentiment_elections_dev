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

import logging
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Importar routers
from backend.api.routes import router as scraper_router

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

# Crear instancia de FastAPI
app = FastAPI(
    title="Termómetro Político Perú 2026",
    description="API para análisis de sentimientos en comentarios de YouTube",
    version="1.0.0",
    debug=IS_DEVELOPMENT
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


@app.get("/")
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


# ==================== PLACEHOLDER ROUTES ====================

@app.get("/api/v1/trends")
async def get_trends():
    """Obtener tendencias políticas"""
    return {
        "status": "placeholder",
        "message": "Endpoint no implementado aún"
    }


@app.get("/api/v1/parties")
async def get_parties():
    """Obtener análisis por partido"""
    return {
        "status": "placeholder",
        "message": "Endpoint no implementado aún"
    }


@app.get("/api/v1/comments")
async def get_comments(limit: int = 10, party: str = None):
    """Obtener comentarios analizados"""
    return {
        "status": "placeholder",
        "message": "Endpoint no implementado aún",
        "filters": {
            "limit": limit,
            "party": party
        }
    }


@app.post("/api/v1/sentiment")
async def analyze_sentiment(text: str):
    """Analizar sentimiento de un texto"""
    return {
        "status": "placeholder",
        "message": "Endpoint no implementado aún",
        "input": text
    }


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