"""
Pydantic models for AI Ken Burns video generation.

Defines the core data structures: VideoSpec, Segment, ImageItem, Motion, and Keyframe.
These models are used throughout the pipeline for storyboard generation and rendering.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class MotionPattern(str, Enum):
    """Available Ken Burns motion patterns."""

    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    SLOW_ZOOM_IN = "slow_zoom_in"
    SLOW_ZOOM_OUT = "slow_zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    ZOOM_IN_LEFT = "zoom_in_left"
    ZOOM_IN_RIGHT = "zoom_in_right"
    STATIC = "static"


class Keyframe(BaseModel):
    """
    Represents a single keyframe for Ken Burns motion.

    Coordinates are normalized (0-1) relative to the image dimensions.
    Scale represents zoom level (1.0 = original size).
    """

    x: float = Field(default=0.0, ge=0.0, le=1.0, description="X position (0-1)")
    y: float = Field(default=0.0, ge=0.0, le=1.0, description="Y position (0-1)")
    scale: float = Field(default=1.0, ge=0.5, le=2.0, description="Zoom scale (1.0 = original)")

    class Config:
        frozen = True


class Motion(BaseModel):
    """
    Motion specification for a single image.

    Defines the type of motion and the start/end keyframes for Ken Burns effect.
    """

    type: str = Field(default="ken_burns", description="Motion type (ken_burns or static)")
    pattern: MotionPattern = Field(
        default=MotionPattern.ZOOM_IN, description="Ken Burns motion pattern"
    )
    start_frame: Keyframe = Field(
        default_factory=lambda: Keyframe(x=0.0, y=0.0, scale=1.0),
        description="Starting keyframe",
    )
    end_frame: Keyframe = Field(
        default_factory=lambda: Keyframe(x=0.0, y=0.0, scale=1.0),
        description="Ending keyframe",
    )

    @model_validator(mode="after")
    def validate_motion(self) -> "Motion":
        """Ensure static motion has matching start/end frames."""
        if self.pattern == MotionPattern.STATIC:
            # For static, start and end should match
            if self.start_frame != self.end_frame:
                object.__setattr__(self, "end_frame", self.start_frame)
        return self


class ImageItem(BaseModel):
    """
    Represents a single image in the video storyboard.

    Contains the image file path, timing, description, and motion specification.
    """

    id: str = Field(default="", description="Unique identifier for the image")
    description: str = Field(default="", description="Description of the image content/mood")
    file: str = Field(default="placeholder", description="Path to the image file")
    start: float = Field(ge=0.0, description="Start time in seconds")
    end: float = Field(gt=0.0, description="End time in seconds")
    motion: Motion = Field(default_factory=Motion, description="Motion specification")

    @property
    def duration(self) -> float:
        """Calculate image display duration in seconds."""
        return self.end - self.start

    @field_validator("file")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Accept placeholder or validate path format."""
        if v == "placeholder":
            return v
        # Allow any string path - actual validation happens at render time
        return v

    @model_validator(mode="after")
    def validate_timing(self) -> "ImageItem":
        """Ensure end time is after start time."""
        if self.end <= self.start:
            raise ValueError(f"Image end time ({self.end}) must be after start time ({self.start})")
        return self


class Segment(BaseModel):
    """
    Represents a segment of the video.

    A segment contains one or more images and has timing, mood, and description.
    """

    id: int = Field(ge=1, description="Segment number (1-indexed)")
    start: float = Field(ge=0.0, description="Segment start time in seconds")
    end: float = Field(gt=0.0, description="Segment end time in seconds")
    mood: str = Field(default="neutral", description="Mood/feeling of this segment")
    short_description: str = Field(
        default="", description="Brief description of segment content"
    )
    images: list[ImageItem] = Field(
        default_factory=list, description="Images in this segment"
    )

    @property
    def duration(self) -> float:
        """Calculate segment duration in seconds."""
        return self.end - self.start

    @model_validator(mode="after")
    def validate_timing(self) -> "Segment":
        """Ensure segment timing is valid."""
        if self.end <= self.start:
            raise ValueError(
                f"Segment {self.id} end time ({self.end}) must be after start time ({self.start})"
            )
        return self


