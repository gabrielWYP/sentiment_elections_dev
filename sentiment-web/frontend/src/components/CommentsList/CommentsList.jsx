import styles from './CommentsList.module.css'

function CommentsList({ videoInfo, comments, onAnalyze, loading }) {
  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <div className={styles['comments-section']}>
      {videoInfo && (
        <div className={styles['video-info']}>
          <h2>{videoInfo.title}</h2>
          <div className={styles['video-meta']}>
            <span>📊 {videoInfo.count} comentarios extraídos</span>
            <span>⏱️ {videoInfo.executionTime.toFixed(2)}s</span>
          </div>
        </div>
      )}

      <button 
        className={styles['analyze-button']}
        onClick={onAnalyze}
        disabled={loading}
      >
        {loading ? (
          <>
            <span className={styles['loading']}></span> Analizando...
          </>
        ) : (
          '🤖 Analizar Sentimientos'
        )}
      </button>

      <div className={styles['comments-container']}>
        {comments.map((comment, index) => (
          <div key={index} className={styles['comment-card']}>
            <div className={styles['comment-header']}>
              <div className={styles['author-info']}>
                <strong className={styles['author']}>{comment.author}</strong>
                {comment.is_reply && <span className={styles['badge-reply']}>Respuesta</span>}
              </div>
              <span className={styles['date']}>{formatDate(comment.timestamp)}</span>
            </div>

            <p className={styles['comment-text']}>{comment.text}</p>

            <div className={styles['comment-footer']}>
              <span className={styles['likes']}>👍 {comment.likes} likes</span>
              {comment.sentiment && (
                <span className={`${styles['sentiment-label']} ${styles['sentiment-' + comment.sentiment]}`}>
                  {comment.sentiment === 'positive' && '😊 Positivo'}
                  {comment.sentiment === 'negative' && '😠 Negativo'}
                  {comment.sentiment === 'neutral' && '😐 Neutral'}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default CommentsList
