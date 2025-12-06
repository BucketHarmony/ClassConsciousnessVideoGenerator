"""
Ken Burns effect engine for AI Ken Burns.

Generates motion parameters based on visual markers and timing.
"""

from __future__ import annotations

import random
from typing import Optional

from ai_ken_burns.config import get_config
from ai_ken_burns.script.models import AnnotatedScript, VisualMarker, MotionSuggestion
from ai_ken_burns.audio.models import AudioOutput
from ai_ken_burns.images.models import ImageCollection, ImageResult
from ai_ken_burns.video.models import VideoSegment, RenderSpec, MotionParams
from ai_ken_burns.utils.logging_utils import get_video_logger

logger = get_video_logger()

# Motion pattern definitions - TRIPLED intensity for dramatic effect
MOTION_PATTERNS = {
    "slow_zoom_in": {
        "zoom_start": 1.0, "zoom_end": 1.5,  # Tripled from original 1.15
        "x_start": 0.5, "y_start": 0.5,
        "x_end": 0.5, "y_end": 0.5,
    },
    "slow_zoom_out": {
        "zoom_start": 1.5, "zoom_end": 1.0,  # Tripled
        "x_start": 0.5, "y_start": 0.5,
        "x_end": 0.5, "y_end": 0.5,
    },
    "zoom_in": {
        "zoom_start": 1.0, "zoom_end": 2.0,  # Very dramatic zoom
        "x_start": 0.5, "y_start": 0.5,
        "x_end": 0.5, "y_end": 0.5,
    },
    "zoom_out": {
        "zoom_start": 2.0, "zoom_end": 1.0,  # Very dramatic zoom out
        "x_start": 0.5, "y_start": 0.5,
        "x_end": 0.5, "y_end": 0.5,
    },
    "pan_left": {
        "zoom_start": 1.5, "zoom_end": 1.5,
        "x_start": 0.9, "y_start": 0.5,  # Near right edge
        "x_end": 0.1, "y_end": 0.5,  # Near left edge
    },
    "pan_right": {
        "zoom_start": 1.5, "zoom_end": 1.5,
        "x_start": 0.1, "y_start": 0.5,  # Near left edge
        "x_end": 0.9, "y_end": 0.5,  # Near right edge
    },
    "pan_up": {
        "zoom_start": 1.5, "zoom_end": 1.5,
        "x_start": 0.5, "y_start": 0.9,  # Near bottom
        "x_end": 0.5, "y_end": 0.1,  # Near top
    },
    "pan_down": {
        "zoom_start": 1.5, "zoom_end": 1.5,
        "x_start": 0.5, "y_start": 0.1,  # Near top
        "x_end": 0.5, "y_end": 0.9,  # Near bottom
    },
    "static": {
        "zoom_start": 1.1, "zoom_end": 1.2,  # Slight zoom even for static
        "x_start": 0.5, "y_start": 0.5,
        "x_end": 0.5, "y_end": 0.5,
    },
    # Zoom + pan combinations for extra drama
    "zoom_in_pan_left": {
        "zoom_start": 1.0, "zoom_end": 1.8,
        "x_start": 0.8, "y_start": 0.5,
        "x_end": 0.2, "y_end": 0.5,
    },
    "zoom_in_pan_right": {
        "zoom_start": 1.0, "zoom_end": 1.8,
        "x_start": 0.2, "y_start": 0.5,
        "x_end": 0.8, "y_end": 0.5,
    },
    "zoom_out_pan_up": {
        "zoom_start": 1.8, "zoom_end": 1.0,
        "x_start": 0.5, "y_start": 0.8,
        "x_end": 0.5, "y_end": 0.2,
    },
    # Sliding patterns for images that don't fit - full pan across image
    "slide_left": {
        "zoom_start": 1.0, "zoom_end": 1.0,
        "x_start": 0.95, "y_start": 0.5,  # Start at right edge
        "x_end": 0.05, "y_end": 0.5,  # End at left edge
    },
    "slide_right": {
        "zoom_start": 1.0, "zoom_end": 1.0,
        "x_start": 0.05, "y_start": 0.5,  # Start at left edge
        "x_end": 0.95, "y_end": 0.5,  # End at right edge
    },
    "slide_up": {
        "zoom_start": 1.0, "zoom_end": 1.0,
        "x_start": 0.5, "y_start": 0.95,  # Start at bottom
        "x_end": 0.5, "y_end": 0.05,  # End at top
    },
    "slide_down": {
        "zoom_start": 1.0, "zoom_end": 1.0,
        "x_start": 0.5, "y_start": 0.05,  # Start at top
        "x_end": 0.5, "y_end": 0.95,  # End at bottom
    },
    # Diagonal slides
    "slide_diagonal_tl": {
        "zoom_start": 1.0, "zoom_end": 1.0,
        "x_start": 0.9, "y_start": 0.9,  # Start at bottom-right
        "x_end": 0.1, "y_end": 0.1,  # End at top-left
    },
    "slide_diagonal_br": {
        "zoom_start": 1.0, "zoom_end": 1.0,
        "x_start": 0.1, "y_start": 0.1,  # Start at top-left
        "x_end": 0.9, "y_end": 0.9,  # End at bottom-right
    },
}


