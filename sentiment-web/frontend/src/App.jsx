import { useState, useEffect } from 'react'
import axios from 'axios'
import ScraperForm from './components/ScraperForm/ScraperForm'
import CommentsList from './components/CommentsList/CommentsList'
import SentimentAnalysis from './components/SentimentAnalysis/SentimentAnalysis'
import './App.css'

//ci/cd

function App() {
  const [activeTab, setActiveTab] = useState('scraper')
  const [comments, setComments] = useState([])
  const [videoInfo, setVideoInfo] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState({ total: 0, positive: 0, negative: 0, neutral: 0 })

  // Función para extraer comentarios
  const handleExtractComments = async (url, maxComments) => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.post('/api/v1/get-comentarios', {
        url: url,
        max_comments: maxComments,
        language: 'es',
        content_type: 'auto'
      })

      setComments(response.data.comments)
      setVideoInfo({
        title: response.data.video_title,
        videoId: response.data.video_id,
        count: response.data.comments_extracted,
        executionTime: response.data.execution_time_seconds
      })
      setActiveTab('comments')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al extraer comentarios')
    } finally {
      setLoading(false)
    }
  }

  // Función para analizar sentimientos
  const handleAnalyzeSentiment = async () => {
    setLoading(true)
    setError(null)
    try {
      const commentTexts = comments.map(c => c.text)
      const response = await axios.post('/api/v1/analyze-sentiment', {
        texts: commentTexts,
        language: 'es'
      })

      // Actualizar comentarios con sentimientos
      const updatedComments = comments.map((comment, index) => ({
        ...comment,
        sentiment: response.data.sentiments[index]
      }))

      setComments(updatedComments)

      // Calcular stats
      const positive = updatedComments.filter(c => c.sentiment === 'positive').length
      const negative = updatedComments.filter(c => c.sentiment === 'negative').length
      const neutral = updatedComments.filter(c => c.sentiment === 'neutral').length

      setStats({
        total: updatedComments.length,
        positive,
        negative,
        neutral
      })

      setActiveTab('sentiment')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al analizar sentimientos')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-card">
          <h1 className="brand-title">
            <img src="/sensivoto.svg" alt="SentiVoto" className="brand-logo" />
            <span>Termómetro Político Perú 2026</span>
          </h1>
          <p className="subtitle">Análisis de sentimientos en comentarios de YouTube</p>
        </div>
      </header>

      <nav className="tabs">
        <button 
          className={`tab ${activeTab === 'scraper' ? 'active' : ''}`}
          onClick={() => setActiveTab('scraper')}
        >
          📹 Extraer Comentarios
        </button>
        <button 
          className={`tab ${activeTab === 'comments' ? 'active' : ''}`}
          onClick={() => setActiveTab('comments')}
          disabled={comments.length === 0}
        >
          💬 Comentarios ({comments.length})
        </button>
        <button 
          className={`tab ${activeTab === 'sentiment' ? 'active' : ''}`}
          onClick={() => setActiveTab('sentiment')}
          disabled={!stats.total}
        >
          📊 Análisis ({stats.total})
        </button>
      </nav>

      <main className="main-container">
        {error && (
          <div className="alert alert-error">
            ❌ {error}
          </div>
        )}

        {activeTab === 'scraper' && (
          <ScraperForm 
            onExtract={handleExtractComments}
            loading={loading}
          />
        )}

        {activeTab === 'comments' && comments.length > 0 && (
          <CommentsList 
            videoInfo={videoInfo}
            comments={comments}
            onAnalyze={handleAnalyzeSentiment}
            loading={loading}
          />
        )}

        {activeTab === 'sentiment' && stats.total > 0 && (
          <SentimentAnalysis 
            comments={comments}
            stats={stats}
            videoInfo={videoInfo}
          />
        )}

        {activeTab === 'comments' && comments.length === 0 && (
          <div className="no-data">
            No hay comentarios para mostrar. Extrae comentarios primero.
          </div>
        )}

        {activeTab === 'sentiment' && stats.total === 0 && (
          <div className="no-data">
            No hay análisis disponible. Analiza sentimientos primero.
          </div>
        )}
      </main>

      <footer className="footer">
        <p>API Status: <span className="status-dot online"></span> Online</p>
      </footer>
    </div>
  )
}

export default App
