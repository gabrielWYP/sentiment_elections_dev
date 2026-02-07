"""
Configuración del scraper de YouTube
"""

from pydantic import BaseSettings
from typing import List
import os
from functools import lru_cache


class ScraperSettings(BaseSettings):
    """
    Configuración del scraper de YouTube
    Carga variables desde .env
    """
    
    # Búsqueda de videos
    SEARCH_QUERIES: List[str] = [
        "elecciones generales 2026 peru",
        "candidatos presidenciales peru 2026",
        "campaña electoral peru 2026",
    ]
    
    # Filtros de videos
    MAX_VIDEOS_PER_SEARCH: int = 10          # Máximo videos a procesar por búsqueda
    HOURS_BACK: int = 24                     # Solo videos de las últimas N horas
    MIN_VIDEO_VIEWS: int = 1000              # Mínimo de vistas para procesar
    
    # Extracción de comentarios
    MAX_COMMENTS_PER_VIDEO: int = 300        # Máximo comentarios a extraer
    MIN_COMMENT_LENGTH: int = 5              # Caracteres mínimos
    MAX_COMMENT_LENGTH: int = 5000           # Caracteres máximos
    
    # Idioma
    ALLOWED_LANGUAGES: List[str] = ["es"]    # Solo español
    
    # Partidos políticos a monitorear (será actualizado por el usuario)
    POLITICAL_PARTIES: dict = {
        "Peru Libre": [
            "pedro castillo",
            "peru libre",
            "vladimir cerrón",
            "junín",
        ],
        "Fuerza Popular": [
            "keiko fujimori",
            "fuerza popular",
            "vargas llosa",
        ],
        "Juntos por el Perú": [
            "vladimiro montesinos",
            "juntos por el peru",
        ],
        "Acción Popular": [
            "acción popular",
            "escritorio político",
        ],
    }
    
    # Configuración de rate limiting
    DELAY_BETWEEN_VIDEOS: float = 2.0        # Segundos entre procesamiento de videos
    DELAY_BETWEEN_SEARCHES: float = 5.0      # Segundos entre búsquedas
    MAX_RETRIES: int = 3                     # Reintentos en caso de error
    RETRY_DELAY: float = 10.0                # Segundos entre reintentos
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_party_keywords(self, party_name: str = None) -> List[str]:
        """
        Obtener palabras clave de un partido
        
        Args:
            party_name: Nombre del partido (ej: "Peru Libre")
                       Si es None, retorna todas las palabras clave
        
        Returns:
            Lista de palabras clave
        """
        if party_name:
            return self.POLITICAL_PARTIES.get(party_name, [])
        
        # Retornar todas las palabras clave
        all_keywords = []
        for keywords in self.POLITICAL_PARTIES.values():
            all_keywords.extend(keywords)
        
        return all_keywords


@lru_cache()
def get_scraper_settings() -> ScraperSettings:
    """Get scraper settings singleton"""
    return ScraperSettings()
