"""
Unit tests for research pipeline.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestNewsFetcher:
    """Tests for NewsFetcher class."""

    def test_keyword_scoring(self):
        """Test relevance keyword scoring."""
        from ai_ken_burns.research.news_fetcher import NewsFetcher
        from ai_ken_burns.research.models import NewsStory

        fetcher = NewsFetcher()
        story = NewsStory(
            title="Union Workers Strike for Better Wages",
            summary="The labor movement continues as workers demand fair pay.",
            link="https://example.com/news",
            source="Test",
        )

        scored = fetcher.score_relevance(story)
        assert scored.relevance_score > 0
        assert len(scored.relevance_keywords) > 0
        assert "labor" in scored.themes or "activism" in scored.themes

    def test_theme_identification(self):
        """Test theme identification from keywords."""
        from ai_ken_burns.research.news_fetcher import NewsFetcher

        fetcher = NewsFetcher()
        keywords = ["union", "strike", "workers"]
        themes = fetcher._identify_themes(keywords)

        assert "labor" in themes

    def test_topic_filtering(self):
        """Test topic-based story filtering."""
        from ai_ken_burns.research.news_fetcher import NewsFetcher
        from ai_ken_burns.research.models import NewsStory

        fetcher = NewsFetcher()
        stories = [
            NewsStory(
                title="Workers Strike",
                summary="Labor dispute",
                link="https://example.com/1",
                source="Test",
            ),
            NewsStory(
                title="Stock Market News",
                summary="Markets rise",
                link="https://example.com/2",
                source="Test",
            ),
        ]

        filtered = fetcher.filter_by_topic(stories, "workers")
        assert len(filtered) == 1
        assert "Workers" in filtered[0].title

    @patch("ai_ken_burns.research.news_fetcher.httpx.Client")
    def test_rss_parsing(self, mock_client):
        """Test RSS XML parsing."""
        from ai_ken_burns.research.news_fetcher import NewsFetcher

        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test Story</title>
                    <description>Test description</description>
                    <link>https://example.com/test</link>
                </item>
            </channel>
        </rss>
        """

        mock_response = MagicMock()
        mock_response.text = rss_xml
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client.return_value = mock_client_instance

        fetcher = NewsFetcher()
        stories = fetcher.fetch_feed()

        assert len(stories) == 1
        assert stories[0].title == "Test Story"


class TestHistoricalConnector:
    """Tests for HistoricalConnector class."""

    def test_prompt_building(self, sample_news_story):
        """Test prompt generation for LLM."""
        from ai_ken_burns.research.historical_connector import HistoricalConnector

        connector = HistoricalConnector()
        prompt = connector._build_prompt(sample_news_story)

        assert sample_news_story.title in prompt
        assert "historical" in prompt.lower()

    @patch("ai_ken_burns.research.historical_connector.get_openai_client")
    def test_connection_parsing(self, mock_get_client, sample_news_story):
        """Test parsing of LLM response."""
        from ai_ken_burns.research.historical_connector import HistoricalConnector
        from ai_ken_burns.clients.openai_client import APIResponse

        mock_client = MagicMock()
        mock_response = APIResponse(
            success=True,
            content="{}",
            data={
                "historical_event": {
                    "name": "Pullman Strike",
                    "year": 1894,
                    "summary": "A major labor strike",
                    "connection_rationale": "Both involve worker organizing",
                },
                "thesis": "History repeats",
                "narrative_angle": "Documentary style",
                "confidence_score": 0.8,
            },
        )
        mock_client.chat_completion_json.return_value = mock_response
        mock_get_client.return_value = mock_client

        connector = HistoricalConnector()
        result = connector.find_connection(sample_news_story)

        assert result is not None
        assert result.historical_event.name == "Pullman Strike"
        assert result.confidence_score == 0.8
