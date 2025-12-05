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

# Motion pattern definitions
MOTION_PATTERNS = {
    "slow_zoom_in": {
        "zoom_start": 1.0, "zoom_end": 1.15,
        "x_start": 0.5, "y_start": 0.5,
        "x_end": 0.5, "y_end": 0.5,
    },
    "slow_zoom_out": {
        "zoom_start": 1.15, "zoom_end": 1.0,
        "x_start": 0.5, "y_start": 0.5,
        "x_end": 0.5, "y_end": 0.5,
    },
    "zoom_in": {
        "zoom_start": 1.0, "zoom_end": 1.3,
        "x_start": 0.5, "y_start": 0.5,
        "x_end": 0.5, "y_end": 0.5,
    },
    "zoom_out": {
        "zoom_start": 1.3, "zoom_end": 1.0,
        "x_start": 0.5, "y_start": 0.5,
        "x_end": 0.5, "y_end": 0.5,
    },
    "pan_left": {
        "zoom_start": 1.15, "zoom_end": 1.15,
        "x_start": 0.7, "y_start": 0.5,
        "x_end": 0.3, "y_end": 0.5,
    },
    "pan_right": {
        "zoom_start": 1.15, "zoom_end": 1.15,
        "x_start": 0.3, "y_start": 0.5,
        "x_end": 0.7, "y_end": 0.5,
    },
    "pan_up": {
        "zoom_start": 1.15, "zoom_end": 1.15,
        "x_start": 0.5, "y_start": 0.7,
        "x_end": 0.5, "y_end": 0.3,
    },
    "pan_down": {
        "zoom_start": 1.15, "zoom_end": 1.15,
        "x_start": 0.5, "y_start": 0.3,
        "x_end": 0.5, "y_end": 0.7,
    },
    "static": {
        "zoom_start": 1.0, "zoom_end": 1.0,
        "x_start": 0.5, "y_start": 0.5,
        "x_end": 0.5, "y_end": 0.5,
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

            # Generate motion
            motion = self._generate_motion(marker, self.intensity)

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
    ) -> MotionParams:
        """
        Generate motion parameters for a visual marker.

        Args:
            marker: VisualMarker with motion suggestion
            intensity: Motion intensity (0-1)

        Returns:
            MotionParams for the segment
        """
        # Get base pattern
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

        Modifies segments to have alternating motion types.

        Args:
            spec: RenderSpec to modify

        Returns:
            Modified RenderSpec
        """
        # Alternate between zoom types
        zoom_patterns = ["slow_zoom_in", "slow_zoom_out", "zoom_in", "zoom_out"]
        pan_patterns = ["pan_left", "pan_right"]

        for i, segment in enumerate(spec.segments):
            if segment.motion.pattern == "slow_zoom_in":
                # Alternate zoom direction
                new_pattern = zoom_patterns[i % len(zoom_patterns)]
                base_params = MOTION_PATTERNS[new_pattern]

                segment.motion = MotionParams(
                    pattern=new_pattern,
                    zoom_start=base_params["zoom_start"],
                    zoom_end=base_params["zoom_start"] + (
                        (base_params["zoom_end"] - base_params["zoom_start"]) * self.intensity
                    ),
                    x_start=base_params["x_start"],
                    y_start=base_params["y_start"],
                    x_end=base_params["x_end"],
                    y_end=base_params["y_end"],
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
