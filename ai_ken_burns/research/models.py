"""
Data models for the research pipeline.

Defines structures for news stories, historical events, and research output.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NewsStory(BaseModel):
    """
    A news story from RSS feed.

    Contains the story details and relevance scoring for class consciousness topics.
    """

    title: str = Field(description="Story headline")
    summary: str = Field(description="Story summary or description")
    link: str = Field(description="URL to the full story")
    published: Optional[datetime] = Field(default=None, description="Publication date")
    source: str = Field(default="", description="News source name")

    # Relevance analysis
    relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevance to class consciousness (0-1)"
    )
    relevance_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords that triggered relevance"
    )
    themes: list[str] = Field(
        default_factory=list,
        description="Identified class consciousness themes"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class HistoricalEvent(BaseModel):
    """
    A historical event connected to current news.

    Represents a parallel from history that illuminates the class dynamics
    of a current news story.
    """

    name: str = Field(description="Name of the historical event")
    year: Optional[int] = Field(default=None, description="Year the event occurred")
    year_range: Optional[str] = Field(default=None, description="Year range if spans multiple years")
    location: str = Field(default="", description="Where the event took place")

    summary: str = Field(description="Brief summary of the event")
    significance: str = Field(
        default="",
        description="Why this event matters for class consciousness"
    )

    # Connection to current news
    connection_rationale: str = Field(
        default="",
        description="How this connects to the current news story"
    )
    parallel_themes: list[str] = Field(
        default_factory=list,
        description="Themes shared with the current story"
    )

    # Key figures and facts
    key_figures: list[str] = Field(
        default_factory=list,
        description="Important people involved"
    )
    key_facts: list[str] = Field(
        default_factory=list,
        description="Important facts to mention"
    )

    # Visual suggestions
    suggested_imagery: list[str] = Field(
        default_factory=list,
        description="Suggested historical images to search for"
    )


class ResearchOutput(BaseModel):
    """
    Complete output from the research pipeline.

    Contains the selected news story, historical connection, and metadata
    for downstream script generation.
    """

    # Core content
    news_story: NewsStory = Field(description="The selected news story")
    historical_event: HistoricalEvent = Field(description="Connected historical event")

    # Narrative framing
    thesis: str = Field(
        default="",
        description="Central thesis connecting news to history"
    )
    narrative_angle: str = Field(
        default="",
        description="Suggested narrative approach"
    )

    # Metadata
    research_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When research was conducted"
    )
    topic_filter: Optional[str] = Field(
        default=None,
        description="Topic filter used, if any"
    )
    stories_analyzed: int = Field(
        default=0,
        description="Number of stories considered"
    )

    # Quality indicators
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the connection (0-1)"
    )

    def to_prompt_context(self) -> str:
        """Generate context string for script generation prompts."""
        return f"""
NEWS STORY:
Title: {self.news_story.title}
Summary: {self.news_story.summary}
Source: {self.news_story.source}
Themes: {', '.join(self.news_story.themes)}

HISTORICAL CONNECTION:
Event: {self.historical_event.name}
Period: {self.historical_event.year or self.historical_event.year_range or 'Unknown'}
Location: {self.historical_event.location}

Summary: {self.historical_event.summary}

Significance: {self.historical_event.significance}

Connection: {self.historical_event.connection_rationale}

Parallel Themes: {', '.join(self.historical_event.parallel_themes)}

Key Figures: {', '.join(self.historical_event.key_figures)}

THESIS: {self.thesis}

NARRATIVE ANGLE: {self.narrative_angle}
""".strip()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
