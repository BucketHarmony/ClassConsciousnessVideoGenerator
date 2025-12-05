"""
Data models for video pipeline.

Defines structures for video segments and render specifications.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class MotionParams(BaseModel):
    """
    Ken Burns motion parameters for a single segment.

    Defines the zoom/pan motion from start to end keyframe.
    """

    # Motion pattern
    pattern: str = Field(
        default="slow_zoom_in",
        description="Motion pattern name"
    )

    # Zoom
    zoom_start: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Starting zoom level"
    )
    zoom_end: float = Field(
        default=1.2,
        ge=0.5,
        le=2.0,
        description="Ending zoom level"
    )

    # Position (normalized 0-1)
    x_start: float = Field(default=0.5, ge=0.0, le=1.0, description="Start X position")
    y_start: float = Field(default=0.5, ge=0.0, le=1.0, description="Start Y position")
    x_end: float = Field(default=0.5, ge=0.0, le=1.0, description="End X position")
    y_end: float = Field(default=0.5, ge=0.0, le=1.0, description="End Y position")


class VideoSegment(BaseModel):
    """
    A single segment of the final video.

    Contains the image, timing, and motion parameters for one Ken Burns segment.
    """

    # Identification
    id: str = Field(description="Segment ID (usually marker ID)")
    order: int = Field(ge=0, description="Order in the video sequence")

    # Image
    image_path: str = Field(description="Path to the image file")
    image_width: Optional[int] = Field(default=None, description="Image width")
    image_height: Optional[int] = Field(default=None, description="Image height")

    # Timing
    start_time: float = Field(ge=0.0, description="Start time in seconds")
    end_time: float = Field(gt=0.0, description="End time in seconds")

    @property
    def duration(self) -> float:
        """Segment duration in seconds."""
        return self.end_time - self.start_time

    # Motion
    motion: MotionParams = Field(
        default_factory=MotionParams,
        description="Ken Burns motion parameters"
    )

    # Rendering
    temp_video_path: Optional[str] = Field(
        default=None,
        description="Path to rendered segment video"
    )
    is_rendered: bool = Field(default=False, description="Whether segment is rendered")


class RenderSpec(BaseModel):
    """
    Complete specification for video rendering.

    Contains all information needed to render the final video.
    """

    # Project info
    project_id: str = Field(description="Project identifier")
    title: str = Field(default="", description="Video title")

    # Video settings
    width: int = Field(default=1920, ge=320, description="Video width")
    height: int = Field(default=1080, ge=240, description="Video height")
    fps: int = Field(default=30, ge=1, le=120, description="Frames per second")

    # Audio
    audio_file: str = Field(description="Path to narration audio")
    total_duration: float = Field(ge=0.0, description="Total duration in seconds")

    # Segments
    segments: list[VideoSegment] = Field(
        default_factory=list,
        description="Video segments to render"
    )

    # Output
    output_path: Optional[str] = Field(
        default=None,
        description="Final output video path"
    )

    # Ken Burns settings
    ken_burns_intensity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Overall motion intensity"
    )

    # Rendering metadata
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When spec was created"
    )
    rendered_at: Optional[datetime] = Field(
        default=None,
        description="When video was rendered"
    )

    @property
    def segment_count(self) -> int:
        """Number of segments."""
        return len(self.segments)

    @property
    def rendered_count(self) -> int:
        """Number of rendered segments."""
        return sum(1 for s in self.segments if s.is_rendered)

    @property
    def resolution(self) -> tuple[int, int]:
        """Video resolution as tuple."""
        return (self.width, self.height)

    def get_segment_by_id(self, segment_id: str) -> Optional[VideoSegment]:
        """Get segment by ID."""
        for seg in self.segments:
            if seg.id == segment_id:
                return seg
        return None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
