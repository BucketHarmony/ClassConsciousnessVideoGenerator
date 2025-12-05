"""
Data models for audio pipeline.

Defines structures for audio segments and output metadata.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class AudioSegment(BaseModel):
    """
    Audio segment with timing information.

    Represents a portion of the narration audio with
    start/end times and associated text.
    """

    id: int = Field(ge=1, description="Segment number")

    # File info
    file_path: str = Field(description="Path to the audio segment file")

    # Timing
    start_time: float = Field(ge=0.0, description="Start time in seconds")
    end_time: float = Field(gt=0.0, description="End time in seconds")
    duration: float = Field(gt=0.0, description="Duration in seconds")

    # Content
    text: str = Field(description="Text content of this segment")
    word_count: int = Field(default=0, description="Number of words")

    # Quality metrics
    words_per_minute: Optional[float] = Field(
        default=None,
        description="Speaking rate"
    )

    @property
    def is_valid(self) -> bool:
        """Check if segment has valid timing."""
        return self.end_time > self.start_time and self.duration > 0


class AudioOutput(BaseModel):
    """
    Complete audio output from TTS generation.

    Contains the main audio file and timing metadata for
    synchronizing with visual markers.
    """

    # Main output
    audio_file: str = Field(description="Path to the main audio file")

    # Timing
    total_duration: float = Field(ge=0.0, description="Total duration in seconds")

    # Segment timing (for visual sync)
    segments: list[AudioSegment] = Field(
        default_factory=list,
        description="Audio segments with timing"
    )

    # Visual marker timing (calculated from segments)
    marker_times: dict[str, tuple[float, float]] = Field(
        default_factory=dict,
        description="Map of marker ID to (start, end) times"
    )

    # Generation metadata
    model: str = Field(default="tts-1", description="TTS model used")
    voice: str = Field(default="onyx", description="Voice used")
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="When audio was generated"
    )

    # Quality metrics
    total_words: int = Field(default=0, description="Total word count")
    average_wpm: Optional[float] = Field(
        default=None,
        description="Average words per minute"
    )

    @property
    def segment_count(self) -> int:
        """Number of segments."""
        return len(self.segments)

    def get_marker_time(self, marker_id: str) -> Optional[tuple[float, float]]:
        """Get start/end time for a visual marker."""
        return self.marker_times.get(marker_id)

    def to_video_spec_timing(self) -> dict:
        """
        Convert to timing info for VideoSpec.

        Returns dict with duration and segment boundaries.
        """
        return {
            "total_duration": self.total_duration,
            "segments": [
                (seg.start_time, seg.end_time)
                for seg in self.segments
            ],
        }

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
