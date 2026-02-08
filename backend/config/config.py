"""
Configuración centralizada de la aplicación
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # ===== APPLICATION =====
    app_name: str = "Termómetro Político Perú 2026"
    app_mode: str = os.getenv('APP_MODE', 'DEVELOPMENT')
    debug: bool = app_mode == 'DEVELOPMENT'
    version: str = "1.0.0"
    
    # ===== SERVER =====
    host_dev: str = "127.0.0.1"
    port_dev: int = 5000
    host_prod: str = "0.0.0.0"
    port_prod: int = 8000
    reload: bool = debug
    
    # ===== DATABASE =====
    oracle_user: str = os.getenv('ORACLE_USER', 'admin')
    oracle_password: str = os.getenv('ORACLE_PASSWORD', '')
    oracle_connection_string: str = os.getenv('ORACLE_CONNECTION_STRING', '')
    
    # ===== SCRAPER =====
    scraper_enabled: bool = os.getenv('SCRAPER_ENABLED', 'True') == 'True'
    scraper_schedule_hours: int = int(os.getenv('SCRAPER_SCHEDULE_HOURS', '6'))
    
    # ===== SENTIMENT ANALYSIS =====
    sentiment_model: str = "nlptown/bert-base-multilingual-uncased-sentiment"
    use_onnx: bool = True  # Usar ONNX Runtime en lugar de PyTorch
    
    # ===== LOGGING =====
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_file: str = os.getenv('LOG_FILE', 'logs/app.log')
    
    # ===== CORS =====
    cors_origins: list = ["*"] if debug else ["localhost", "127.0.0.1"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    """Obtener configuración (cached)"""
    return Settings()


# Instancia global de configuración
settings = get_settings()

#ci/cd
