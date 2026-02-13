"""
Script de prueba para el analizador de sentimientos
Ejecutar: python backend/sentiment_analysis/test_sentiment.py
"""

import logging
import requests
import json
from sentiment_service import get_analyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_single_analysis():
    """Probar análisis de un comentario"""
    print("\n" + "="*70)
    print("TEST 1: Análisis de un comentario")
    print("="*70)
    
    analyzer = get_analyzer()
    
    # Comentarios de prueba
    test_comments = [
        "Me encanta este candidato, es increíble!",
        "Terrible, que decepción de política",
        "El candidato tiene buenos puntos",
        "No me interesa la política",
        "¡Qué asco de gobierno! Pésimo trabajo"
    ]
    
    for comment in test_comments:
        result = analyzer.analyze(comment)
        print(f"\n📝 Comentario: '{comment}'")
        print(f"   Sentimiento: {result['sentiment'].upper()}")
        print(f"   Score: {result['score']:.3f}")
        print(f"   Confianza: {result['confidence']:.3f}")
        print(f"   Raw Label: {result['raw_label']}")


def test_batch_analysis():
    """Probar análisis de múltiples comentarios"""
    print("\n" + "="*70)
    print("TEST 2: Análisis de lote (batch)")
    print("="*70)
    
    analyzer = get_analyzer()
    
    comments = [
        "El presidente está haciendo un buen trabajo",
        "No estoy de acuerdo con la política actual",
        "Es un tema complicado, hay pros y contras",
        "¡Increíble! Finalmente algo positivo",
        "Decepcionante, esperaba más"
    ]
    
    results = analyzer.analyze_batch(comments)
    stats = analyzer.get_statistics(results)
    
    print(f"\n📊 Resultados del Lote:")
    print(f"   Total de comentarios: {stats['total']}")
    print(f"   Positivos: {stats['positive_count']} ({stats['positive_pct']:.1f}%)")
    print(f"   Negativos: {stats['negative_count']} ({stats['negative_pct']:.1f}%)")
    print(f"   Neutrales: {stats['neutral_count']} ({stats['neutral_pct']:.1f}%)")
    print(f"   Score promedio: {stats['avg_score']:.3f}")
    print(f"   Confianza promedio: {stats['avg_confidence']:.3f}")
    
    print(f"\n📝 Detalles:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. [{result['sentiment'].upper()}] {result['text'][:50]}...")


def test_with_scraper():
    """Probar análisis con comentarios del scraper"""
    print("\n" + "="*70)
    print("TEST 3: Análisis con comentarios del Scraper (YouTube)")
    print("="*70)
    
    analyzer = get_analyzer()
    
    # URL del endpoint del scraper
    scraper_url = "http://localhost:5000/api/v1/get-comentarios"
    
    # Payload para obtener comentarios
    payload = {
        "url": "https://www.youtube.com/watch?v=1a-5P0BkUUU",
        "max_comments": 50,
        "language": "es"
    }
    
    print(f"\n🔗 Solicitando comentarios a: {scraper_url}")
    print(f"   Video: {payload['url']}")
    print(f"   Max comentarios: {payload['max_comments']}")
    
    try:
        # Hacer request al scraper
        response = requests.post(
            scraper_url,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Error en scraper: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return
        
        data = response.json()
        print(f"✅ Respuesta del scraper recibida")
        print(f"   Status: {data.get('status')}")
        
        # Extraer comentarios
        comments_data = data.get('comments', [])
        print(f"   Total comentarios obtenidos: {len(comments_data)}")
        
        # Filtrar comentarios válidos (no vacíos)
        valid_comments = [
            c.get('text') or c.get('comment_text') 
            for c in comments_data 
            if c.get('text') or c.get('comment_text')
        ]
        
        if not valid_comments:
            print("❌ No hay comentarios válidos para analizar")
            return
        
        print(f"   Analizando comentarios para encontrar 20 con confianza > 0.6...\n")
        
        # Analizar comentarios y filtrar por confianza > 0.6
        high_confidence_results = []
        for comment in valid_comments:
            if len(high_confidence_results) >= 20:
                break
            
            result = analyzer.analyze(comment)
            if result.get('confidence', 0) > 0.6:
                high_confidence_results.append(result)
        
        if not high_confidence_results:
            print("❌ No hay comentarios con confianza > 0.6")
            return
        
        print(f"✅ Se encontraron {len(high_confidence_results)} comentarios con confianza > 0.6\n")
        
        # Calcular estadísticas solo de los comentarios filtrados
        stats = analyzer.get_statistics(high_confidence_results)
        
        # Mostrar estadísticas
        print(f"📊 Resultados del Análisis:")
        print(f"   Total analizado: {stats['total']}")
        print(f"   Positivos: {stats['positive_count']} ({stats['positive_pct']:.1f}%)")
        print(f"   Negativos: {stats['negative_count']} ({stats['negative_pct']:.1f}%)")
        print(f"   Neutrales: {stats['neutral_count']} ({stats['neutral_pct']:.1f}%)")
        print(f"   Score promedio: {stats['avg_score']:.3f}")
        print(f"   Confianza promedio: {stats['avg_confidence']:.3f}")
        
        # Mostrar detalles de cada comentario
        print(f"📝 Comentarios (confianza > 0.6):")
        for i, result in enumerate(high_confidence_results, 1):
            text_preview = result['text'][:60].replace('\n', ' ')
            print(f"   {i}. [{result['sentiment'].upper()}] {text_preview}...")
            print(f"      Score: {result['score']:.3f} | Confianza: {result['confidence']:.3f}")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar a {scraper_url}")
        print("   ¿El servidor está corriendo en http://localhost:5000?")
        print("   Intenta con: python -m uvicorn backend.app:app --port 5000 --reload")
    except requests.exceptions.Timeout:
        print(f"❌ Timeout: La solicitud tardó demasiado")
    except json.JSONDecodeError:
        print(f"❌ Error procesando respuesta JSON")
        print(f"   Response: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    try:
        test_single_analysis()
        test_batch_analysis()
        test_with_scraper()
        print("\n" + "="*70)
        print("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("="*70 + "\n")
    except Exception as e:
        print(f"\n❌ ERROR EN TESTS: {str(e)}")
        import traceback
        traceback.print_exc()
        traceback.print_exc()
