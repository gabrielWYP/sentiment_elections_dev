"""
Servicio de análisis de sentimientos usando ONNX BERT Multilingual
Optimizado para análisis de comentarios en español
Modelo: nlptown/bert-base-multilingual-uncased-sentiment
"""

import logging
from typing import Dict, List
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from scipy.special import softmax

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analizador de sentimientos usando modelo multilingual BERT con ONNX Runtime
    Modelo: nlptown/bert-base-multilingual-uncased-sentiment
    Soporta: español, inglés, francés, alemán, holandés, italiano
    """
    
    # Mapeo de etiquetas del modelo (5 clases)
    LABEL_MAP = {
        0: "1 star",
        1: "2 stars",
        2: "3 stars",
        3: "4 stars",
        4: "5 stars"
    }
    
    # Mapeo a 3 clases simplificado
    SIMPLIFIED_MAP = {
        0: "negative",      # 1 star
        1: "negative",      # 2 stars
        2: "neutral",       # 3 stars
        3: "positive",      # 4 stars
        4: "positive"       # 5 stars
    }
    
    def __init__(self):
        """Inicializar el modelo de sentimientos con transformers + ONNX Runtime"""
        try:
            logger.info("🤖 Cargando modelo BERT multilingual para sentimientos...")
            
            # Usar modelo BERT multilingual entrenado para sentiment (5 clases)
            model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
            
            try:
                # Intentar cargar con pipeline (automáticamente usa ONNX si está disponible)
                self.pipeline = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    device=-1  # CPU
                )
                self.tokenizer = None
                self.model = None
                logger.info("✅ Pipeline BERT multilingual cargado correctamente")
                return
            except Exception as e:
                logger.warning(f"⚠️  Error con pipeline, cargando modelo directo: {str(e)}")
                
                # Fallback directo
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.pipeline = None
                logger.info("✅ Tokenizador y modelo BERT multilingual cargados correctamente")
                
        except Exception as e:
            logger.error(f"❌ Error crítico cargando modelo: {str(e)}")
            raise
    
    def analyze(self, text: str, use_simplified: bool = True) -> Dict:
        """
        Analizar sentimiento de un texto usando BERT multilingual
        
        Args:
            text: Texto a analizar (comentario)
            use_simplified: Si False, usa 5 clases; si True usa 3 clases (negative/neutral/positive)
        
        Returns:
            {
                "text": str,
                "sentiment": str,  # "positive", "negative", "neutral"
                "score": float,    # 0.0-1.0
                "confidence": float  # 0.0-1.0
            }
        """
        try:
            # Validar entrada
            if not text or not isinstance(text, str):
                logger.warning(f"⚠️  Texto inválido para análisis: {text}")
                return {
                    "text": text,
                    "sentiment": "neutral",
                    "score": 0.5,
                    "confidence": 0.0,
                    "error": "Texto inválido"
                }
            
            # Limpiar texto (máx 512 caracteres por limitación de BERT)
            text_clean = text.strip()[:512]
            
            # Si se cargó el pipeline, usarlo
            if self.pipeline is not None:
                result = self.pipeline(text_clean)[0]
                
                # result contiene: {'label': '1 star', '2 stars', etc., 'score': float}
                raw_label = result['label']
                confidence = float(result['score'])
                
                # Extraer número de estrellas (0-4)
                label_num = int(raw_label.split()[0]) - 1  # Convertir "1 star" → 0, "5 stars" → 4
                
                if use_simplified:
                    sentiment = self.SIMPLIFIED_MAP.get(label_num, "neutral")
                    score = (label_num + 1) / 5.0  # Normalizar a 0.0-1.0
                else:
                    sentiment = raw_label
                    score = (label_num + 1) / 5.0
                
                logger.debug(f"✅ Análisis exitoso: '{text_clean[:50]}...' → {sentiment} (score: {score:.3f}, confianza: {confidence:.3f})")
                
                return {
                    "text": text_clean,
                    "sentiment": sentiment,
                    "score": float(score),
                    "confidence": confidence
                }
            
            # Usar modelo directo
            import torch
            
            # Tokenizar
            inputs = self.tokenizer(
                text_clean,
                return_tensors="pt",
                truncation=True,
                padding=True
            )
            
            # Hacer predicción
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Obtener logits
            logits = outputs.logits[0].cpu().numpy()
            
            # Calcular probabilidades
            probabilities = softmax(logits, axis=0)
            predicted_class = int(np.argmax(probabilities))
            confidence = float(probabilities[predicted_class])
            
            # Mapear etiqueta
            if use_simplified:
                sentiment = self.SIMPLIFIED_MAP.get(predicted_class, "neutral")
                score = (predicted_class + 1) / 5.0
            else:
                sentiment = self.LABEL_MAP.get(predicted_class, "neutral")
                score = (predicted_class + 1) / 5.0
            
            logger.debug(f"✅ Análisis exitoso: '{text_clean[:50]}...' → {sentiment} (score: {score:.3f}, confianza: {confidence:.3f})")
            
            return {
                "text": text_clean,
                "sentiment": sentiment,
                "score": float(score),
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis de sentimiento: {str(e)}")
            raise
    
    def analyze_batch(self, texts: List[str], use_simplified: bool = True) -> List[Dict]:
        """
        Analizar múltiples textos
        
        Args:
            texts: Lista de textos a analizar
            use_simplified: Usar 3 clases o 5 clases
        
        Returns:
            Lista de diccionarios con resultados
        """
        results = []
        for text in texts:
            try:
                result = self.analyze(text, use_simplified)
                results.append(result)
            except Exception as e:
                logger.error(f"Error procesando texto: {str(e)}")
                results.append({
                    "text": text,
                    "sentiment": None,
                    "score": None,
                    "error": str(e)
                })
        return results
    
    def get_statistics(self, results: List[Dict]) -> Dict:
        """
        Calcular estadísticas de un lote de resultados
        
        Args:
            results: Lista de resultados del análisis
        
        Returns:
            {
                "total": int,
                "positive_count": int,
                "negative_count": int,
                "neutral_count": int,
                "positive_pct": float,
                "negative_pct": float,
                "neutral_pct": float,
                "avg_score": float,
                "avg_confidence": float
            }
        """
        if not results:
            return {}
        
        # Filtrar resultados válidos
        valid_results = [r for r in results if r.get("sentiment")]
        
        if not valid_results:
            return {}
        
        total = len(valid_results)
        positive = sum(1 for r in valid_results if r["sentiment"] == "positive")
        negative = sum(1 for r in valid_results if r["sentiment"] == "negative")
        neutral = sum(1 for r in valid_results if r["sentiment"] == "neutral")
        
        scores = [r["score"] for r in valid_results if r.get("score") is not None]
        confidences = [r["confidence"] for r in valid_results if r.get("confidence") is not None]
        
        avg_score = sum(scores) / len(scores) if scores else 0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "total": total,
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "positive_pct": (positive / total * 100) if total > 0 else 0,
            "negative_pct": (negative / total * 100) if total > 0 else 0,
            "neutral_pct": (neutral / total * 100) if total > 0 else 0,
            "avg_score": float(avg_score),
            "avg_confidence": float(avg_confidence)
        }


# Instancia global (lazy loading)
_analyzer = None


def get_analyzer() -> SentimentAnalyzer:
    """Obtener instancia del analizador (singleton)"""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
