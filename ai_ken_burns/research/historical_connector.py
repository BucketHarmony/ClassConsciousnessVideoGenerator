"""
Historical connector for AI Ken Burns.

Uses LLM to find historical parallels for current news stories,
connecting them to class struggle and labor history.
"""

from __future__ import annotations

import json
import random
from typing import Optional

from ai_ken_burns.clients.openai_client import get_openai_client, APIResponse
from ai_ken_burns.config import get_config
from ai_ken_burns.utils.logging_utils import get_research_logger, log_timing
from ai_ken_burns.research.models import NewsStory, HistoricalEvent, ResearchOutput
from ai_ken_burns.prompts.research import (
    HISTORICAL_CONNECTION_SYSTEM,
    HISTORICAL_CONNECTION_USER,
    HISTORICAL_CONNECTION_SCHEMA,
)

logger = get_research_logger()


class HistoricalConnector:
    """
    Connects current news to historical events using LLM analysis.

    Uses GPT-4 to find meaningful parallels between current events
    and historical class struggles.
    """

    def __init__(self) -> None:
        """Initialize the historical connector."""
        self.config = get_config()
        self.client = get_openai_client()

    def _build_prompt(self, story: NewsStory) -> str:
        """Build the prompt for the LLM using the prompts module."""
        themes_str = ", ".join(story.themes) if story.themes else "general class consciousness"
        keywords_str = ", ".join(story.relevance_keywords[:5]) if story.relevance_keywords else ""

        return HISTORICAL_CONNECTION_USER.format(
            title=story.title,
            summary=story.summary,
            source=story.source,
            themes=themes_str,
            keywords=keywords_str,
        )

    def find_connection(
        self,
        story: NewsStory,
        temperature: float = 0.7,
    ) -> Optional[ResearchOutput]:
        """
        Find a historical connection for a news story.

        Args:
            story: NewsStory to find connection for
            temperature: LLM temperature for creativity

        Returns:
            ResearchOutput with historical connection, or None if failed
        """
        logger.info(f"Finding historical connection for: {story.title[:50]}...")

        prompt = self._build_prompt(story)

        messages = [
            {"role": "system", "content": str(HISTORICAL_CONNECTION_SYSTEM)},
            {"role": "user", "content": prompt},
        ]

        with log_timing("llm_historical_connection", logger):
            response = self.client.chat_completion_json(
                messages=messages,
                model=self.config.llm.research_model,
                temperature=temperature,
            )

        if not response.success:
            logger.error(f"LLM request failed: {response.error}")
            return None

        try:
            return self._parse_response(story, response)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None

    def _parse_response(
        self,
        story: NewsStory,
        response: APIResponse,
    ) -> ResearchOutput:
        """Parse the LLM response into ResearchOutput."""
        data = response.data

        # Extract historical event
        event_data = data.get("historical_event", {})

        historical_event = HistoricalEvent(
            name=event_data.get("name", "Unknown Event"),
            year=event_data.get("year"),
            year_range=event_data.get("year_range"),
            location=event_data.get("location", ""),
            summary=event_data.get("summary", ""),
            significance=event_data.get("significance", ""),
            connection_rationale=event_data.get("connection_rationale", ""),
            parallel_themes=event_data.get("parallel_themes", []),
            key_figures=event_data.get("key_figures", []),
            key_facts=event_data.get("key_facts", []),
            suggested_imagery=event_data.get("suggested_imagery", []),
        )

        # Build research output
        output = ResearchOutput(
            news_story=story,
            historical_event=historical_event,
            thesis=data.get("thesis", ""),
            narrative_angle=data.get("narrative_angle", ""),
            confidence_score=data.get("confidence_score", 0.5),
            stories_analyzed=1,
        )

        logger.info(
            f"Found connection: {historical_event.name} "
            f"(confidence: {output.confidence_score:.2f})"
        )

        return output

    def find_best_connection(
        self,
        stories: list[NewsStory],
        topic: Optional[str] = None,
        randomize: bool = True,
    ) -> Optional[ResearchOutput]:
        """
        Find the best historical connection from multiple stories.

        Tries stories (optionally randomized) and returns the first high-confidence match.

        Args:
            stories: List of news stories to analyze
            topic: Optional topic for context
            randomize: If True, shuffle stories to get variety (default: True)

        Returns:
            Best ResearchOutput, or None if all failed
        """
        if not stories:
            logger.warning("No stories provided for historical connection")
            return None

        # Shuffle stories for variety if randomize is enabled
        if randomize:
            stories = stories.copy()
            random.shuffle(stories)
            logger.info(f"Randomized story order for variety")

        best_output: Optional[ResearchOutput] = None

        for i, story in enumerate(stories):
            logger.info(f"Analyzing story {i + 1}/{len(stories)}: {story.title[:40]}...")

            output = self.find_connection(story)

            if output is None:
                continue

            # Update metadata
            output.stories_analyzed = len(stories)
            output.topic_filter = topic

            # Keep best connection
            if best_output is None or output.confidence_score > best_output.confidence_score:
                best_output = output

            # If we find a high-confidence match, stop early
            if output.confidence_score >= 0.8:
                logger.info("Found high-confidence connection, stopping search")
                break

        if best_output:
            logger.info(
                f"Best connection: {best_output.historical_event.name} "
                f"(confidence: {best_output.confidence_score:.2f})"
            )
        else:
            logger.warning("No valid historical connections found")

        return best_output


def find_historical_connection(
    story: NewsStory,
) -> Optional[ResearchOutput]:
    """
    Convenience function to find historical connection for a story.

    Args:
        story: NewsStory to analyze

    Returns:
        ResearchOutput with historical connection
    """
    connector = HistoricalConnector()
    return connector.find_connection(story)