class VideoSpec(BaseModel):
    """
    Complete video specification.

    Contains all metadata and segment information needed to render a video.
    This is the central data structure passed through the pipeline.
    """

    audio_file: str = Field(description="Path to the audio file")
    fps: int = Field(default=30, ge=1, le=120, description="Frames per second")
    resolution: tuple[int, int] = Field(
        default=(1920, 1080), description="Video resolution (width, height)"
    )
    total_duration: float = Field(ge=0.0, description="Total video duration in seconds")
    style_prompt: str = Field(default="", description="Style prompt for the video")
    segments: list[Segment] = Field(
        default_factory=list, description="Video segments"
    )

    @property
    def width(self) -> int:
        """Get video width."""
        return self.resolution[0]

    @property
    def height(self) -> int:
        """Get video height."""
        return self.resolution[1]

    @property
    def segment_count(self) -> int:
        """Get number of segments."""
        return len(self.segments)

    @property
    def image_count(self) -> int:
        """Get total number of images across all segments."""
        return sum(len(s.images) for s in self.segments)

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: tuple[int, int]) -> tuple[int, int]:
        """Ensure resolution is valid."""
        width, height = v
        if width < 320 or height < 240:
            raise ValueError(f"Resolution {width}x{height} is too small (min 320x240)")
        if width > 7680 or height > 4320:
            raise ValueError(f"Resolution {width}x{height} is too large (max 7680x4320)")
        return v

    @model_validator(mode="after")
    def validate_segments(self) -> "VideoSpec":
        """Validate segment timing consistency."""
        if not self.segments:
            return self

        # Check segments are in order and don't overlap
        for i, segment in enumerate(self.segments):
            if i > 0:
                prev = self.segments[i - 1]
                if segment.start < prev.end:
                    raise ValueError(
                        f"Segment {segment.id} starts at {segment.start} but previous "
                        f"segment ends at {prev.end}"
                    )

        # Check last segment doesn't exceed total duration (with small tolerance)
        last_segment = self.segments[-1]
        if last_segment.end > self.total_duration + 0.1:
            raise ValueError(
                f"Last segment ends at {last_segment.end} but total duration is "
                f"{self.total_duration}"
            )

        return self

    def get_all_images(self) -> list[ImageItem]:
        """Get all images from all segments in order."""
        images = []
        for segment in self.segments:
            images.extend(segment.images)
        return images

    def to_json_file(self, path: str | Path) -> None:
        """Save VideoSpec to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def from_json_file(cls, path: str | Path) -> "VideoSpec":
        """Load VideoSpec from a JSON file."""
        path = Path(path)
        return cls.model_validate_json(path.read_text())


class LLMStoryboardResponse(BaseModel):
    """
    Schema for LLM-generated storyboard response.

    This is the raw response from the LLM before image assignment and motion planning.
    Uses relative times (0-1) that get converted to absolute times.
    """

    segments: list[LLMSegment] = Field(description="List of storyboard segments")


class LLMSegment(BaseModel):
    """LLM response segment with relative timing."""

    id: int = Field(ge=1)
    relative_start: float = Field(ge=0.0, le=1.0)
    relative_end: float = Field(ge=0.0, le=1.0)
    mood: str = Field(default="neutral")
    short_description: str = Field(default="")
    images: list[LLMImage] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_timing(self) -> "LLMSegment":
        """Ensure relative end is after relative start."""
        if self.relative_end <= self.relative_start:
            raise ValueError("relative_end must be greater than relative_start")
        return self


class LLMImage(BaseModel):
    """LLM response image with relative duration."""

    description: str = Field(default="")
    relative_duration: float = Field(ge=0.0, le=1.0, description="Fraction of segment duration")
    motion_type: str = Field(default="slow_zoom_in")


class AudioMetadata(BaseModel):
    """Metadata extracted from audio analysis."""

    duration: float = Field(ge=0.0, description="Total audio duration in seconds")
    segments: list[tuple[float, float]] = Field(
        default_factory=list, description="List of (start, end) segment boundaries"
    )
    sample_rate: Optional[int] = Field(default=None, description="Audio sample rate")
    channels: Optional[int] = Field(default=None, description="Number of audio channels")

    @property
    def segment_count(self) -> int:
        """Get number of segments."""
        return len(self.segments)
