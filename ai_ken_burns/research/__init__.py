"""
Research pipeline for AI Ken Burns.

Modules:
- news_fetcher: Fetch and filter news from RSS feeds
- historical_connector: Find historical parallels using LLM
- models: Data models for research output
"""

from ai_ken_burns.research.models import (
    NewsStory,
    HistoricalEvent,
    ResearchOutput,
)
from ai_ken_burns.research.news_fetcher import NewsFetcher, fetch_news
from ai_ken_burns.research.historical_connector import HistoricalConnector, find_historical_connection

__all__ = [
    "NewsStory",
    "HistoricalEvent",
    "ResearchOutput",
    "NewsFetcher",
    "fetch_news",
    "HistoricalConnector",
    "find_historical_connection",
]
