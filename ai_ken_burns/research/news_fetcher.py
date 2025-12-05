"""
News fetcher for AI Ken Burns.

Fetches news from RSS feeds and filters for class consciousness relevance.
Uses keyword matching and optional LLM analysis for relevance scoring.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree

import httpx

from ai_ken_burns.config import get_config
from ai_ken_burns.utils.logging_utils import get_research_logger, log_timing
from ai_ken_burns.research.models import NewsStory

logger = get_research_logger()

# Default relevance keywords for class consciousness topics
DEFAULT_KEYWORDS = [
    # Labor
    "union", "strike", "workers", "labor", "wages", "layoffs", "unemployment",
    "gig economy", "minimum wage", "collective bargaining",
    # Economic inequality
    "inequality", "wealth gap", "billionaire", "poverty", "cost of living",
    "inflation", "housing crisis", "rent", "eviction", "homeless",
    # Corporate power
    "corporate", "monopoly", "antitrust", "ceo pay", "stock buyback",
    "privatization", "deregulation",
    # Social issues
    "healthcare", "education", "student debt", "prison", "immigration",
    # Activism
    "protest", "activist", "grassroots", "organizing", "solidarity",
]


class NewsFetcher:
    """
    Fetches and filters news from RSS feeds.

    Scores stories for relevance to class consciousness themes using
    keyword matching and configurable filters.
    """

    def __init__(
        self,
        rss_url: Optional[str] = None,
        keywords: Optional[list[str]] = None,
    ) -> None:
        """
        Initialize the news fetcher.

        Args:
            rss_url: RSS feed URL (defaults to config)
            keywords: Relevance keywords (defaults to config + defaults)
        """
        self.config = get_config()
        self.rss_url = rss_url or self.config.research.news_rss_url

        # Combine default keywords with config keywords
        config_keywords = self.config.research.relevance_keywords or []
        self.keywords = keywords or list(set(DEFAULT_KEYWORDS + config_keywords))

        # Compile keyword patterns for efficient matching
        self._keyword_patterns = [
            re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            for kw in self.keywords
        ]

    def fetch_feed(self, timeout: int = 30) -> list[NewsStory]:
        """
        Fetch stories from the RSS feed.

        Args:
            timeout: Request timeout in seconds

        Returns:
            List of NewsStory objects
        """
        logger.info(f"Fetching news from {self.rss_url}")

        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(self.rss_url)
                response.raise_for_status()

            return self._parse_rss(response.text)

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching RSS: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching RSS: {e}")
            return []

    def _parse_rss(self, xml_content: str) -> list[NewsStory]:
        """Parse RSS XML into NewsStory objects."""
        stories = []

        try:
            root = ElementTree.fromstring(xml_content)

            # Handle both RSS 2.0 and Atom feeds
            items = root.findall(".//item")  # RSS 2.0
            if not items:
                # Try Atom format
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                items = root.findall(".//atom:entry", ns)

            for item in items:
                story = self._parse_item(item)
                if story:
                    stories.append(story)

            logger.info(f"Parsed {len(stories)} stories from feed")

        except ElementTree.ParseError as e:
            logger.error(f"Failed to parse RSS XML: {e}")

        return stories

    def _parse_item(self, item: ElementTree.Element) -> Optional[NewsStory]:
        """Parse a single RSS item into a NewsStory."""
        try:
            # RSS 2.0 format
            title = self._get_text(item, "title")
            summary = self._get_text(item, "description") or self._get_text(item, "summary")
            link = self._get_text(item, "link")
            pub_date = self._get_text(item, "pubDate")
            source = self._get_text(item, "source") or ""

            # Try Atom format if RSS fields empty
            if not title:
                title = self._get_text(item, "{http://www.w3.org/2005/Atom}title")
            if not summary:
                summary = self._get_text(item, "{http://www.w3.org/2005/Atom}summary")
            if not link:
                link_elem = item.find("{http://www.w3.org/2005/Atom}link")
                if link_elem is not None:
                    link = link_elem.get("href", "")

            if not title or not link:
                return None

            # Parse publication date
            published = None
            if pub_date:
                published = self._parse_date(pub_date)

            # Clean HTML from summary
            if summary:
                summary = self._clean_html(summary)

            return NewsStory(
                title=title,
                summary=summary or "",
                link=link,
                published=published,
                source=source,
            )

        except Exception as e:
            logger.debug(f"Failed to parse item: {e}")
            return None

    def _get_text(self, element: ElementTree.Element, tag: str) -> str:
        """Get text content of a child element."""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return ""

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats from RSS feeds."""
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 822
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        # Remove HTML tags
        clean = re.sub(r"<[^>]+>", "", text)
        # Decode common entities
        clean = clean.replace("&amp;", "&")
        clean = clean.replace("&lt;", "<")
        clean = clean.replace("&gt;", ">")
        clean = clean.replace("&quot;", '"')
        clean = clean.replace("&#39;", "'")
        clean = clean.replace("&nbsp;", " ")
        # Normalize whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def score_relevance(self, story: NewsStory) -> NewsStory:
        """
        Score a story's relevance to class consciousness themes.

        Updates the story with relevance_score, relevance_keywords, and themes.

        Args:
            story: NewsStory to score

        Returns:
            Updated NewsStory with relevance scoring
        """
        text = f"{story.title} {story.summary}".lower()
        matched_keywords = []

        for i, pattern in enumerate(self._keyword_patterns):
            if pattern.search(text):
                matched_keywords.append(self.keywords[i])

        # Calculate relevance score
        # Weight title matches more heavily
        title_lower = story.title.lower()
        title_matches = sum(1 for kw in matched_keywords if kw.lower() in title_lower)
        body_matches = len(matched_keywords) - title_matches

        # Score: title matches worth 2x, normalized to 0-1
        raw_score = (title_matches * 2 + body_matches) / (len(self.keywords) * 0.5)
        score = min(1.0, raw_score)

        # Identify themes
        themes = self._identify_themes(matched_keywords)

        story.relevance_score = score
        story.relevance_keywords = matched_keywords
        story.themes = themes

        return story

    def _identify_themes(self, keywords: list[str]) -> list[str]:
        """Map matched keywords to broader themes."""
        theme_map = {
            "labor": ["union", "strike", "workers", "labor", "wages", "collective bargaining"],
            "economic_inequality": ["inequality", "wealth gap", "billionaire", "poverty", "cost of living"],
            "housing": ["housing crisis", "rent", "eviction", "homeless"],
            "corporate_power": ["corporate", "monopoly", "antitrust", "ceo pay", "privatization"],
            "social_services": ["healthcare", "education", "student debt"],
            "activism": ["protest", "activist", "grassroots", "organizing", "solidarity"],
        }

        themes = set()
        keywords_lower = [kw.lower() for kw in keywords]

        for theme, theme_keywords in theme_map.items():
            for kw in theme_keywords:
                if kw in keywords_lower:
                    themes.add(theme)
                    break

        return list(themes)

    def filter_by_topic(
        self,
        stories: list[NewsStory],
        topic: Optional[str] = None,
    ) -> list[NewsStory]:
        """
        Filter stories by a specific topic.

        Args:
            stories: List of stories to filter
            topic: Topic keyword to filter by (optional)

        Returns:
            Filtered list of stories
        """
        if not topic:
            return stories

        topic_lower = topic.lower()
        filtered = []

        for story in stories:
            text = f"{story.title} {story.summary}".lower()
            if topic_lower in text:
                filtered.append(story)

        logger.info(f"Topic filter '{topic}': {len(filtered)}/{len(stories)} stories")
        return filtered

    def get_top_stories(
        self,
        topic: Optional[str] = None,
        min_relevance: float = 0.1,
        max_stories: int = 5,
    ) -> list[NewsStory]:
        """
        Fetch, score, and return top relevant stories.

        Args:
            topic: Optional topic filter
            min_relevance: Minimum relevance score
            max_stories: Maximum stories to return

        Returns:
            List of top scored NewsStory objects
        """
        with log_timing("fetch_news", logger):
            stories = self.fetch_feed()

        if not stories:
            logger.warning("No stories fetched from feed")
            return []

        # Score all stories
        with log_timing("score_relevance", logger):
            scored = [self.score_relevance(story) for story in stories]

        # Filter by topic if specified
        if topic:
            scored = self.filter_by_topic(scored, topic)

        # Filter by minimum relevance
        relevant = [s for s in scored if s.relevance_score >= min_relevance]

        # Sort by relevance score
        relevant.sort(key=lambda s: s.relevance_score, reverse=True)

        # Return top stories
        top = relevant[:max_stories]

        logger.info(
            f"Found {len(relevant)} relevant stories "
            f"(min_relevance={min_relevance}), returning top {len(top)}"
        )

        return top


def fetch_news(
    topic: Optional[str] = None,
    max_stories: int = 5,
) -> list[NewsStory]:
    """
    Convenience function to fetch and score news.

    Args:
        topic: Optional topic filter
        max_stories: Maximum stories to return

    Returns:
        List of top scored NewsStory objects
    """
    fetcher = NewsFetcher()
    return fetcher.get_top_stories(topic=topic, max_stories=max_stories)
