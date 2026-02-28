"""
Microservice para análisis de sentimientos
Carga el modelo BERT multilingual una sola vez al startup
"""

import logging
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Agregar path al módulo compartido
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.sentiment_analysis.sentiment_service import get_analyzer

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos de request/response
class AnalyzeRequest(BaseModel):
    texts: List[str]
    use_simplified: bool = True

class SentimentResult(BaseModel):
    text: str
    sentiment: str
    score: float
    confidence: float

class AnalyzeResponse(BaseModel):
    sentiments: List[str]
    scores: List[float]
    confidences: List[float]
    results: List[SentimentResult]

# Variable global para el analizador
analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management - cargar modelo en startup"""
    global analyzer
    try:
        logger.info("🚀 Iniciando sentiment-service...")
        logger.info("📥 Precargando modelo BERT multilingual...")
        analyzer = get_analyzer()
        logger.info("✅ Modelo cargado y listo en memoria")
    except Exception as e:
        logger.error(f"❌ Error crítico al cargar modelo: {str(e)}")
        raise
    yield
    logger.info("🛑 Deteniendo sentiment-service")

# Crear app
app = FastAPI(
    title="Sentiment Analysis Service",
    version="1.0.0",
    description="Microservicio para análisis de sentimientos usando BERT multilingual",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint para K8s"""
    return {
        "status": "healthy",
        "service": "sentiment-analysis",
        "model_loaded": analyzer is not None
    }

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_sentiment(request: AnalyzeRequest):
    """
    Analizar sentimiento de múltiples textos
    
    Args:
        texts: Lista de comentarios a analizar
        use_simplified: Si True, usa 3 clases (neg/neutral/pos); si False usa 5 clases
    
    Returns:
        - sentiments: Lista simple de sentimientos ["positive", "negative", ...]
        - scores: Lista de scores normalizados (0.0-1.0)
        - confidences: Lista de confianzas de la predicción
        - results: Objetos detallados con toda la info
    """
    if not analyzer:
        logger.error("❌ Modelo no cargado")
        raise HTTPException(status_code=503, detail="Modelo no disponible. Reinicia el servicio")
    
    if not request.texts or len(request.texts) == 0:
        raise HTTPException(status_code=400, detail="La lista de textos no puede estar vacía")
    
    try:
        logger.info(f"📊 Analizando {len(request.texts)} comentarios...")
        
        # Analizar batch
        results = analyzer.analyze_batch(request.texts, use_simplified=request.use_simplified)
        
        # Extraer componentes
        sentiments = [r.get("sentiment", "neutral") for r in results]
        scores = [r.get("score", 0.0) for r in results]
        confidences = [r.get("confidence", 0.0) for r in results]
        
        # Log de estadísticas
        positive = sum(1 for s in sentiments if s == "positive")
        negative = sum(1 for s in sentiments if s == "negative")
        neutral = sum(1 for s in sentiments if s == "neutral")
        
        logger.info(f"✅ Análisis completado: {positive} positivos, {negative} negativos, {neutral} neutrales")
        
        return AnalyzeResponse(
            sentiments=sentiments,
            scores=scores,
            confidences=confidences,
            results=[
                SentimentResult(
                    text=r["text"],
                    sentiment=r["sentiment"],
                    score=r["score"],
                    confidence=r["confidence"]
                )
                for r in results
            ]
        )
        
    except Exception as e:
        logger.error(f"❌ Error procesando batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

@app.get("/model-info")
async def model_info():
    """Información sobre el modelo cargado"""
    if not analyzer:
        raise HTTPException(status_code=503, detail="Modelo no cargado")
    
    return {
        "model": "nlptown/bert-base-multilingual-uncased-sentiment",
        "task": "sentiment-analysis",
        "languages": ["es", "en", "fr", "de", "nl", "it"],
        "classes": ["negative", "neutral", "positive"],
        "status": "ready"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
