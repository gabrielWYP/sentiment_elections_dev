"""
Schemas de request/response para la API
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime


# ==================== SCRAPER REQUESTS/RESPONSES ====================

class CommentResponse(BaseModel):
    """Respuesta de un comentario extraído"""
    comment_id: str
    text: str
    author: str
    timestamp: str
    likes: int
    is_reply: bool = False
    parent_comment_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "comment_id": "Ugx1234567890",
                "text": "Excelente análisis sobre las elecciones",
                "author": "Juan Pérez",
                "timestamp": "2026-02-07T10:30:00",
                "likes": 15,
                "is_reply": False,
                "parent_comment_id": None
            }
        }


class ExtractCommentsRequest(BaseModel):
    """Request para extraer comentarios de un video o short"""
    url: str = Field(..., description="URL del video o short de YouTube (ej: https://www.youtube.com/watch?v=xxxxx o https://www.youtube.com/shorts/xxxxx)")
    max_comments: int = Field(default=300, ge=1, le=1000, description="Máximo de comentarios a extraer")
    language: str = Field(default="es", description="Idioma de los comentarios (solo 'es' soportado)")
    content_type: str = Field(default="auto", description="Tipo de contenido: 'auto', 'video', 'short'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "max_comments": 300,
                "language": "es",
                "content_type": "auto"
            }
        }


class ExtractCommentsResponse(BaseModel):
    """Respuesta al extraer comentarios"""
    success: bool
    message: str
    video_id: str
    video_title: str
    comments_extracted: int
    comments: List[CommentResponse]
    execution_time_seconds: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Se extrajeron 45 comentarios exitosamente",
                "video_id": "dQw4w9WgXcQ",
                "video_title": "Mi video sobre elecciones",
                "comments_extracted": 45,
                "comments": [],
                "execution_time_seconds": 23.5
            }
        }


class SearchVideosRequest(BaseModel):
    """Request para buscar videos"""
    query: str = Field(..., description="Término de búsqueda (ej: 'elecciones peru 2026')")
    max_results: int = Field(default=10, ge=1, le=50, description="Máximo de videos a retornar")
    hours_back: int = Field(default=24, ge=1, le=168, description="Solo videos de las últimas N horas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "elecciones generales 2026 peru",
                "max_results": 10,
                "hours_back": 24
            }
        }


class VideoResponse(BaseModel):
    """Respuesta de un video"""
    video_id: str
    title: str
    channel: str
    views: int
    likes: int
    upload_date: str
    duration: int
    url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "title": "Análisis de las elecciones 2026",
                "channel": "Canal de Noticias",
                "views": 50000,
                "likes": 1200,
                "upload_date": "2026-02-07T10:00:00",
                "duration": 1440,
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }


class SearchVideosResponse(BaseModel):
    """Respuesta al buscar videos"""
    success: bool
    message: str
    query: str
    videos_found: int
    videos: List[VideoResponse]
    execution_time_seconds: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Se encontraron 5 videos",
                "query": "elecciones generales 2026 peru",
                "videos_found": 5,
                "videos": [],
                "execution_time_seconds": 8.3
            }
        }


class ErrorResponse(BaseModel):
    """Respuesta de error"""
    success: bool = False
    error: str
    error_type: str = "general"
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "URL inválida o video no encontrado",
                "error_type": "invalid_url"
            }
        }
