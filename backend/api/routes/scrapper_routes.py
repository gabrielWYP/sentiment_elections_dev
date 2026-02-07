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
)
from backend.api.services.scrapper_service import ScraperService
from backend.scrapper import YouTubeScraper

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
