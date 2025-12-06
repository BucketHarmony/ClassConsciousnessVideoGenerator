"""
FFmpeg utility functions for AI Ken Burns.

Provides helpers for:
- FFmpeg availability checking
- Ken Burns filter generation
- Video concatenation
- Audio merging
"""

from __future__ import annotations

import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple

from ai_ken_burns.utils.logging_utils import get_video_logger

logger = get_video_logger()


def check_ffmpeg() -> Tuple[bool, str]:
    """
    Check if FFmpeg is available and get version.

    Returns:
        Tuple of (is_available, version_string)
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            # Parse version from first line
            first_line = result.stdout.split("\n")[0]
            version_match = re.search(r"ffmpeg version (\S+)", first_line)
            version = version_match.group(1) if version_match else "unknown"
            return True, version

        return False, "FFmpeg returned error"

    except FileNotFoundError:
        return False, "FFmpeg not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "FFmpeg version check timed out"
    except Exception as e:
        return False, f"Error checking FFmpeg: {e}"


def check_ffprobe() -> Tuple[bool, str]:
    """
    Check if FFprobe is available.

    Returns:
        Tuple of (is_available, version_string)
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            first_line = result.stdout.split("\n")[0]
            version_match = re.search(r"ffprobe version (\S+)", first_line)
            version = version_match.group(1) if version_match else "unknown"
            return True, version

        return False, "FFprobe returned error"

    except FileNotFoundError:
        return False, "FFprobe not found in PATH"
    except Exception as e:
        return False, f"Error checking FFprobe: {e}"


