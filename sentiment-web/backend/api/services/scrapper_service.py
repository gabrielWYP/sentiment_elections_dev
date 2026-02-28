"""
Servicio de scraping de YouTube
Contiene la lógica de negocio para extraer y procesar comentarios
"""

import logging
import time
import re
from typing import Tuple, List
from backend.scrapper import YouTubeScraper, Comment

logger = logging.getLogger(__name__)


class ScraperService:
    """Lógica de negocio para scraping de YouTube"""
    
    @staticmethod
    def _is_valid_youtube_url(url: str) -> bool:
        """
        Validar si una URL es de YouTube válida (video o short)
        
        Formatos aceptados:
        - https://www.youtube.com/watch?v=XXXXX (video)
        - https://youtube.com/watch?v=XXXXX (video)
        - https://youtu.be/XXXXX (acortado)
        - https://www.youtube.com/shorts/XXXXX (short)
        - https://youtube.com/shorts/XXXXX (short)
        """
        youtube_patterns = [
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=[\w-]{11}',
            r'(?:https?:\/\/)?youtu\.be\/[\w-]{11}',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/[\w-]{11}',
        ]
        
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    @staticmethod
    def _extract_video_id(url: str) -> str:
        """
        Extrae el ID del video/short de una URL de YouTube
        
        Args:
            url: URL de YouTube
        
        Returns:
            Video ID (11 caracteres) o None si es inválido
        """
        # Patrón para youtube.com/watch?v=, youtu.be/ y youtube.com/shorts/
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})',
            r'youtube\.com\/shorts\/([\w-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _detect_content_type(url: str) -> str:
        """Detecta si es un video o short basándose en la URL"""
        if 'shorts' in url.lower():
            return 'short'
        return 'video'
    
    @staticmethod
    def extract_comments(
        url: str,
        max_comments: int = 300,
        language: str = "es",
        content_type: str = "auto"
    ) -> Tuple[List[Comment], dict]:
        """
        Servicio para extraer comentarios de un video o short
        
        Args:
            url: URL del video/short
            max_comments: Máximo de comentarios
            language: Idioma requerido
            content_type: Tipo de contenido ("auto", "video", "short")
        
        Returns:
            (lista de comentarios, metadata)
        """
        start_time = time.time()
        metadata = {
            "video_id": None,
            "content_type": content_type,
            "success": False,
            "error": None,
            "execution_time": 0,
            "execution_time_seconds": 0,
        }
        
        try:
            # Validar URL
            if not ScraperService._is_valid_youtube_url(url):
                logger.warning(f"URL inválida: {url}")
                metadata["error"] = "URL de YouTube inválida"
                return [], metadata
            
            # Extraer video ID
            video_id = ScraperService._extract_video_id(url)
            if not video_id:
                logger.warning(f"No se pudo extraer video ID de: {url}")
                metadata["error"] = "No se pudo extraer el ID del video"
                return [], metadata
            
            metadata["video_id"] = video_id
            
            # Detectar tipo de contenido si es "auto"
            if content_type == "auto":
                content_type = ScraperService._detect_content_type(url)
                metadata["content_type"] = content_type
            
            logger.info(f"📥 Extrayendo comentarios del {content_type}: {video_id}")
            
            # Inicializar scraper y extraer
            scraper = YouTubeScraper(max_comments_per_video=max_comments)
            comments = scraper.extract_comments(
                video_id=video_id,
                video_title="",
                content_type=content_type
            )
            
            # Filtrar por idioma si es necesario
            if language == "es":
                comments = [c for c in comments if c.language == "es"]
            
            metadata["success"] = True
            metadata["execution_time"] = time.time() - start_time
            metadata["execution_time_seconds"] = metadata["execution_time"]
            
            logger.info(f"✅ {len(comments)} comentarios extraídos en {metadata['execution_time']:.1f}s")
            
            return comments, metadata
        
        except Exception as e:
            logger.error(f"Error en scraper service: {str(e)}", exc_info=True)
            metadata["error"] = str(e)
            metadata["execution_time"] = time.time() - start_time
            metadata["execution_time_seconds"] = metadata["execution_time"]
            return [], metadata
