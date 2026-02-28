"""
Scraper de YouTube usando yt-dlp para videos y youtube-comment-downloader para comentarios
Extrae videos por búsqueda y extrae comentarios
"""

import logging
import yt_dlp
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from youtube_comment_downloader import YoutubeCommentDownloader
from .models import Comment, YouTubeVideo, ScraperStats
from .comment_processor import CommentProcessor

logger = logging.getLogger(__name__)


class YouTubeScraper:
    """
    Scraper de YouTube usando yt-dlp
    
    LIMITACIONES DE yt-dlp:
    ========================
    1. Rate limiting: YouTube puede limitar si haces demasiadas solicitudes
    2. Comentarios deshabilitados: Si el video tiene comentarios deshabilitados, no se extraen
    3. Límite de comentarios: yt-dlp extrae los comentarios disponibles pero puede ser lento
    4. Datos limitados: Obtienes: ID, texto, autor, likes, timestamp
       NO obtienes: verificación de autor, etiquetas, etc.
    5. Respuestas con límite: Las respuestas se extraen pero pueden ser truncadas
    6. Sin autenticación: No puedes ver comentarios de canales privados/membresía
    7. Velocidad: Extraer 300 comentarios por video puede tomar 30-60 segundos
    8. Bloqueos: YouTube puede bloquear si detecta scraping automatizado
    
    RECOMENDACIONES:
    ================
    - Respetar rate limits (no scraping simultáneo de múltiples videos)
    - Agregar delays entre solicitudes
    - Implementar reintentos con backoff exponencial
    - Monitorear errores de rate limiting
    - Usar rotating proxies si es necesario (requiere extra config)
    """
    
    def __init__(self, max_comments_per_video: int = 300):
        """
        Inicializar scraper
        
        Args:
            max_comments_per_video: Máximo de comentarios a extraer por video
        """
        self.max_comments = max_comments_per_video
        self.processor = CommentProcessor()
        
        # Configurar yt-dlp
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,
        }
    
    def search_videos(
        self,
        query: str,
        max_results: int = 10,
        hours_back: int = 24
    ) -> List[YouTubeVideo]:
        """
        Buscar videos en YouTube
        
        Args:
            query: Término de búsqueda (ej: "elecciones generales 2026 peru")
            max_results: Número máximo de videos a retornar
            hours_back: Solo videos de las últimas N horas
        
        Returns:
            Lista de objetos YouTubeVideo ordenados por vistas (descendente)
        
        Nota: Esto requiere que yt-dlp tenga acceso a la búsqueda de YouTube
              La búsqueda es lenta y YouTube puede limitar los resultados
        """
        logger.info(f"🔍 Buscando videos: '{query}'")
        
        search_query = f"ytsearch{max_results}:{query}"
        videos = []
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                
                if 'entries' not in info:
                    logger.warning(f"No se encontraron videos para: {query}")
                    return []
                
                # Procesar cada resultado
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                
                for entry in info['entries']:
                    try:
                        upload_date = entry.get('upload_date')
                        if upload_date:
                            # Format: YYYYMMDD
                            upload_dt = datetime.strptime(upload_date, '%Y%m%d')
                        else:
                            upload_dt = datetime.now()
                        
                        # Filtrar por fecha
                        if upload_dt < cutoff_time:
                            logger.debug(f"Video descartado por antigüedad: {entry.get('title')}")
                            continue
                        
                        video = YouTubeVideo(
                            video_id=entry['id'],
                            title=entry.get('title', 'Unknown'),
                            channel=entry.get('uploader', 'Unknown'),
                            views=entry.get('view_count', 0),
                            likes=entry.get('like_count', 0),
                            upload_date=upload_dt,
                            duration=entry.get('duration', 0),
                            url=f"https://www.youtube.com/watch?v={entry['id']}"
                        )
                        videos.append(video)
                    
                    except Exception as e:
                        logger.error(f"Error procesando video: {e}")
                        continue
                
                # Ordenar por vistas (descendente)
                videos.sort(key=lambda v: v.views, reverse=True)
                logger.info(f"✅ {len(videos)} videos encontrados")
                
        except Exception as e:
            logger.error(f"Error en búsqueda de videos: {e}")
        
        return videos
    
    def extract_comments(
        self,
        video_id: str,
        video_title: str,
        content_type: str = "auto"
    ) -> List[Comment]:
        """
        Extraer comentarios de un video o short de YouTube con timeout seguro
        
        Args:
            video_id: ID del video/short de YouTube
            video_title: Título del video (para contexto)
            content_type: tipo de contenido ("auto", "video", "short")
        
        Returns:
            Lista de objetos Comment
        """
        # Detectar tipo de contenido si es "auto"
        if content_type == "auto":
            content_type = "video"
        
        logger.info(f"💬 Extrayendo comentarios del {content_type}: {video_id} (timeout: 45s)")
        
        comments = []
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Usar un contenedor mutable para compartir datos entre threads
        result_container = {'comments': [], 'completed': False}
        
        def extract_comments_thread():
            """Función que se ejecuta en un thread separado"""
            try:
                downloader = YoutubeCommentDownloader()
                comment_count = 0
                filtered_count = 0
                
                logger.debug(f"Iniciando descarga de comentarios para {video_id}")
                
                # Esto puede colgarse, pero está en un thread
                for raw_comment in downloader.get_comments_from_url(video_url, sort_by=0):
                    if comment_count >= self.max_comments:
                        logger.info(f"Alcanzado límite de {self.max_comments} comentarios")
                        break
                    
                    if result_container['completed']:  # Si timeout ya ocurrió
                        break
                    
                    try:
                        text = raw_comment.get('text', '')
                        
                        # Detectar idioma
                        language = CommentProcessor.detect_language(text)
                        
                        # Solo español
                        if language != 'es':
                            filtered_count += 1
                            logger.debug(f"Comentario descartado (no es español): {language}")
                            continue
                        
                        # Validar comentario
                        is_valid, cleaned_text = CommentProcessor.validate_comment(text, language)
                        if not is_valid:
                            filtered_count += 1
                            logger.debug("Comentario descartado (validación fallida)")
                            continue
                        
                        # Convertir timestamp
                        timestamp = raw_comment.get('time_text', '')
                        try:
                            if isinstance(timestamp, str) and timestamp:
                                try:
                                    ts = datetime.fromtimestamp(int(timestamp))
                                except:
                                    ts = datetime.now()
                            else:
                                ts = datetime.now()
                        except:
                            ts = datetime.now()
                        
                        # Crear objeto Comment
                        comment = Comment(
                            comment_id=raw_comment.get('cid', f"unknown_{comment_count}"),
                            text=cleaned_text,
                            author=raw_comment.get('author', 'Anonymous'),
                            author_id=raw_comment.get('channel_id', ''),
                            timestamp=ts,
                            likes=int(raw_comment.get('votes', 0)) if raw_comment.get('votes') else 0,
                            video_id=video_id,
                            video_title=video_title,
                            is_reply=bool(raw_comment.get('reply_count', 0) or False),
                            parent_comment_id=None,
                            language=language
                        )
                        
                        result_container['comments'].append(comment)
                        comment_count += 1
                        
                        # Log de progreso cada 10 comentarios
                        if comment_count % 10 == 0:
                            logger.debug(f"Progreso: {comment_count} comentarios extraídos")
                    
                    except Exception as e:
                        logger.debug(f"Error procesando comentario: {e}")
                        continue
                
                logger.info(
                    f"✅ Thread completado: {comment_count} comentarios extraídos, "
                    f"{filtered_count} descartados"
                )
            
            except Exception as e:
                logger.error(f"Error en thread de extracción: {e}")
        
        # Ejecutar en un thread separado con timeout
        try:
            thread = threading.Thread(target=extract_comments_thread, daemon=False)
            thread.start()
            thread.join(timeout=45)  # 45 segundos de timeout
            
            if thread.is_alive():
                logger.warning(f"⏱️  Thread timeout después de 45s")
                result_container['completed'] = True
                # El thread puede continuar en background, pero ya retornamos
        
        except Exception as e:
            logger.error(f"Error en thread management: {e}")
        
        return result_container['comments']
    
    def scrape_search_results(
        self,
        query: str,
        max_videos: int = 10,
        max_comments_per_video: int = 300,
        hours_back: int = 24
    ) -> tuple[List[Comment], ScraperStats]:
        """
        Workflow completo: buscar videos y extraer comentarios
        
        Args:
            query: Término de búsqueda
            max_videos: Máximo de videos a procesar
            max_comments_per_video: Máximo de comentarios por video
            hours_back: Solo videos de las últimas N horas
        
        Returns:
            (lista de comentarios, estadísticas)
        """
        stats = ScraperStats(start_time=datetime.now())
        all_comments = []
        
        try:
            # Buscar videos
            videos = self.search_videos(query, max_videos, hours_back)
            stats.videos_found = len(videos)
            
            if not videos:
                logger.warning(f"No se encontraron videos para: {query}")
                stats.end_time = datetime.now()
                return [], stats
            
            # Procesar cada video
            for video in videos[:max_videos]:
                try:
                    logger.info(f"Procesando video: {video.title} ({video.views:,} vistas)")
                    
                    # Extraer comentarios
                    comments = self.extract_comments(video.video_id, video.title)
                    all_comments.extend(comments)
                    
                    stats.videos_processed += 1
                    stats.comments_extracted += len(comments)
                
                except Exception as e:
                    error_msg = f"Error en video {video.video_id}: {str(e)}"
                    logger.error(error_msg)
                    stats.errors.append(error_msg)
            
            logger.info(f"🎉 Scraping completado: {stats.comments_extracted} comentarios totales")
        
        except Exception as e:
            error_msg = f"Error crítico en scraping: {str(e)}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
        
        finally:
            stats.end_time = datetime.now()
        
        return all_comments, stats