class KenBurnsEngine:
    """
    Generates Ken Burns motion parameters for video segments.

    Takes visual markers with motion suggestions and creates
    concrete motion parameters for FFmpeg rendering.
    """

    def __init__(self, intensity: float = 0.5) -> None:
        """
        Initialize the Ken Burns engine.

        Args:
            intensity: Global motion intensity (0-1)
        """
        self.config = get_config()
        self.intensity = intensity

    def create_render_spec(
        self,
        script: AnnotatedScript,
        audio: AudioOutput,
        images: ImageCollection,
        output_path: str,
    ) -> RenderSpec:
        """
        Create a complete render specification.

        Ensures video duration matches full audio duration by:
        1. Using marker timing from audio for segments with images
        2. Redistributing time from missing markers to available ones
        3. Extending the last segment to cover remaining audio time

        Args:
            script: AnnotatedScript with visual markers
            audio: AudioOutput with timing information
            images: ImageCollection with downloaded images
            output_path: Path for output video

        Returns:
            RenderSpec ready for rendering
        """
        logger.info(f"Creating render spec for: {script.title}")

        config = get_config()

        spec = RenderSpec(
            project_id=images.project_id,
            title=script.title,
            width=config.video.width,
            height=config.video.height,
            fps=config.video.fps,
            audio_file=audio.audio_file,
            total_duration=audio.total_duration,
            output_path=output_path,
            ken_burns_intensity=self.intensity,
        )

        # Get markers in order
        markers = script.all_markers

        # First pass: identify which markers have images
        available_markers = []
        for marker in markers:
            image = images.get_image_for_marker(marker.id)
            if image and image.local_path:
                available_markers.append((marker, image))
            else:
                logger.warning(f"No image for marker [{marker.id}], will redistribute time")

        if not available_markers:
            logger.error("No markers with images available")
            return spec

        # Calculate total duration to cover
        total_audio_duration = audio.total_duration

        # Distribute duration evenly among available markers
        # This ensures we cover the full audio duration
        segment_duration = total_audio_duration / len(available_markers)

        # Create segments with proper timing
        current_time = 0.0
        for i, (marker, image) in enumerate(available_markers):
            # Calculate segment end time
            if i == len(available_markers) - 1:
                # Last segment extends to the end of audio
                end_time = total_audio_duration
            else:
                end_time = current_time + segment_duration

            # Generate motion with image dimensions for aspect ratio detection
            motion = self._generate_motion(
                marker,
                self.intensity,
                image_width=image.width,
                image_height=image.height,
            )

            segment = VideoSegment(
                id=marker.id,
                order=i,
                image_path=image.local_path,
                image_width=image.width,
                image_height=image.height,
                start_time=current_time,
                end_time=end_time,
                motion=motion,
            )

            spec.segments.append(segment)
            current_time = end_time

        logger.info(
            f"Render spec created: {spec.segment_count} segments, "
            f"total duration: {total_audio_duration:.1f}s"
        )

        return spec

    def _generate_motion(
        self,
        marker: VisualMarker,
        intensity: float,
        image_width: int = None,
        image_height: int = None,
    ) -> MotionParams:
        """
        Generate motion parameters for a visual marker.

        Images are scaled to fit the shorter side to the video dimension,
        then we pan along the longer side to show the entire image.

        Args:
            marker: VisualMarker with motion suggestion
            intensity: Motion intensity (0-1)
            image_width: Width of the image (for aspect ratio detection)
            image_height: Height of the image (for aspect ratio detection)

        Returns:
            MotionParams for the segment
        """
        config = get_config()
        video_width = config.video.width
        video_height = config.video.height
        video_aspect = video_width / video_height

        if image_width and image_height:
            image_aspect = image_width / image_height

            # Image is wider than video - pan horizontally
            if image_aspect > video_aspect * 1.1:
                # Randomly choose direction
                if random.choice([True, False]):
                    # Slide left (start right, end left)
                    x_start, x_end = 1.0, 0.0
                    direction = "slide_left"
                else:
                    # Slide right (start left, end right)
                    x_start, x_end = 0.0, 1.0
                    direction = "slide_right"

                logger.info(f"Image wider than video ({image_aspect:.2f} vs {video_aspect:.2f}), using {direction}")
                return MotionParams(
                    pattern=direction,
                    zoom_start=1.0,
                    zoom_end=1.0,
                    x_start=x_start,
                    y_start=0.5,  # Centered vertically
                    x_end=x_end,
                    y_end=0.5,
                )

            # Image is taller than video - pan vertically
            elif image_aspect < video_aspect * 0.9:
                # Randomly choose direction
                if random.choice([True, False]):
                    # Slide up (start bottom, end top)
                    y_start, y_end = 1.0, 0.0
                    direction = "slide_up"
                else:
                    # Slide down (start top, end bottom)
                    y_start, y_end = 0.0, 1.0
                    direction = "slide_down"

                logger.info(f"Image taller than video ({image_aspect:.2f} vs {video_aspect:.2f}), using {direction}")
                return MotionParams(
                    pattern=direction,
                    zoom_start=1.0,
                    zoom_end=1.0,
                    x_start=0.5,  # Centered horizontally
                    y_start=y_start,
                    x_end=0.5,
                    y_end=y_end,
                )

        # Image roughly matches video aspect ratio - use zoom effects
        # Get base pattern from marker or default
        pattern_name = marker.motion.value if marker.motion else "slow_zoom_in"
        base_params = MOTION_PATTERNS.get(pattern_name, MOTION_PATTERNS["slow_zoom_in"])

        # Apply intensity scaling
        zoom_range = base_params["zoom_end"] - base_params["zoom_start"]
        scaled_zoom_end = base_params["zoom_start"] + (zoom_range * intensity)

        pan_range_x = base_params["x_end"] - base_params["x_start"]
        pan_range_y = base_params["y_end"] - base_params["y_start"]
        scaled_x_end = base_params["x_start"] + (pan_range_x * intensity)
        scaled_y_end = base_params["y_start"] + (pan_range_y * intensity)

        return MotionParams(
            pattern=pattern_name,
            zoom_start=base_params["zoom_start"],
            zoom_end=scaled_zoom_end,
            x_start=base_params["x_start"],
            y_start=base_params["y_start"],
            x_end=scaled_x_end,
            y_end=scaled_y_end,
        )

    def add_variety(self, spec: RenderSpec) -> RenderSpec:
        """
        Add variety to motion patterns to avoid repetition.

        Modifies segments to have alternating motion types with more dramatic effects.
        Preserves sliding patterns for mismatched aspect ratios.

        Args:
            spec: RenderSpec to modify

        Returns:
            Modified RenderSpec
        """
        # Expanded pattern pool for more variety
        zoom_patterns = ["slow_zoom_in", "slow_zoom_out", "zoom_in", "zoom_out"]
        pan_patterns = ["pan_left", "pan_right", "pan_up", "pan_down"]
        all_patterns = zoom_patterns + pan_patterns

        for i, segment in enumerate(spec.segments):
            # Skip if it's already a slide pattern (aspect ratio mismatch)
            if segment.motion.pattern.startswith("slide"):
                continue

            # Use alternating patterns for variety
            new_pattern = all_patterns[i % len(all_patterns)]
            base_params = MOTION_PATTERNS[new_pattern]

            # Apply intensity scaling
            zoom_range = base_params["zoom_end"] - base_params["zoom_start"]
            scaled_zoom_end = base_params["zoom_start"] + (zoom_range * self.intensity)

            pan_range_x = base_params["x_end"] - base_params["x_start"]
            pan_range_y = base_params["y_end"] - base_params["y_start"]
            scaled_x_end = base_params["x_start"] + (pan_range_x * self.intensity)
            scaled_y_end = base_params["y_start"] + (pan_range_y * self.intensity)

            segment.motion = MotionParams(
                pattern=new_pattern,
                zoom_start=base_params["zoom_start"],
                zoom_end=scaled_zoom_end,
                x_start=base_params["x_start"],
                y_start=base_params["y_start"],
                x_end=scaled_x_end,
                y_end=scaled_y_end,
            )

        return spec


def generate_motion(
    script: AnnotatedScript,
    audio: AudioOutput,
    images: ImageCollection,
    output_path: str,
    intensity: float = 0.5,
) -> RenderSpec:
    """
    Convenience function to generate render spec.

    Args:
        script: AnnotatedScript with visual markers
        audio: AudioOutput with timing
        images: ImageCollection with images
        output_path: Output video path
        intensity: Motion intensity (0-1)

    Returns:
        RenderSpec ready for rendering
    """
    engine = KenBurnsEngine(intensity=intensity)
    spec = engine.create_render_spec(script, audio, images, output_path)
    spec = engine.add_variety(spec)
    return spec
