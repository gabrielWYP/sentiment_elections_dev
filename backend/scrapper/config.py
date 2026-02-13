"""
Configuración del scraper de YouTube
"""

from pydantic_settings import BaseSettings
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
    
    # Partidos políticos a monitorear - Elecciones Perú 2026
    POLITICAL_PARTIES: dict = {
        "Renovación Popular": [
            "renovación popular",
            "rafael lópez aliaga",
            "rafael lopez aliaga",
            "alcalde lima",
        ],
        "Fuerza Popular": [
            "fuerza popular",
            "keiko fujimori",
            "fujimorismo",
            "votante fujimorista",
        ],
        "País Para Todos": [
            "país para todos",
            "pais para todos",
            "carlos álvarez",
            "carlos alvarez",
            "comediante político",
            "comediano político",
        ],
        "Ahora Nación": [
            "ahora nación",
            "ahora nacion",
            "alfonso lópez chau",
            "alfonso lopez chau",
            "rector uni",
            "universidad nacional de ingeniería",
            "centro-izquierda",
            "izquierda académica",
        ],
        "Perú Primero": [
            "perú primero",
            "peru primero",
            "mario vizcarra",
            "martín vizcarra",
            "martin vizcarra",
            "vizcarrismo",
        ],
        "Alianza para el Progreso": [
            "alianza para el progreso",
            "app perú",
            "app peru",
            "césar acuña",
            "cesar acuña",
            "cesar acuna",
        ],
        "Podemos Perú": [
            "podemos perú",
            "podemos peru",
            "josé luna gálvez",
            "jose luna galvez",
            "luna gálvez",
        ],
        "Somos Perú": [
            "somos perú",
            "somos peru",
            "george forsyth",
            "exalcalde la victoria",
            "alcalde la victoria",
        ],
        "Avanza País": [
            "avanza país",
            "avanza pais",
            "josé williams zapata",
            "jose williams zapata",
            "williams zapata",
            "expresidente congreso",
            "comando chavín de huántar",
            "comando chavin",
        ],
        "Partido Aprista Peruano": [
            "apra",
            "partido aprista peruano",
            "aprista",
            "jorge del castillo",
            "aprismo",
        ],
        "Perú Libre": [
            "perú libre",
            "peru libre",
            "vladimir cerrón",
            "vladimir cerron",
            "waldemar cerrón",
            "waldemar cerron",
            "pedro castillo",
            "castillismo",
        ],
        "Frente de la Esperanza": [
            "frente de la esperanza",
            "frente esperanza",
            "fernando olivera",
            "popy olivera",
            "popy",
        ],
    }
    
    # Configuración de rate limiting
    DELAY_BETWEEN_VIDEOS: float = 2.0        # Segundos entre procesamiento de videos
    DELAY_BETWEEN_SEARCHES: float = 5.0      # Segundos entre búsquedas
    MAX_RETRIES: int = 3                     # Reintentos en caso de error
    RETRY_DELAY: float = 10.0                # Segundos entre reintentos
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    model_config = {"env_file": ".env"}
    
    def get_party_keywords(self, party_name: str = None) -> List[str]:
        """
        Obtener palabras clave de un partido
        
        Args:
            party_name: Nombre del partido (ej: "Renovación Popular")
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
    
    def classify_comment_by_party(self, text: str) -> str:
        """
        Clasificar un comentario por partido político basado en palabras clave
        
        Args:
            text: Texto del comentario
        
        Returns:
            Nombre del partido o "Sin partido" si no coincide
        """
        text_lower = text.lower()
        
        for party, keywords in self.POLITICAL_PARTIES.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return party
        
        return "Sin partido"
    
    def get_all_parties(self) -> List[str]:
        """Obtener lista de todos los partidos monitoreados"""
        return list(self.POLITICAL_PARTIES.keys())


@lru_cache()
def get_scraper_settings() -> ScraperSettings:
    """Get scraper settings singleton"""
    return ScraperSettings()
