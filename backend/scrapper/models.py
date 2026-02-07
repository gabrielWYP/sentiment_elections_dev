"""
Modelos de datos para comentarios y análisis
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Comment:
    """Estructura de un comentario de YouTube"""
    comment_id: str
    text: str
    author: str
    author_id: str
    timestamp: datetime
    likes: int
    video_id: str
    video_title: str
    is_reply: bool = False
    parent_comment_id: Optional[str] = None
    language: str = "es"  # Detectado
    
    def to_dict(self):
        """Convertir a diccionario para guardar"""
        return {
            'comment_id': self.comment_id,
            'text': self.text,
            'author': self.author,
            'author_id': self.author_id,
            'timestamp': self.timestamp.isoformat(),
            'likes': self.likes,
            'video_id': self.video_id,
            'video_title': self.video_title,
            'is_reply': self.is_reply,
            'parent_comment_id': self.parent_comment_id,
            'language': self.language,
        }


@dataclass
class YouTubeVideo:
    """Estructura de un video de YouTube"""
    video_id: str
    title: str
    channel: str
    views: int
    likes: int
    upload_date: datetime
    duration: int  # en segundos
    url: str
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'video_id': self.video_id,
            'title': self.title,
            'channel': self.channel,
            'views': self.views,
            'likes': self.likes,
            'upload_date': self.upload_date.isoformat(),
            'duration': self.duration,
            'url': self.url,
        }


@dataclass
class ScraperStats:
    """Estadísticas de una ejecución de scraping"""
    start_time: datetime
    end_time: Optional[datetime] = None
    videos_found: int = 0
    videos_processed: int = 0
    comments_extracted: int = 0
    comments_filtered: int = 0  # Comentarios descartados (no español)
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'videos_found': self.videos_found,
            'videos_processed': self.videos_processed,
            'comments_extracted': self.comments_extracted,
            'comments_filtered': self.comments_filtered,
            'total_errors': len(self.errors),
            'errors': self.errors,
        }
