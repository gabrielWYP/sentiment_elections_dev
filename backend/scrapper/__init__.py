"""
Módulo de scraping de YouTube para Termómetro Político
"""

from .youtube_scraper import YouTubeScraper
from .comment_processor import CommentProcessor
from .models import Comment, YouTubeVideo, ScraperStats

__all__ = [
    'YouTubeScraper',
    'CommentProcessor',
    'Comment',
    'YouTubeVideo',
    'ScraperStats',
]
