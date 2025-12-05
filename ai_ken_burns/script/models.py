"""
Data models for script generation.

Defines structures for annotated scripts with visual markers.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VisualType(str, Enum):
    """Types of visual content for markers."""

    HISTORICAL_PHOTO = "historical_photo"
    HISTORICAL_ARTWORK = "historical_artwork"
    HISTORICAL_DOCUMENT = "historical_document"
    NEWS_IMAGE = "news_image"
    PORTRAIT = "portrait"
    SCENE = "scene"
    ABSTRACT = "abstract"
    MAP = "map"
    GRAPH = "graph"


class MotionSuggestion(str, Enum):
    """Suggested Ken Burns motion patterns."""

    SLOW_ZOOM_IN = "slow_zoom_in"
    SLOW_ZOOM_OUT = "slow_zoom_out"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    STATIC = "static"


class VisualMarker(BaseModel):
    """
    A marker indicating what visual should appear at this point.

    Embedded in the script to guide image selection and timing.
    """

    id: str = Field(description="Unique marker ID (e.g., 'v1', 'v2')")

    # Content description
    description: str = Field(
        description="Description of what the visual should show"
    )
    search_terms: list[str] = Field(
        default_factory=list,
        description="Suggested search terms for finding images"
    )

    # Visual type and mood
    visual_type: VisualType = Field(
        default=VisualType.HISTORICAL_PHOTO,
        description="Type of visual content"
    )
    mood: str = Field(
        default="neutral",
        description="Emotional tone (somber, hopeful, urgent, etc.)"
    )

    # Motion suggestion
    motion: MotionSuggestion = Field(
        default=MotionSuggestion.SLOW_ZOOM_IN,
        description="Suggested Ken Burns motion"
    )

    # Timing hints
    duration_hint: Optional[float] = Field(
        default=None,
        description="Suggested duration in seconds"
    )

    # Historical context
    era: Optional[str] = Field(
        default=None,
        description="Historical era for the visual"
    )
    location: Optional[str] = Field(
        default=None,
        description="Geographic location"
    )


class ScriptSegment(BaseModel):
    """
    A segment of the narration script.

    Contains the spoken text and associated visual markers.
    """

    id: int = Field(ge=1, description="Segment number")

    # Content
    text: str = Field(description="Narration text for this segment")

    # Visual markers embedded in this segment
    visual_markers: list[VisualMarker] = Field(
        default_factory=list,
        description="Visual markers for this segment"
    )

    # Timing (populated after TTS)
    start_time: Optional[float] = Field(
        default=None,
        description="Start time in seconds (after TTS)"
    )
    end_time: Optional[float] = Field(
        default=None,
        description="End time in seconds (after TTS)"
    )
    duration: Optional[float] = Field(
        default=None,
        description="Duration in seconds (after TTS)"
    )

    # Mood and pacing
    mood: str = Field(
        default="neutral",
        description="Emotional tone of this segment"
    )
    pacing: str = Field(
        default="normal",
        description="Pacing hint (slow, normal, fast)"
    )

    def get_plain_text(self) -> str:
        """Get text with markers stripped."""
        import re
        # Remove marker tags like [v1], [v2], etc.
        return re.sub(r'\[v\d+\]', '', self.text).strip()

    def word_count(self) -> int:
        """Estimate word count for timing."""
        return len(self.get_plain_text().split())

    def estimate_duration(self, words_per_minute: int = 150) -> float:
        """Estimate duration based on word count."""
        return (self.word_count() / words_per_minute) * 60


class AnnotatedScript(BaseModel):
    """
    Complete annotated script with visual markers.

    Contains the full narration organized into segments,
    with embedded visual markers for Ken Burns video generation.
    """

    # Metadata
    title: str = Field(description="Video title")

    # Source context
    news_title: str = Field(default="", description="Original news story title")
    historical_event: str = Field(default="", description="Connected historical event")
    thesis: str = Field(default="", description="Central thesis")

    # Style
    style: str = Field(
        default="documentary",
        description="Narrative style"
    )
    tone: str = Field(
        default="thoughtful",
        description="Overall tone"
    )

    # Content
    segments: list[ScriptSegment] = Field(
        default_factory=list,
        description="Script segments"
    )

    # Timing (populated after TTS)
    total_duration: Optional[float] = Field(
        default=None,
        description="Total duration in seconds"
    )

    # Generation metadata
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="When the script was generated"
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="LLM model used for generation"
    )

    class Config:
        protected_namespaces = ()

    @property
    def full_text(self) -> str:
        """Get full narration text."""
        return "\n\n".join(seg.text for seg in self.segments)

    @property
    def plain_text(self) -> str:
        """Get full text with markers stripped."""
        return "\n\n".join(seg.get_plain_text() for seg in self.segments)

    @property
    def all_markers(self) -> list[VisualMarker]:
        """Get all visual markers in order."""
        markers = []
        for segment in self.segments:
            markers.extend(segment.visual_markers)
        return markers

    @property
    def segment_count(self) -> int:
        """Number of segments."""
        return len(self.segments)

    @property
    def marker_count(self) -> int:
        """Total number of visual markers."""
        return sum(len(seg.visual_markers) for seg in self.segments)

    def estimate_duration(self, words_per_minute: int = 150) -> float:
        """Estimate total duration based on word count."""
        return sum(seg.estimate_duration(words_per_minute) for seg in self.segments)

    def to_prompt_context(self) -> str:
        """Generate context for downstream prompts."""
        return f"""
SCRIPT: {self.title}

News: {self.news_title}
Historical Event: {self.historical_event}
Thesis: {self.thesis}

Style: {self.style}
Tone: {self.tone}

Segments: {self.segment_count}
Visual Markers: {self.marker_count}
Estimated Duration: {self.estimate_duration():.1f}s
""".strip()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