def get_media_duration(file_path: str) -> Optional[float]:
    """
    Get duration of a media file in seconds using FFprobe.

    Args:
        file_path: Path to audio or video file

    Returns:
        Duration in seconds, or None if failed
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return float(result.stdout.strip())

        logger.error(f"FFprobe error: {result.stderr}")
        return None

    except Exception as e:
        logger.error(f"Failed to get media duration: {e}")
        return None


def generate_zoompan_filter(
    width: int,
    height: int,
    duration_seconds: float,
    fps: int,
    zoom_start: float = 1.0,
    zoom_end: float = 1.3,
    x_start: float = 0.5,
    y_start: float = 0.5,
    x_end: float = 0.5,
    y_end: float = 0.5,
    pan_ratio: float = 1.0,
) -> str:
    """
    Generate FFmpeg zoompan filter string for Ken Burns effect.

    The zoompan filter crops a region from the source image.
    - zoom: determines crop size (zoom=2 means visible region is 1/2 of source)
    - x/y: top-left corner of the crop region in source pixel coordinates

    The input image is scaled so the shorter side fits the output exactly.
    For example, a 1920x1080 image on a 1080x1080 output:
    - Height fits exactly (1080)
    - Width is scaled proportionally (1920)
    - pan_ratio = 1920/1080 = 1.78

    We set zoom = pan_ratio so the visible region equals the output size,
    leaving (pan_ratio - 1) * output_size pixels for panning.

    Args:
        width: Output video width
        height: Output video height
        duration_seconds: Duration of the clip in seconds
        fps: Frames per second
        zoom_start: Starting zoom level (1.0 = fit to screen, >1.0 = zoom in)
        zoom_end: Ending zoom level
        x_start: Starting X position (0-1, normalized, 0=left, 1=right)
        y_start: Starting Y position (0-1, normalized, 0=top, 1=bottom)
        x_end: Ending X position (0-1, normalized)
        y_end: Ending Y position (0-1, normalized)
        pan_ratio: Ratio of scaled image size to output size (e.g., 1.78 for 16:9 on square)

    Returns:
        FFmpeg filter string for zoompan
    """
    total_frames = int(duration_seconds * fps)
    if total_frames <= 0:
        total_frames = 1

    # Base zoom equals pan_ratio so visible region = output size
    # This means at zoom=pan_ratio, the entire output is filled with no black bars
    # and we have (pan_ratio - 1) * dimension pixels to pan across
    BASE_ZOOM = max(pan_ratio, 1.0)

    # Apply additional zoom on top of base
    # zoom_start=1.0 means no extra zoom (just pan)
    # zoom_start=1.5 means 1.5x zoom in addition to fitting
    ffmpeg_zoom_start = BASE_ZOOM * zoom_start
    ffmpeg_zoom_end = BASE_ZOOM * zoom_end

    # Calculate zoom progression per frame
    zoom_delta = (ffmpeg_zoom_end - ffmpeg_zoom_start) / total_frames

    # Build the zoom expression
    zoom_expr = f"{ffmpeg_zoom_start}+{zoom_delta}*on"

    # For x/y positioning:
    # The visible region size = iw/zoom
    # The pan range = iw - iw/zoom = iw * (1 - 1/zoom)
    # x position = pan_range * normalized_position
    #
    # At zoom=pan_ratio (e.g., 1.78), pan_range = iw * (1 - 1/1.78) = iw * 0.44
    # For a 1920px wide image, that's ~844px of pan range

    # Calculate normalized position progression
    x_delta = (x_end - x_start) / total_frames
    y_delta = (y_end - y_start) / total_frames

    # Current normalized position at frame 'on'
    x_norm = f"({x_start}+{x_delta}*on)"
    y_norm = f"({y_start}+{y_delta}*on)"

    # x/y in pixels, based on current zoom level
    x_expr = f"(iw-iw/zoom)*{x_norm}"
    y_expr = f"(ih-ih/zoom)*{y_norm}"

    filter_str = (
        f"zoompan=z='{zoom_expr}':"
        f"x='{x_expr}':"
        f"y='{y_expr}':"
        f"d={total_frames}:"
        f"s={width}x{height}:"
        f"fps={fps}"
    )

    return filter_str


def get_ken_burns_filter_for_pattern(
    pattern: str,
    width: int,
    height: int,
    duration: float,
    fps: int,
    intensity: float = 0.5,
) -> str:
    """
    Get FFmpeg filter for a named Ken Burns pattern.

    Args:
        pattern: Pattern name (zoom_in, pan_left, etc.)
        width: Output width
        height: Output height
        duration: Clip duration in seconds
        fps: Frames per second
        intensity: Motion intensity (0-1)

    Returns:
        FFmpeg filter string
    """
    # Scale intensity to zoom range
    max_zoom = 1.0 + (0.5 * intensity)  # 1.0 to 1.5
    min_zoom = 1.0
    pan_amount = 0.3 * intensity  # How far to pan (0-0.3)

    patterns = {
        "zoom_in": {
            "zoom_start": min_zoom,
            "zoom_end": max_zoom,
            "x_start": 0.5, "y_start": 0.5,
            "x_end": 0.5, "y_end": 0.5,
        },
        "slow_zoom_in": {
            "zoom_start": min_zoom,
            "zoom_end": 1.0 + (0.2 * intensity),
            "x_start": 0.5, "y_start": 0.5,
            "x_end": 0.5, "y_end": 0.5,
        },
        "zoom_out": {
            "zoom_start": max_zoom,
            "zoom_end": min_zoom,
            "x_start": 0.5, "y_start": 0.5,
            "x_end": 0.5, "y_end": 0.5,
        },
        "slow_zoom_out": {
            "zoom_start": 1.0 + (0.2 * intensity),
            "zoom_end": min_zoom,
            "x_start": 0.5, "y_start": 0.5,
            "x_end": 0.5, "y_end": 0.5,
        },
        "pan_left": {
            "zoom_start": 1.1,
            "zoom_end": 1.1,
            "x_start": 0.5 + pan_amount,
            "y_start": 0.5,
            "x_end": 0.5 - pan_amount,
            "y_end": 0.5,
        },
        "pan_right": {
            "zoom_start": 1.1,
            "zoom_end": 1.1,
            "x_start": 0.5 - pan_amount,
            "y_start": 0.5,
            "x_end": 0.5 + pan_amount,
            "y_end": 0.5,
        },
        "pan_up": {
            "zoom_start": 1.1,
            "zoom_end": 1.1,
            "x_start": 0.5,
            "y_start": 0.5 + pan_amount,
            "x_end": 0.5,
            "y_end": 0.5 - pan_amount,
        },
        "pan_down": {
            "zoom_start": 1.1,
            "zoom_end": 1.1,
            "x_start": 0.5,
            "y_start": 0.5 - pan_amount,
            "x_end": 0.5,
            "y_end": 0.5 + pan_amount,
        },
        "zoom_in_left": {
            "zoom_start": min_zoom,
            "zoom_end": max_zoom,
            "x_start": 0.5 + pan_amount,
            "y_start": 0.5,
            "x_end": 0.3,
            "y_end": 0.5,
        },
        "zoom_in_right": {
            "zoom_start": min_zoom,
            "zoom_end": max_zoom,
            "x_start": 0.5 - pan_amount,
            "y_start": 0.5,
            "x_end": 0.7,
            "y_end": 0.5,
        },
        "static": {
            "zoom_start": 1.0,
            "zoom_end": 1.0,
            "x_start": 0.5,
            "y_start": 0.5,
            "x_end": 0.5,
            "y_end": 0.5,
        },
    }

    params = patterns.get(pattern, patterns["zoom_in"])

    return generate_zoompan_filter(
        width=width,
        height=height,
        duration_seconds=duration,
        fps=fps,
        **params,
    )


def run_ffmpeg(
    args: list[str],
    timeout: int = 300,
    capture_output: bool = True,
) -> Tuple[bool, str]:
    """
    Run an FFmpeg command.

    Args:
        args: FFmpeg arguments (without 'ffmpeg' prefix)
        timeout: Timeout in seconds
        capture_output: Whether to capture stdout/stderr

    Returns:
        Tuple of (success, output_or_error)
    """
    cmd = ["ffmpeg"] + args

    logger.debug(f"Running FFmpeg: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return True, result.stdout if capture_output else ""
        else:
            error = result.stderr if capture_output else "FFmpeg failed"
            logger.error(f"FFmpeg error: {error}")
            return False, error

    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg timed out after {timeout}s")
        return False, f"Timeout after {timeout} seconds"
    except Exception as e:
        logger.error(f"FFmpeg exception: {e}")
        return False, str(e)
