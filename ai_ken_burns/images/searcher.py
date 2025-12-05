"""
Image searcher for AI Ken Burns.

Searches for images based on visual markers using various sources:
- Google Images (via scraping for fair use news images)
- Wikimedia Commons (fallback for historical images)
- Placeholder generation for testing
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional
from urllib.parse import quote_plus, urlparse

import httpx

from ai_ken_burns.config import get_config
from ai_ken_burns.script.models import VisualMarker
from ai_ken_burns.images.models import ImageResult
from ai_ken_burns.utils.logging_utils import get_logger, log_timing

logger = get_logger("ai_ken_burns.images")


class ImageSearcher:
    """
    Searches for images matching visual markers.

    Supports multiple image sources with fallback:
    1. Google Images - News and current images (fair use)
    2. Wikimedia Commons - Free historical images
    3. Placeholder - Generated placeholders for testing
    """

    # News sites for fair use
    NEWS_DOMAINS = [
        "reuters.com",
        "apnews.com",
        "nytimes.com",
        "washingtonpost.com",
        "theguardian.com",
        "bbc.com",
        "cnn.com",
        "npr.org",
        "pbs.org",
        "abcnews.go.com",
        "nbcnews.com",
        "cbsnews.com",
    ]

    def __init__(self) -> None:
        """Initialize the image searcher."""
        self.config = get_config()
        self.http_client = httpx.Client(
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            follow_redirects=True,
        )

    def search_for_marker(
        self,
        marker: VisualMarker,
        max_results: int = 5,
    ) -> list[ImageResult]:
        """
        Search for images matching a visual marker.

        Args:
            marker: VisualMarker with search terms and requirements
            max_results: Maximum results to return

        Returns:
            List of ImageResult objects
        """
        logger.info(f"Searching images for marker [{marker.id}]: {marker.description[:40]}...")

        results = []

        # Build search query from marker
        search_terms = marker.search_terms or [marker.description]

        # Try Google Images first
        google_results = self._search_google_images(search_terms, marker, max_results)
        results.extend(google_results)

        # If not enough results, try Wikimedia Commons
        if len(results) < max_results:
            remaining = max_results - len(results)
            wiki_results = self._search_wikimedia(search_terms, marker, remaining)
            results.extend(wiki_results)

        # If still not enough, add placeholders
        if len(results) < 1:
            placeholder = self._create_placeholder(marker)
            results.append(placeholder)

        logger.info(f"Found {len(results)} images for [{marker.id}]")
        return results

    def _search_google_images(
        self,
        search_terms: list[str],
        marker: VisualMarker,
        max_results: int,
    ) -> list[ImageResult]:
        """Search Google Images for news/current images."""
        results = []

        for term in search_terms[:2]:  # Limit to first 2 terms
            try:
                # Google Images search URL
                query = quote_plus(f"{term} news photo")
                url = f"https://www.google.com/search?q={query}&tbm=isch&tbs=isz:l"

                response = self.http_client.get(url)
                response.raise_for_status()
                html = response.text

                # Extract image URLs from the response
                # Look for data-src or src in img tags
                image_urls = self._extract_google_images(html)

                for img_url in image_urls[:max_results]:
                    if not img_url or len(img_url) < 20:
                        continue

                    # Check if from news site (for fair use)
                    is_news_source = any(
                        domain in img_url.lower()
                        for domain in self.NEWS_DOMAINS
                    )

                    result = ImageResult(
                        id=self._generate_id(img_url),
                        marker_id=marker.id,
                        source_url=img_url,
                        source_name="Google Images" + (" (News)" if is_news_source else ""),
                        title=term,
                        description=marker.description,
                        era=marker.era,
                        relevance_score=0.8 if is_news_source else 0.6,
                    )
                    results.append(result)

                    if len(results) >= max_results:
                        break

            except Exception as e:
                logger.debug(f"Google Images search error for '{term}': {e}")

            if len(results) >= max_results:
                break

        return results[:max_results]

    def _extract_google_images(self, html: str) -> list[str]:
        """Extract image URLs from Google Images HTML."""
        urls = []

        # Pattern for image URLs in Google's response
        # Google uses various patterns for embedding image data
        patterns = [
            r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|gif|webp)',
            r'"ou":"(https?://[^"]+)"',  # Original URL in JSON
            r'data-src="(https?://[^"]+)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                url = match if isinstance(match, str) else match
                # Filter out google's own URLs and small thumbnails
                if (
                    url
                    and "google" not in url.lower()
                    and "gstatic" not in url.lower()
                    and "encrypted-tbn" not in url
                    and len(url) > 30
                ):
                    urls.append(url)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls[:20]  # Limit results

    def _search_wikimedia(
        self,
        search_terms: list[str],
        marker: VisualMarker,
        max_results: int,
    ) -> list[ImageResult]:
        """Search Wikimedia Commons for images."""
        results = []

        for term in search_terms[:3]:  # Limit to first 3 terms
            try:
                query = quote_plus(term)
                url = (
                    f"https://commons.wikimedia.org/w/api.php?"
                    f"action=query&list=search&srsearch={query}%20filetype:image"
                    f"&srnamespace=6&srlimit={max_results}&format=json"
                )

                response = self.http_client.get(url)
                response.raise_for_status()
                data = response.json()

                for item in data.get("query", {}).get("search", []):
                    title = item.get("title", "")
                    if not title.startswith("File:"):
                        continue

                    # Get image info
                    image_info = self._get_wikimedia_image_info(title)
                    if not image_info:
                        continue

                    result = ImageResult(
                        id=self._generate_id(image_info["url"]),
                        marker_id=marker.id,
                        source_url=image_info["url"],
                        source_name="Wikimedia Commons",
                        title=title.replace("File:", ""),
                        description=item.get("snippet", ""),
                        width=image_info.get("width"),
                        height=image_info.get("height"),
                        era=marker.era,
                        relevance_score=0.7,
                    )
                    results.append(result)

                    if len(results) >= max_results:
                        break

            except Exception as e:
                logger.debug(f"Wikimedia search error for '{term}': {e}")

            if len(results) >= max_results:
                break

        return results[:max_results]

    def _get_wikimedia_image_info(self, title: str) -> Optional[dict]:
        """Get direct image URL and dimensions from Wikimedia."""
        try:
            query = quote_plus(title)
            url = (
                f"https://commons.wikimedia.org/w/api.php?"
                f"action=query&titles={query}&prop=imageinfo"
                f"&iiprop=url|size&format=json"
            )

            response = self.http_client.get(url)
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                imageinfo = page.get("imageinfo", [{}])[0]
                if "url" in imageinfo:
                    return {
                        "url": imageinfo["url"],
                        "width": imageinfo.get("width"),
                        "height": imageinfo.get("height"),
                    }

        except Exception as e:
            logger.debug(f"Error getting image info for {title}: {e}")

        return None

    def _create_placeholder(self, marker: VisualMarker) -> ImageResult:
        """Create a placeholder image result for testing."""
        placeholder_id = f"placeholder_{marker.id}"

        # Create placeholder URL (using placeholder.com or similar)
        text = quote_plus(marker.description[:30])
        placeholder_url = f"https://via.placeholder.com/1920x1080.png?text={text}"

        return ImageResult(
            id=placeholder_id,
            marker_id=marker.id,
            source_url=placeholder_url,
            source_name="Placeholder",
            title=f"Placeholder for {marker.id}",
            description=marker.description,
            width=1920,
            height=1080,
            era=marker.era,
            relevance_score=0.1,
        )

    def _generate_id(self, url: str) -> str:
        """Generate a unique ID from URL."""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def close(self) -> None:
        """Close HTTP client."""
        self.http_client.close()


def search_images(
    markers: list[VisualMarker],
    max_per_marker: int = 3,
) -> dict[str, list[ImageResult]]:
    """
    Convenience function to search images for multiple markers.

    Args:
        markers: List of VisualMarker objects
        max_per_marker: Maximum results per marker

    Returns:
        Dict mapping marker_id to list of ImageResult
    """
    searcher = ImageSearcher()
    results = {}

    try:
        for marker in markers:
            marker_results = searcher.search_for_marker(marker, max_per_marker)
            results[marker.id] = marker_results
    finally:
        searcher.close()

    return results
