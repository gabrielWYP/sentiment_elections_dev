import { useState } from 'react'
import styles from './ScraperForm.module.css'

function ScraperForm({ onExtract, loading }) {
  const [url, setUrl] = useState('')
  const [maxComments, setMaxComments] = useState(100)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!url.trim()) {
      alert('Por favor ingresa una URL de YouTube')
      return
    }
    onExtract(url, maxComments)
  }

  return (
    <div className={styles['scraper-form']}>
      <h2>📹 Extraer Comentarios de YouTube</h2>
      
      <form onSubmit={handleSubmit}>
        <div className={styles['form-group']}>
          <label htmlFor="url">URL del Video o Short:</label>
          <input
            type="text"
            id="url"
            placeholder="https://www.youtube.com/watch?v=xxxxx"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className={styles['form-row']}>
          <div className={styles['form-group']}>
            <label htmlFor="maxComments">Máximo de comentarios:</label>
            <input
              type="number"
              id="maxComments"
              min="1"
              max="1000"
              value={maxComments}
              onChange={(e) => setMaxComments(parseInt(e.target.value))}
              disabled={loading}
            />
          </div>
        </div>

        <button type="submit" className={styles['extract-button']} disabled={loading}>
          {loading ? (
            <>
              <span className={styles['loading']}></span> Extrayendo...
            </>
          ) : (
            '🚀 Extraer Comentarios'
          )}
        </button>
      </form>

      <div className={styles['info-box']}>
        <h3>ℹ️ Instrucciones</h3>
        <ul>
          <li>Ingresa el URL de un video o short de YouTube</li>
          <li>Define el máximo de comentarios a extraer (1-1000)</li>
          <li>Haz clic en "Extraer Comentarios"</li>
          <li>Los comentarios se limpiarán de emojis y URLs automáticamente</li>
        </ul>
      </div>

      <div className={styles['format-examples']}>
        <h3>📝 Formatos aceptados:</h3>
        <code>https://www.youtube.com/watch?v=XXXXXXXXX</code>
        <code>https://www.youtube.com/shorts/XXXXXXXXX</code>
      </div>
    </div>
  )
}

export default ScraperForm
