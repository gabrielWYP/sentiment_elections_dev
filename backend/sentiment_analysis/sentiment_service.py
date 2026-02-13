"""
Servicio de análisis de sentimientos usando ONNX Runtime
Optimizado para ARM64 sin PyTorch/TensorFlow
"""

import logging
from typing import Dict, List
import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np
from scipy.special import softmax

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analizador de sentimientos usando modelo multilingual BERT
    Modelo: nlptown/bert-base-multilingual-uncased-sentiment
    Soporta: español, inglés, francés, alemán, holandés, italiano
    """
    
    # Mapeo de etiquetas del modelo (5 clases)
    LABEL_MAP = {
        1: "very negative",
        2: "negative",
        3: "neutral",
        4: "positive",
        5: "very positive"
    }
    
    # Mapeo a 3 clases simplificado
    SIMPLIFIED_MAP = {
        1: "negative",      # very negative
        2: "negative",      # negative
        3: "neutral",       # neutral
        4: "positive",      # positive
        5: "positive"       # very positive
    }
    
    # Umbrales de confianza
    CONFIDENCE_THRESHOLD = 0.3
    
    def __init__(self):
        """Inicializar el modelo de sentimientos con ONNX Runtime"""
        try:
            logger.info("🤖 Cargando modelo ONNX para sentimientos...")
            
            # Usar modelo BERT multilingual entrenado para sentiment (5 clases)
            model_onnx = "nlptown/bert-base-multilingual-uncased-sentiment"
            
            # Descargar modelo ONNX y tokenizador
            from huggingface_hub import hf_hub_download
            
            try:
                # Intentar descargar modelo ONNX preconvertido
                model_path = hf_hub_download(
                    repo_id=model_onnx,
                    filename="onnx/model.onnx",
                    local_dir="models"
                )
            except Exception as e:
                logger.warning(f"⚠️  No hay ONNX preconvertido, usando pipeline tradicional")
                # Fallback a pipeline de transformers
                from transformers import pipeline
                self.pipeline = pipeline(
                    "sentiment-analysis",
                    model=model_onnx,
                    device=-1
                )
                self.tokenizer = None
                self.session = None
                logger.info("✅ Pipeline de sentimientos cargado correctamente")
                return
            
            # Cargar sesión ONNX
            self.session = ort.InferenceSession(model_path)
            self.pipeline = None
            
            # Obtener los inputs requeridos por el modelo
            self.input_names = [input.name for input in self.session.get_inputs()]
            logger.info(f"   Inputs requeridos: {self.input_names}")
            
            # Cargar tokenizador
            self.tokenizer = AutoTokenizer.from_pretrained(model_onnx)
            
            logger.info("✅ Modelo ONNX de sentimientos cargado correctamente")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {str(e)}")
            raise
    
    def analyze(self, text: str, use_simplified: bool = True) -> Dict:
        """
        Analizar sentimiento de un texto
        
        Args:
            text: Texto a analizar (comentario)
            use_simplified: Si False, usa 5 clases; si True usa 3 clases (negative/neutral/positive)
        
        Returns:
            {
                "text": str,
                "sentiment": str,  # "positive", "negative", "neutral"
                "score": float,    # 0.0-1.0
                "raw_label": str,  # "5 stars", "4 stars", etc.
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
                    "raw_label": None,
                    "confidence": 0.0,
                    "error": "Texto inválido"
                }
            
            # Limpiar texto (máx 512 caracteres por limitación de BERT)
            text_clean = text.strip()[:512]
            
            # Si se cargó el pipeline tradicional, usarlo
            if self.pipeline is not None:
                result = self.pipeline(text_clean)[0]
                
                # Mapear etiqueta a número (1-5)
                raw_label = result['label']  # '1 star', '5 stars', etc.
                label_num = int(raw_label.split()[0])
                confidence = float(result['score'])
                
                if use_simplified:
                    sentiment = self.SIMPLIFIED_MAP.get(label_num, "neutral")
                    score = (label_num - 1) / 4.0
                else:
                    sentiment = self.LABEL_MAP.get(label_num, "neutral")
                    score = (label_num - 1) / 4.0
                
                logger.debug(f"✅ Análisis exitoso: '{text_clean[:50]}...' → {sentiment} ({confidence:.3f})")
                
                return {
                    "text": text_clean,
                    "sentiment": sentiment,
                    "score": float(score),
                    "raw_label": raw_label,
                    "confidence": confidence
                }
            
            # Usar ONNX Runtime
            # Tokenizar
            inputs = self.tokenizer(
                text_clean,
                return_tensors="np",
                truncation=True,
                padding=True
            )
            
            # Construir inputs dinámicamente según lo que requiera el modelo
            ort_inputs = {}
            for input_name in self.input_names:
                if input_name == "input_ids":
                    ort_inputs[input_name] = inputs["input_ids"].astype(np.int64)
                elif input_name == "attention_mask":
                    ort_inputs[input_name] = inputs["attention_mask"].astype(np.int64)
                elif input_name == "token_type_ids":
                    ort_inputs[input_name] = inputs.get("token_type_ids", np.zeros_like(inputs["input_ids"])).astype(np.int64)
            
            # Hacer predicción con ONNX Runtime
            outputs = self.session.run(None, ort_inputs)
            
            # Obtener logits y calcular probabilidades
            logits = outputs[0]
            if logits.ndim > 1:
                logits = logits[0]
            
            logits = np.asarray(logits).flatten()
            probabilities = softmax(logits, axis=0)
            predicted_class = int(np.argmax(probabilities))
            confidence = float(probabilities.flat[predicted_class])
            
            # Mapear clase (0-4) a número de estrellas (1-5)
            label_num = predicted_class + 1
            raw_label = f"{label_num} {'star' if label_num == 1 else 'stars'}"
            
            # Convertir a 3 clases o mantener etiqueta original
            if use_simplified:
                sentiment = self.SIMPLIFIED_MAP.get(label_num, "neutral")
                score = (label_num - 1) / 4.0
            else:
                sentiment = self.LABEL_MAP.get(label_num, "neutral")
                score = (label_num - 1) / 4.0
            
            logger.debug(f"✅ Análisis exitoso: '{text_clean[:50]}...' → {sentiment} ({confidence:.3f})")
            
            return {
                "text": text_clean,
                "sentiment": sentiment,
                "score": float(score),
                "raw_label": raw_label,
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
        
        avg_score = np.mean([r["score"] for r in valid_results]) if valid_results else 0
        avg_confidence = np.mean([r["confidence"] for r in valid_results]) if valid_results else 0
        
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
