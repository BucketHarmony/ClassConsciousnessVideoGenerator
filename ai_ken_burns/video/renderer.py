"""
Video renderer for AI Ken Burns.

Uses FFmpeg to render Ken Burns effect videos with audio.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from ai_ken_burns.config import get_config
from ai_ken_burns.video.models import RenderSpec, VideoSegment
from ai_ken_burns.utils.ffmpeg_utils import (
    run_ffmpeg,
    generate_zoompan_filter,
    check_ffmpeg,
)
from ai_ken_burns.utils.logging_utils import get_video_logger, log_timing

logger = get_video_logger()


class VideoRenderer:
    """
    Renders Ken Burns effect videos using FFmpeg.

    Process:
    1. Render each segment with zoompan filter
    2. Concatenate all segments
    3. Add audio track
    4. Produce final output
    """

    def __init__(self, temp_dir: Optional[Path] = None) -> None:
        """
        Initialize the video renderer.

        Args:
            temp_dir: Directory for temporary files
        """
        self.config = get_config()
        self.temp_dir = temp_dir or Path(self.config.paths.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Check FFmpeg availability
        ffmpeg_ok, ffmpeg_version = check_ffmpeg()
        if not ffmpeg_ok:
            raise RuntimeError(f"FFmpeg not available: {ffmpeg_version}")
        logger.info(f"Using FFmpeg: {ffmpeg_version}")

    def render(self, spec: RenderSpec) -> bool:
        """
        Render the complete video.

        Args:
            spec: RenderSpec with segments and settings

        Returns:
            True if successful
        """
        logger.info(f"Rendering video: {spec.title}")
        logger.info(f"Resolution: {spec.width}x{spec.height} @ {spec.fps}fps")
        logger.info(f"Segments: {spec.segment_count}, Duration: {spec.total_duration:.1f}s")

        # Create project temp directory
        project_temp = self.temp_dir / spec.project_id
        project_temp.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Render each segment
            with log_timing("render_segments", logger):
                for segment in spec.segments:
                    success = self._render_segment(segment, spec, project_temp)
                    if not success:
                        logger.error(f"Failed to render segment {segment.id}")
                        return False

            # Step 2: Concatenate segments
            with log_timing("concatenate_segments", logger):
                video_only_path = project_temp / "video_only.mp4"
                success = self._concatenate_segments(spec, video_only_path)
                if not success:
                    logger.error("Failed to concatenate segments")
                    return False

            # Step 3: Add audio
            with log_timing("add_audio", logger):
                output_path = Path(spec.output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                success = self._add_audio(video_only_path, spec.audio_file, output_path)
                if not success:
                    logger.error("Failed to add audio")
                    return False

            spec.rendered_at = datetime.now()
            logger.info(f"Video rendered successfully: {spec.output_path}")

            return True

        except Exception as e:
            logger.error(f"Render failed: {e}")
            return False

    def _render_segment(
        self,
        segment: VideoSegment,
        spec: RenderSpec,
        temp_dir: Path,
    ) -> bool:
        """Render a single segment with Ken Burns effect."""
        logger.debug(f"Rendering segment [{segment.id}]: {segment.duration:.1f}s")
        logger.debug(f"Motion: {segment.motion.pattern} zoom={segment.motion.zoom_start:.2f}->{segment.motion.zoom_end:.2f}")
        logger.debug(f"Pan: x={segment.motion.x_start:.2f}->{segment.motion.x_end:.2f}, y={segment.motion.y_start:.2f}->{segment.motion.y_end:.2f}")

        output_path = temp_dir / f"segment_{segment.order:03d}.mp4"

        # Determine scaling strategy based on image vs video aspect ratio
        img_w = segment.image_width or spec.width
        img_h = segment.image_height or spec.height
        img_aspect = img_w / img_h
        video_aspect = spec.width / spec.height

        # Scale so shorter side fits video, longer side extends for panning
        if img_aspect > video_aspect:
            # Image is wider - fit height, pan horizontally
            scale_filter = f"scale=-1:{spec.height}"
            # Calculate how much wider the scaled image is
            scaled_width = int(spec.height * img_aspect)
            pan_ratio = scaled_width / spec.width  # e.g., 1.78 for 16:9 on square
        else:
            # Image is taller - fit width, pan vertically
            scale_filter = f"scale={spec.width}:-1"
            scaled_height = int(spec.width / img_aspect)
            pan_ratio = scaled_height / spec.height

        # Generate zoompan filter with the actual pan ratio
        zoompan_filter = generate_zoompan_filter(
            width=spec.width,
            height=spec.height,
            duration_seconds=segment.duration,
            fps=spec.fps,
            zoom_start=segment.motion.zoom_start,
            zoom_end=segment.motion.zoom_end,
            x_start=segment.motion.x_start,
            y_start=segment.motion.y_start,
            x_end=segment.motion.x_end,
            y_end=segment.motion.y_end,
            pan_ratio=pan_ratio,
        )

        # Build filter: scale to fit shorter side, then zoompan for motion
        filter_complex = (
            f"{scale_filter},"
            f"setsar=1,"
            f"{zoompan_filter},"
            f"format=yuv420p"
        )

        # Build args - skip -loop for GIFs (not supported)
        image_path = segment.image_path
        is_gif = image_path.lower().endswith('.gif')

        args = ["-y"]
        if not is_gif:
            args.extend(["-loop", "1"])
        args.extend([
            "-i", image_path,
            "-t", str(segment.duration),
            "-vf", filter_complex,
            "-c:v", self.config.video.video_codec,
            "-preset", "medium",
            "-crf", "23",
            "-an",  # No audio for segments
            str(output_path),
        ])

        success, error = run_ffmpeg(args, timeout=300)

        if success:
            segment.temp_video_path = str(output_path)
            segment.is_rendered = True
            logger.debug(f"Segment [{segment.id}] rendered: {output_path.name}")
        else:
            logger.error(f"Segment [{segment.id}] failed: {error}")

        return success

    def _concatenate_segments(
        self,
        spec: RenderSpec,
        output_path: Path,
    ) -> bool:
        """Concatenate all rendered segments."""
        logger.debug(f"Concatenating {spec.rendered_count} segments")

        # Create concat file
        concat_file = output_path.parent / "concat_list.txt"
        with open(concat_file, "w") as f:
            for segment in sorted(spec.segments, key=lambda s: s.order):
                if segment.temp_video_path:
                    # Escape path for FFmpeg
                    escaped = segment.temp_video_path.replace("\\", "/").replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

        # Concatenate
        args = [
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(output_path),
        ]

        success, error = run_ffmpeg(args, timeout=300)

        # Clean up concat file
        concat_file.unlink(missing_ok=True)

        if not success:
            logger.error(f"Concatenation failed: {error}")

        return success

    def _add_audio(
        self,
        video_path: Path,
        audio_path: str,
        output_path: Path,
    ) -> bool:
        """Add audio track to video, ensuring full audio plays."""
        logger.debug(f"Adding audio: {audio_path}")

        # Don't use -shortest - we want full audio duration
        # If video is shorter than audio, the last frame will be held
        args = [
            "-y",
            "-i", str(video_path),
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", self.config.video.audio_codec,
            "-map", "0:v:0",
            "-map", "1:a:0",
            str(output_path),
        ]

        success, error = run_ffmpeg(args, timeout=300)

        if not success:
            logger.error(f"Audio merge failed: {error}")

        return success

    def cleanup_temp_files(self, spec: RenderSpec) -> None:
        """Clean up temporary segment files."""
        for segment in spec.segments:
            if segment.temp_video_path:
                try:
                    Path(segment.temp_video_path).unlink(missing_ok=True)
                except Exception as e:
                    logger.debug(f"Could not delete temp file: {e}")


def render_video(
    spec: RenderSpec,
    cleanup: bool = True,
) -> bool:
    """
    Convenience function to render a video.

    Args:
        spec: RenderSpec with all render information
        cleanup: Whether to clean up temp files after

    Returns:
        True if successful
    """
    renderer = VideoRenderer()
    success = renderer.render(spec)

    if cleanup and success:
        renderer.cleanup_temp_files(spec)

    return success
