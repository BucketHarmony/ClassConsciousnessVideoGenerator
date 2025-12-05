"""
Image pipeline for AI Ken Burns.

Modules:
- models: Data models for image metadata
- searcher: Image search using various APIs
- manager: Download, cache, and manage images
- ai_generator: DALL-E image generation
"""

from ai_ken_burns.images.models import ImageResult, ImageCollection
from ai_ken_burns.images.searcher import ImageSearcher, search_images
from ai_ken_burns.images.manager import ImageManager
from ai_ken_burns.images.ai_generator import AIImageGenerator, generate_ai_image

__all__ = [
    "ImageResult",
    "ImageCollection",
    "ImageSearcher",
    "search_images",
    "ImageManager",
    "AIImageGenerator",
    "generate_ai_image",
]
