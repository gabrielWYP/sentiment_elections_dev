import os
import logging
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Logging ci/cd
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURACIÓN DE ENTORNO
# ==========================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development | production
MODEL_QUANTIZED = ENVIRONMENT == "production"

# Seleccionar directorio del modelo
if MODEL_QUANTIZED:
    MODEL_DIR = "./modelo_onnx/modelo_quantized"
    logger.info("🔴 Entorno: PRODUCTION - Modelo CUANTIZADO (164MB)")
else:
    MODEL_DIR = "./modelo_onnx/modelo_normal"
    logger.info("🟢 Entorno: DEVELOPMENT - Modelo NORMAL (642MB)")

# ==========================================
# 1. MOTOR DE INFERENCIA ONNX
# ==========================================
class ONNXSentimentAnalyzer:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        
        model_path = os.path.join(self.model_dir, "model.onnx")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo ONNX no encontrado: {model_path}")
            
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        logger.info(f"✅ Modelo ONNX cargado: {model_path}")

    def analyze_batch(self, texts: List[str], use_simplified: bool = True) -> List[dict]:
        inputs = self.tokenizer(
            texts, 
            return_tensors="np", 
            padding=True, 
            truncation=True, 
            max_length=512
        )
        
        onnx_inputs = {
            "input_ids": inputs["input_ids"],
            "attention_mask": inputs["attention_mask"]
        }
        if "token_type_ids" in inputs:
            onnx_inputs["token_type_ids"] = inputs["token_type_ids"]

        logits = self.session.run(None, onnx_inputs)[0]
        
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probabilities = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        
        predicted_indices = np.argmax(probabilities, axis=1)
        confidences = np.max(probabilities, axis=1)

        results = []
        for i, text in enumerate(texts):
            pred_idx = int(predicted_indices[i])
            conf = float(confidences[i])
            
            if use_simplified:
                if pred_idx in [0, 1]:
                    sentiment = "negative"
                    score = 0.0 + (pred_idx * 0.25) 
                elif pred_idx == 2:
                    sentiment = "neutral"
                    score = 0.5
                else:
                    sentiment = "positive"
                    score = 0.75 + ((pred_idx - 3) * 0.25)
            else:
                sentiment = f"{pred_idx + 1} stars"
                score = (pred_idx + 1) / 5.0

            results.append({
                "text": text,
                "sentiment": sentiment,
                "score": score,
                "confidence": conf
            })
            
        return results

# ==========================================
# 2. MODELOS PYDANTIC Y FASTAPI
# ==========================================
class AnalyzeRequest(BaseModel):
    texts: List[str]
    use_simplified: bool = True

class SentimentResult(BaseModel):
    text: str
    sentiment: str
    score: float
    confidence: float

class AnalyzeResponse(BaseModel):
    sentiments: List[str]
    scores: List[float]
    confidences: List[float]
    results: List[SentimentResult]

analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global analyzer
    try:
        logger.info("🚀 Iniciando sentiment-service...")
        logger.info(f"📥 Cargando modelo desde: {MODEL_DIR}")
        analyzer = ONNXSentimentAnalyzer(model_dir=MODEL_DIR)
        logger.info("✅ Modelo cargado y listo")
    except Exception as e:
        logger.error(f"❌ Error crítico al cargar modelo: {str(e)}")
        raise
    yield
    logger.info("🛑 Deteniendo sentiment-service")

app = FastAPI(
    title="Sentiment Analysis ONNX Service",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "sentiment-analysis-onnx",
        "model_loaded": analyzer is not None
    }

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_sentiment(request: AnalyzeRequest):
    if not analyzer:
        raise HTTPException(status_code=503, detail="Modelo no disponible")
    
    if not request.texts:
        raise HTTPException(status_code=400, detail="Textos vacíos")
    
    try:
        results = analyzer.analyze_batch(request.texts, use_simplified=request.use_simplified)
        
        sentiments = [r["sentiment"] for r in results]
        scores = [r["score"] for r in results]
        confidences = [r["confidence"] for r in results]
        
        return AnalyzeResponse(
            sentiments=sentiments,
            scores=scores,
            confidences=confidences,
            results=[SentimentResult(**r) for r in results]
        )
    except Exception as e:
        logger.error(f"❌ Error procesando batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=False, log_level="info")