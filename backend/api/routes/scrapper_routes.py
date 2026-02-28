"""
Rutas API para scraper de YouTube
Endpoints para extraer comentarios y buscar videos
"""

from fastapi import APIRouter, HTTPException
import logging
import time

from backend.schemas import (
    ExtractCommentsRequest,
    ExtractCommentsResponse,
    CommentResponse,
    SearchVideosRequest,
    SearchVideosResponse,
    VideoResponse,
    AnalyzeSentimentRequest,
    AnalyzeSentimentResponse,
    SentimentResult,
)
from backend.api.services.scrapper_service import ScraperService
from backend.scrapper import YouTubeScraper
from backend.sentiment_analysis.sentiment_client import get_sentiment_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Scraper"])


@router.post(
    "/get-comentarios",
    response_model=ExtractCommentsResponse,
    summary="Extraer comentarios de un video o short de YouTube",
)
async def extract_comments(request: ExtractCommentsRequest):
    """
    Extrae comentarios de un video o short de YouTube
    
    **Acepta ambos formatos:**
    - Video: https://www.youtube.com/watch?v=xxxxx
    - Short: https://www.youtube.com/shorts/xxxxx
    
    **Parámetros:**
    - **url**: URL del video o short
    - **max_comments**: Máximo de comentarios a extraer (1-1000)
    - **language**: Idioma (solo 'es' soportado)
    - **content_type**: Tipo de contenido ('auto', 'video', 'short')
    
    **Retorna:**
    - Lista de comentarios limpiados (sin URLs, emojis)
    - Información de autor, fecha, likes
    - Tiempo de ejecución
    """
    try:
        # Usar servicio de scraper
        comments, metadata = ScraperService.extract_comments(
            url=request.url,
            max_comments=request.max_comments,
            language=request.language,
            content_type=request.content_type
        )
        
        if metadata["error"]:
            logger.warning(f"Error en extracción: {metadata['error']}")
            raise HTTPException(status_code=400, detail=metadata["error"])
        
        # Convertir a response model
        comment_responses = [
            CommentResponse(
                comment_id=c.comment_id,
                text=c.text,
                author=c.author,
                timestamp=c.timestamp.isoformat(),
                likes=c.likes,
                is_reply=c.is_reply,
                parent_comment_id=c.parent_comment_id
            )
            for c in comments
        ]
        
        return ExtractCommentsResponse(
            success=True,
            message=f"Se extrajeron {len(comments)} comentarios exitosamente",
            video_id=metadata["video_id"],
            video_title=comments[0].video_title if comments else "Video",
            comments_extracted=len(comments),
            comments=comment_responses,
            execution_time_seconds=metadata["execution_time_seconds"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extrayendo comentarios: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al extraer comentarios: {str(e)}")


@router.post(
    "/search-videos",
    response_model=SearchVideosResponse,
    summary="Buscar videos de YouTube",
)
async def search_videos(request: SearchVideosRequest):
    """
    Busca videos en YouTube basado en términos de búsqueda
    
    - **query**: Término de búsqueda (ej: "elecciones peru 2026")
    - **max_results**: Máximo de videos a retornar (1-50)
    - **hours_back**: Solo videos de las últimas N horas (1-168)
    
    Retorna:
    - Lista de videos ordenados por vistas (descendente)
    - Información: título, canal, vistas, likes, fecha
    - Tiempo de ejecución
    """
    try:
        start_time = time.time()
        
        if not request.query or len(request.query) < 3:
            raise HTTPException(
                status_code=400,
                detail="El término de búsqueda debe tener al menos 3 caracteres"
            )
        
        logger.info(f"🔍 Buscando videos: '{request.query}'")
        
        # Inicializar scraper y buscar
        scraper = YouTubeScraper()
        videos = scraper.search_videos(
            query=request.query,
            max_results=request.max_results,
            hours_back=request.hours_back
        )
        
        # Convertir a response model
        video_responses = [
            VideoResponse(
                video_id=v.video_id,
                title=v.title,
                channel=v.channel,
                views=v.views,
                likes=v.likes,
                upload_date=v.upload_date.isoformat(),
                duration=v.duration,
                url=v.url
            )
            for v in videos
        ]
        
        execution_time = time.time() - start_time
        
        logger.info(f"✅ {len(videos)} videos encontrados en {execution_time:.1f}s")
        
        return SearchVideosResponse(
            success=True,
            message=f"Se encontraron {len(videos)} videos",
            query=request.query,
            videos_found=len(videos),
            videos=video_responses,
            execution_time_seconds=execution_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error buscando videos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al buscar videos: {str(e)}")


@router.post(
    "/analyze-sentiment",
    response_model=AnalyzeSentimentResponse,
    summary="Analizar sentimientos de comentarios",
)
async def analyze_sentiment(request: AnalyzeSentimentRequest):
    """
    Analiza el sentimiento de múltiples textos/comentarios
    
    **Funcionalidades:**
    - Soporta análisis de batch (múltiples textos)
    - Usa modelo BERT multilingual (soporta español)
    - Retorna sentimientos en 3 clases: positive, negative, neutral
    - Incluye scores de confianza
    
    **Parámetros:**
    - **texts**: Lista de textos a analizar
    - **language**: Idioma (default: 'es')
    - **use_simplified**: True para 3 clases, False para 5 clases
    
    **Retorna:**
    - Sentimiento de cada texto
    - Puntuación de confianza
    - Estadísticas agregadas
    - Tiempo de ejecución
    """
    try:
        if not request.texts or len(request.texts) == 0:
            raise HTTPException(
                status_code=400,
                detail="La lista de textos no puede estar vacía"
            )
        
        if len(request.texts) > 500:
            raise HTTPException(
                status_code=400,
                detail="Máximo 500 textos por request"
            )
        
        logger.info(f"🤖 Analizando sentimientos de {len(request.texts)} textos")
        
        start_time = time.time()
        
        # Usar cliente del sentiment-service
        sentiment_client = get_sentiment_client()
        
        # Llamar al servicio remoto (o fallback local)
        service_result = await sentiment_client.analyze_sentiment(
            texts=request.texts,
            use_simplified=request.use_simplified
        )
        
        sentiments = service_result["sentiments"]
        scores = service_result["scores"]
        confidences = service_result["confidences"]
        service_name = service_result["service"]
        
        # Construir resultados
        results = []
        stats = {"total": 0, "positive": 0, "negative": 0, "neutral": 0}
        
        for text, sentiment, score, confidence in zip(request.texts, sentiments, scores, confidences):
            if not text or not isinstance(text, str):
                continue
            
            stats[sentiment] += 1
            stats["total"] += 1
            
            results.append(
                SentimentResult(
                    text=text.strip(),
                    sentiment=sentiment,
                    score=score,
                    confidence=confidence
                )
            )
        
        execution_time = time.time() - start_time
        
        logger.info(f"✅ Análisis completado ({service_name}): {stats['positive']}+ {stats['negative']}-, {stats['neutral']}= en {execution_time:.2f}s")
        
        return AnalyzeSentimentResponse(
            success=True,
            message=f"Se analizaron {len(request.texts)} textos exitosamente",
            texts_analyzed=len(request.texts),
            sentiments=sentiments,
            results=results,
            stats=stats,
            execution_time_seconds=execution_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analizando sentimientos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al analizar sentimientos: {str(e)}"
        )
