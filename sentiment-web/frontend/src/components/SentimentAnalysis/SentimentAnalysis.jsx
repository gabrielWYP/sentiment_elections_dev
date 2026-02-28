import styles from './SentimentAnalysis.module.css'

function SentimentAnalysis({ comments, stats, videoInfo }) {
  const getPercentage = (count) => {
    return stats.total > 0 ? ((count / stats.total) * 100).toFixed(1) : 0
  }

  const sentimentComments = {
    positive: comments.filter(c => c.sentiment === 'positive'),
    negative: comments.filter(c => c.sentiment === 'negative'),
    neutral: comments.filter(c => c.sentiment === 'neutral')
  }

  return (
    <div className={styles['sentiment-analysis']}>
      <h2>📊 Análisis de Sentimientos</h2>

      {videoInfo && (
        <div className={styles['video-title']}>
          <p><strong>{videoInfo.title}</strong></p>
          <p className={styles['video-subtitle']}>{stats.total} comentarios analizados</p>
        </div>
      )}

      {/* Estadísticas generales */}
      <div className={styles['stats-grid']}>
        <div className={`${styles['stat-card']} ${styles['total']}`}>
          <div className={styles['stat-number']}>{stats.total}</div>
          <div className={styles['stat-text']}>Total Comentarios</div>
        </div>

        <div className={`${styles['stat-card']} ${styles['positive']}`}>
          <div className={styles['stat-number']}>{stats.positive}</div>
          <div className={styles['stat-percentage']}>{getPercentage(stats.positive)}%</div>
          <div className={styles['stat-text']}>😊 Positivos</div>
        </div>

        <div className={`${styles['stat-card']} ${styles['negative']}`}>
          <div className={styles['stat-number']}>{stats.negative}</div>
          <div className={styles['stat-percentage']}>{getPercentage(stats.negative)}%</div>
          <div className={styles['stat-text']}>😠 Negativos</div>
        </div>

        <div className={`${styles['stat-card']} ${styles['neutral']}`}>
          <div className={styles['stat-number']}>{stats.neutral}</div>
          <div className={styles['stat-percentage']}>{getPercentage(stats.neutral)}%</div>
          <div className={styles['stat-text']}>😐 Neutros</div>
        </div>
      </div>

      {/* Gráfico de barras */}
      <div className={styles['chart-container']}>
        <h3>Distribución de Sentimientos</h3>
        <div className={styles['bar-chart']}>
          <div className={styles['bar-group']}>
            <div className={styles['bar-label']}>😊 Positivo</div>
            <div className={styles['bar-wrapper']}>
              <div 
                className={`${styles['bar']} ${styles['positive']}`}
                style={{width: `${getPercentage(stats.positive)}%`}}
              >
                <span className={styles['bar-text']}>{getPercentage(stats.positive)}%</span>
              </div>
            </div>
          </div>

          <div className={styles['bar-group']}>
            <div className={styles['bar-label']}>😠 Negativo</div>
            <div className={styles['bar-wrapper']}>
              <div 
                className={`${styles['bar']} ${styles['negative']}`}
                style={{width: `${getPercentage(stats.negative)}%`}}
              >
                <span className={styles['bar-text']}>{getPercentage(stats.negative)}%</span>
              </div>
            </div>
          </div>

          <div className={styles['bar-group']}>
            <div className={styles['bar-label']}>😐 Neutral</div>
            <div className={styles['bar-wrapper']}>
              <div 
                className={`${styles['bar']} ${styles['neutral']}`}
                style={{width: `${getPercentage(stats.neutral)}%`}}
              >
                <span className={styles['bar-text']}>{getPercentage(stats.neutral)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Resumen por sentimiento */}
      <div className={styles['sentiment-details']}>
        <div className={styles['detail-column']}>
          <h3>✅ Comentarios Positivos ({stats.positive})</h3>
          <div className={styles['sentiment-list']}>
            {sentimentComments.positive.slice(0, 5).map((comment, idx) => (
              <div key={idx} className={`${styles['sentiment-item']} ${styles['positive']}`}>
                <p className={styles['sentiment-text']}>{comment.text.substring(0, 100)}...</p>
                <span className={styles['author-badge']}>{comment.author}</span>
              </div>
            ))}
            {stats.positive > 5 && (
              <p className={styles['more-items']}>+{stats.positive - 5} comentarios más</p>
            )}
            {stats.positive === 0 && (
              <p className={styles['no-items']}>No hay comentarios positivos</p>
            )}
          </div>
        </div>

        <div className={styles['detail-column']}>
          <h3>❌ Comentarios Negativos ({stats.negative})</h3>
          <div className={styles['sentiment-list']}>
            {sentimentComments.negative.slice(0, 5).map((comment, idx) => (
              <div key={idx} className={`${styles['sentiment-item']} ${styles['negative']}`}>
                <p className={styles['sentiment-text']}>{comment.text.substring(0, 100)}...</p>
                <span className={styles['author-badge']}>{comment.author}</span>
              </div>
            ))}
            {stats.negative > 5 && (
              <p className={styles['more-items']}>+{stats.negative - 5} comentarios más</p>
            )}
            {stats.negative === 0 && (
              <p className={styles['no-items']}>No hay comentarios negativos</p>
            )}
          </div>
        </div>

        <div className={styles['detail-column']}>
          <h3>⚪ Comentarios Neutrales ({stats.neutral})</h3>
          <div className={styles['sentiment-list']}>
            {sentimentComments.neutral.slice(0, 5).map((comment, idx) => (
              <div key={idx} className={`${styles['sentiment-item']} ${styles['neutral']}`}>
                <p className={styles['sentiment-text']}>{comment.text.substring(0, 100)}...</p>
                <span className={styles['author-badge']}>{comment.author}</span>
              </div>
            ))}
            {stats.neutral > 5 && (
              <p className={styles['more-items']}>+{stats.neutral - 5} comentarios más</p>
            )}
            {stats.neutral === 0 && (
              <p className={styles['no-items']}>No hay comentarios neutrales</p>
            )}
          </div>
        </div>
      </div>

      {/* Conclusión */}
      <div className={styles['conclusion']}>
        <h3>📈 Conclusión</h3>
        <p>
          {stats.positive > stats.negative 
            ? `El sentimiento general es POSITIVO con ${getPercentage(stats.positive)}% de comentarios favorables.`
            : stats.negative > stats.positive
            ? `El sentimiento general es NEGATIVO con ${getPercentage(stats.negative)}% de comentarios críticos.`
            : `El sentimiento general es MIXTO con opiniones variadas.`
          }
        </p>
      </div>
    </div>
  )
}

export default SentimentAnalysis
