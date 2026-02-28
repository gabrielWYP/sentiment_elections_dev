"""
Cliente HTTP para conectarse al servicio de sentimientos remoto
Maneja conexión, reconexión y fallback a análisis local si es necesario
"""

import logging
import httpx
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SentimentServiceClient:
    """Cliente para llamar al microservicio de sentimientos"""
    
    def __init__(self, 
                 service_url: Optional[str] = None,
                 timeout: float = 30.0,
                 fallback_to_local: bool = True):
        """
        Args:
            service_url: URL del servicio (ej: http://sentiment-service:8001)
            timeout: Timeout en segundos para requests
            fallback_to_local: Si True y el servicio falla, usa análisis local
        """
        self.service_url = service_url or os.getenv(
            'SENTIMENT_SERVICE_URL', 
            'http://localhost:8001'
        )
        self.timeout = timeout
        self.fallback_to_local = fallback_to_local
        self.is_healthy = False
        self.last_health_check = None
        self.health_check_interval = 30  # segundos
        
        logger.info(f"🔌 SentimentServiceClient inicializado: {self.service_url}")
    
    async def check_health(self) -> bool:
        """Verificar si el servicio está disponible"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.service_url}/health")
                self.is_healthy = response.status_code == 200
                self.last_health_check = datetime.now()
                
                if self.is_healthy:
                    logger.info("✅ Sentiment Service está HEALTHY")
                else:
                    logger.warning(f"⚠️  Sentiment Service respondió con {response.status_code}")
                
                return self.is_healthy
        except Exception as e:
            logger.warning(f"⚠️  Error verificando salud del servicio: {str(e)}")
            self.is_healthy = False
            return False
    
    async def analyze_sentiment(self, 
                               texts: List[str], 
                               use_simplified: bool = True) -> Dict:
        """
        Analizar sentimiento de textos usando el servicio remoto
        
        Args:
            texts: Lista de comentarios a analizar
            use_simplified: Usar 3 clases o 5 clases
        
        Returns:
            {
                "sentiments": ["positive", "negative", ...],
                "scores": [0.8, 0.6, ...],
                "confidences": [0.95, 0.87, ...],
                "service": "remote" | "local" | "error"
            }
        """
        
        # Verificar salud periódicamente
        if not self.last_health_check or \
           (datetime.now() - self.last_health_check).seconds > self.health_check_interval:
            await self.check_health()
        
        # Si el servicio está healthy, usar remoto
        if self.is_healthy:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.service_url}/analyze",
                        json={
                            "texts": texts,
                            "use_simplified": use_simplified
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"✅ Análisis remoto exitoso para {len(texts)} textos")
                        return {
                            "sentiments": data["sentiments"],
                            "scores": data["scores"],
                            "confidences": data["confidences"],
                            "service": "remote"
                        }
                    else:
                        logger.error(f"❌ Sentiment Service error {response.status_code}")
                        self.is_healthy = False
                        return await self._fallback_analysis(texts, use_simplified)
                        
            except httpx.TimeoutException:
                logger.warning("⏱️  Timeout al conectar con Sentiment Service")
                self.is_healthy = False
                return await self._fallback_analysis(texts, use_simplified)
            except Exception as e:
                logger.error(f"❌ Error llamando Sentiment Service: {str(e)}")
                self.is_healthy = False
                return await self._fallback_analysis(texts, use_simplified)
        
        # Si no está healthy, usar fallback
        return await self._fallback_analysis(texts, use_simplified)
    
    async def _fallback_analysis(self, 
                                texts: List[str], 
                                use_simplified: bool) -> Dict:
        """Analizar localmente si el servicio no está disponible"""
        if not self.fallback_to_local:
            logger.error("❌ Sentiment Service no disponible y fallback deshabilitado")
            raise Exception("Sentiment Service no disponible")
        
        logger.warning("⚠️  Usando análisis local (fallback)")
        
        try:
            from backend.sentiment_analysis.sentiment_service import get_analyzer
            analyzer = get_analyzer()
            results = analyzer.analyze_batch(texts, use_simplified)
            
            return {
                "sentiments": [r["sentiment"] for r in results],
                "scores": [r["score"] for r in results],
                "confidences": [r["confidence"] for r in results],
                "service": "local"
            }
        except Exception as e:
            logger.error(f"❌ Error en análisis local: {str(e)}")
            raise


# Cliente global (singleton)
_client: Optional[SentimentServiceClient] = None

def get_sentiment_client() -> SentimentServiceClient:
    """Obtener instancia del cliente (singleton)"""
    global _client
    if _client is None:
        _client = SentimentServiceClient()
    return _client
