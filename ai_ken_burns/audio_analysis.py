"""
Audio analysis module for AI Ken Burns.

Extracts audio metadata including duration and creates segment boundaries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydub import AudioSegment

from ai_ken_burns.models import AudioMetadata
from ai_ken_burns.utils.logging_utils import get_logger

logger = get_logger()


def analyze_audio(
    audio_path: str,
    segment_duration: float = 5.0,
    min_segments: int = 4,
    max_segments: int = 12,
) -> AudioMetadata:
    """
    Analyze an audio file and return metadata including segment boundaries.

    Args:
        audio_path: Path to the audio file
        segment_duration: Target duration for each segment in seconds
        min_segments: Minimum number of segments to create
        max_segments: Maximum number of segments to create

    Returns:
        AudioMetadata with duration and segment boundaries
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Load audio file with pydub
    logger.debug(f"Loading audio file: {audio_path}")
    audio = AudioSegment.from_file(audio_path)

    # Extract basic metadata
    duration = len(audio) / 1000.0  # milliseconds to seconds
    sample_rate = audio.frame_rate
    channels = audio.channels

    logger.debug(f"Audio duration: {duration:.2f}s, sample_rate: {sample_rate}, channels: {channels}")

    # Create segments
    segments = create_segments(
        duration=duration,
        segment_duration=segment_duration,
        min_segments=min_segments,
        max_segments=max_segments,
    )

    return AudioMetadata(
        duration=duration,
        segments=segments,
        sample_rate=sample_rate,
        channels=channels,
    )


def create_segments(
    duration: float,
    segment_duration: float = 5.0,
    min_segments: int = 4,
    max_segments: int = 12,
) -> list[tuple[float, float]]:
    """
    Create segment boundaries for the given duration.

    Uses a simple equal-division strategy. More sophisticated segmentation
    (e.g., beat detection) can be added later.

    Args:
        duration: Total audio duration in seconds
        segment_duration: Target duration for each segment
        min_segments: Minimum number of segments
        max_segments: Maximum number of segments

    Returns:
        List of (start, end) tuples in seconds
    """
    if duration <= 0:
        return []

    # Calculate number of segments based on target duration
    num_segments = int(duration / segment_duration)

    # Clamp to min/max
    num_segments = max(min_segments, min(max_segments, num_segments))

    # Ensure at least 1 segment for very short audio
    num_segments = max(1, num_segments)

    # Calculate actual segment length
    actual_segment_duration = duration / num_segments

    # Create segment boundaries
    segments: list[tuple[float, float]] = []
    for i in range(num_segments):
        start = i * actual_segment_duration
        end = (i + 1) * actual_segment_duration

        # Ensure last segment ends exactly at duration
        if i == num_segments - 1:
            end = duration

        segments.append((round(start, 3), round(end, 3)))

    logger.debug(f"Created {len(segments)} segments of ~{actual_segment_duration:.2f}s each")

    return segments


def get_audio_duration(audio_path: str) -> float:
    """
    Quick helper to get just the duration of an audio file.

    Args:
        audio_path: Path to the audio file

    Returns:
        Duration in seconds
    """
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0
