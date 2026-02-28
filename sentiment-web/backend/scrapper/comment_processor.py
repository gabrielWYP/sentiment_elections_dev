"""
Procesamiento y limpieza de comentarios
"""

import re
import logging
from typing import Optional
from langdetect import detect, DetectorFactory

# Para resultados consistentes
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)


class CommentProcessor:
    """Procesa y valida comentarios extraídos"""
    
    # Patrones de caracteres indeseados
    REMOVE_URLS = re.compile(r'http\S+|www.\S+')
    REMOVE_EMOJIS = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticones
        "\U0001F300-\U0001F5FF"  # símbolos y pictogramas
        "\U0001F680-\U0001F6FF"  # transporte y símbolos de mapa
        "\U0001F1E0-\U0001F1FF"  # banderas
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # dingbats
        "\u3030"
        "]+",
        re.UNICODE
    )
    
    MIN_LENGTH = 5  # Mínimo de caracteres
    MAX_LENGTH = 5000  # Máximo de caracteres
    
    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detectar idioma del comentario
        Retorna código de idioma ISO (ej: 'es', 'en')
        """
        try:
            lang = detect(text)
            return lang
        except Exception as e:
            logger.debug(f"Error detectando idioma: {e}")
            return "unknown"
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Limpiar texto del comentario
        - Elimina URLs
        - Elimina emojis
        - Normaliza espacios
        - Remove caracteres de control
        """
        # Eliminar URLs
        text = CommentProcessor.REMOVE_URLS.sub('', text)
        
        # Eliminar emojis
        text = CommentProcessor.REMOVE_EMOJIS.sub(r'', text)
        
        # Normalizar espacios (múltiples espacios → uno)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remover caracteres de control
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text
    
    @staticmethod
    def validate_comment(text: str, language: str = None) -> tuple[bool, Optional[str]]:
        """
        Validar si un comentario es apto
        
        Returns:
            (es_válido, texto_limpio)
        """
        # Limpiar texto
        cleaned = CommentProcessor.clean_text(text)
        
        # Validar longitud
        if len(cleaned) < CommentProcessor.MIN_LENGTH:
            return False, None
        
        if len(cleaned) > CommentProcessor.MAX_LENGTH:
            cleaned = cleaned[:CommentProcessor.MAX_LENGTH]
        
        # Validar idioma si es especificado
        if language and language != "es":
            return False, None
        
        # Validar que no sea solo números o caracteres especiales
        if not re.search(r'[a-záéíóúñ]', cleaned.lower()):
            return False, None
        
        return True, cleaned
    
    @staticmethod
    def extract_keywords(text: str, keywords: list[str]) -> list[str]:
        """
        Extrae palabras clave encontradas en el comentario
        (útil para asociar comentarios con partidos)
        """
        text_lower = text.lower()
        found = []
        
        for keyword in keywords:
            # Buscar palabra completa (con límites)
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found.append(keyword)
        
        return found
