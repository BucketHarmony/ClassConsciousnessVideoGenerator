"""
TTS generator for AI Ken Burns.

Uses OpenAI TTS API to generate narration audio from scripts,
with timing calculation for visual marker synchronization.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from ai_ken_burns.clients.openai_client import get_openai_client
from ai_ken_burns.config import get_config
from ai_ken_burns.script.models import AnnotatedScript, ScriptSegment
from ai_ken_burns.audio.models import AudioOutput, AudioSegment
from ai_ken_burns.utils.ffmpeg_utils import get_media_duration
from ai_ken_burns.utils.logging_utils import get_audio_logger, log_timing

logger = get_audio_logger()


class TTSGenerator:
    """
    Generates audio from annotated scripts using OpenAI TTS.

    Handles:
    - Full script audio generation
    - Per-segment audio generation (for precise timing)
    - Visual marker timing calculation
    """

    def __init__(
        self,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> None:
        """
        Initialize the TTS generator.

        Args:
            voice: TTS voice (defaults to config)
            model: TTS model (defaults to config)
            speed: Speech speed (defaults to config)
        """
        self.config = get_config()
        self.client = get_openai_client()

        self.voice = voice or self.config.tts.voice
        self.model = model or self.config.tts.model
        self.speed = speed or self.config.tts.speed

    def generate(
        self,
        script: AnnotatedScript,
        output_dir: Path,
        generate_segments: bool = True,
    ) -> Optional[AudioOutput]:
        """
        Generate audio from an annotated script.

        Args:
            script: AnnotatedScript to convert to audio
            output_dir: Directory to save audio files
            generate_segments: Whether to generate per-segment audio

        Returns:
            AudioOutput with timing information, or None if failed
        """
        logger.info(f"Generating audio for script: {script.title}")
        logger.info(f"Voice: {self.voice}, Model: {self.model}, Speed: {self.speed}")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if generate_segments:
            return self._generate_segmented(script, output_dir)
        else:
            return self._generate_full(script, output_dir)

    def _generate_full(
        self,
        script: AnnotatedScript,
        output_dir: Path,
    ) -> Optional[AudioOutput]:
        """Generate single audio file for full script."""
        # Get plain text (without markers)
        full_text = script.plain_text

        logger.info(f"Generating full audio ({len(full_text)} chars)")

        output_path = output_dir / "narration.mp3"

        with log_timing("tts_full_audio", logger):
            response = self.client.text_to_speech(
                text=full_text,
                output_path=str(output_path),
                model=self.model,
                voice=self.voice,
                speed=self.speed,
            )

        if not response.success:
            logger.error(f"TTS generation failed: {response.error}")
            return None

        # Get actual duration
        duration = get_media_duration(str(output_path))
        if duration is None:
            logger.error("Failed to get audio duration")
            return None

        # Calculate estimated timing per segment
        segments = self._estimate_segment_timing(script, duration)

        # Calculate marker timing
        marker_times = self._calculate_marker_times(script, segments)

        word_count = len(full_text.split())

        output = AudioOutput(
            audio_file=str(output_path),
            total_duration=duration,
            segments=segments,
            marker_times=marker_times,
            model=self.model,
            voice=self.voice,
            total_words=word_count,
            average_wpm=(word_count / duration) * 60 if duration > 0 else None,
        )

        logger.info(
            f"Audio generated: {duration:.1f}s, "
            f"{len(segments)} segments, "
            f"{len(marker_times)} markers"
        )

        return output

    def _generate_segmented(
        self,
        script: AnnotatedScript,
        output_dir: Path,
    ) -> Optional[AudioOutput]:
        """Generate separate audio files per segment for precise timing."""
        segments = []
        current_time = 0.0
        total_words = 0

        logger.info(f"Generating {len(script.segments)} segment audio files")

        for i, seg in enumerate(script.segments):
            plain_text = seg.get_plain_text()
            if not plain_text.strip():
                continue

            segment_path = output_dir / f"segment_{i + 1:02d}.mp3"

            with log_timing(f"tts_segment_{i + 1}", logger):
                response = self.client.text_to_speech(
                    text=plain_text,
                    output_path=str(segment_path),
                    model=self.model,
                    voice=self.voice,
                    speed=self.speed,
                )

            if not response.success:
                logger.error(f"TTS failed for segment {i + 1}: {response.error}")
                continue

            # Get segment duration
            duration = get_media_duration(str(segment_path))
            if duration is None:
                logger.warning(f"Could not get duration for segment {i + 1}")
                duration = seg.estimate_duration()

            word_count = seg.word_count()

            audio_segment = AudioSegment(
                id=seg.id,
                file_path=str(segment_path),
                start_time=current_time,
                end_time=current_time + duration,
                duration=duration,
                text=plain_text,
                word_count=word_count,
                words_per_minute=(word_count / duration) * 60 if duration > 0 else None,
            )

            segments.append(audio_segment)
            current_time += duration
            total_words += word_count

        if not segments:
            logger.error("No segments generated")
            return None

        # Concatenate segments into single file
        main_audio_path = output_dir / "narration.mp3"
        concat_success = self._concatenate_segments(segments, main_audio_path)

        if not concat_success:
            # Fall back to using individual segment files
            # The renderer will need to handle multiple audio files
            logger.warning("Audio concatenation failed, using first segment as main audio")
            main_audio_path = Path(segments[0].file_path)

        total_duration = sum(s.duration for s in segments)

        # Calculate marker timing from segment timing
        marker_times = self._calculate_marker_times_from_segments(script, segments)

        output = AudioOutput(
            audio_file=str(main_audio_path),
            total_duration=total_duration,
            segments=segments,
            marker_times=marker_times,
            model=self.model,
            voice=self.voice,
            total_words=total_words,
            average_wpm=(total_words / total_duration) * 60 if total_duration > 0 else None,
        )

        logger.info(
            f"Segmented audio complete: {total_duration:.1f}s, "
            f"{len(segments)} segments, "
            f"{len(marker_times)} markers"
        )

        return output

    def _concatenate_segments(
        self,
        segments: list[AudioSegment],
        output_path: Path,
    ) -> bool:
        """Concatenate segment audio files using FFmpeg."""
        from ai_ken_burns.utils.ffmpeg_utils import run_ffmpeg

        if len(segments) == 1:
            # Just copy the single segment
            import shutil
            shutil.copy(segments[0].file_path, output_path)
            return True

        # Create concat file list
        concat_list_path = output_path.parent / "concat_list.txt"
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for seg in segments:
                # FFmpeg concat needs forward slashes and escaped quotes
                escaped_path = seg.file_path.replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")

        # Run FFmpeg concat with re-encoding for MP3 compatibility
        # Use filter_complex to concatenate audio streams properly
        args = [
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_path),
            "-c:a", "libmp3lame",
            "-q:a", "2",  # High quality VBR
            str(output_path),
        ]

        success, error = run_ffmpeg(args)

        # Clean up concat list
        concat_list_path.unlink(missing_ok=True)

        if not success:
            logger.error(f"Failed to concatenate audio: {error}")
            return False

        return True

    def _estimate_segment_timing(
        self,
        script: AnnotatedScript,
        total_duration: float,
    ) -> list[AudioSegment]:
        """Estimate segment timing proportionally."""
        segments = []

        # Calculate total estimated time
        total_estimate = sum(seg.estimate_duration() for seg in script.segments)
        if total_estimate == 0:
            return []

        current_time = 0.0

        for seg in script.segments:
            plain_text = seg.get_plain_text()
            if not plain_text.strip():
                continue

            # Scale segment duration proportionally
            seg_estimate = seg.estimate_duration()
            duration = (seg_estimate / total_estimate) * total_duration

            audio_segment = AudioSegment(
                id=seg.id,
                file_path="",  # No separate file in full mode
                start_time=current_time,
                end_time=current_time + duration,
                duration=duration,
                text=plain_text,
                word_count=seg.word_count(),
            )

            segments.append(audio_segment)
            current_time += duration

        return segments

    def _calculate_marker_times(
        self,
        script: AnnotatedScript,
        segments: list[AudioSegment],
    ) -> dict[str, tuple[float, float]]:
        """Calculate visual marker times based on segment timing."""
        marker_times = {}

        for script_seg, audio_seg in zip(script.segments, segments):
            if not script_seg.visual_markers:
                continue

            # Distribute markers evenly within segment
            marker_count = len(script_seg.visual_markers)
            marker_duration = audio_seg.duration / marker_count

            for i, marker in enumerate(script_seg.visual_markers):
                start = audio_seg.start_time + (i * marker_duration)
                end = start + marker_duration
                marker_times[marker.id] = (start, end)

        return marker_times

    def _calculate_marker_times_from_segments(
        self,
        script: AnnotatedScript,
        segments: list[AudioSegment],
    ) -> dict[str, tuple[float, float]]:
        """Calculate marker times from actual segment timing."""
        marker_times = {}

        # Create mapping from script segment ID to audio segment
        audio_seg_map = {seg.id: seg for seg in segments}

        for script_seg in script.segments:
            audio_seg = audio_seg_map.get(script_seg.id)
            if not audio_seg or not script_seg.visual_markers:
                continue

            # Find marker positions in text
            marker_positions = self._find_marker_positions(
                script_seg.text,
                [m.id for m in script_seg.visual_markers],
            )

            # Calculate timing based on text position
            for marker in script_seg.visual_markers:
                rel_start, rel_end = marker_positions.get(
                    marker.id,
                    (0.0, 1.0 / len(script_seg.visual_markers))
                )

                abs_start = audio_seg.start_time + (rel_start * audio_seg.duration)
                abs_end = audio_seg.start_time + (rel_end * audio_seg.duration)

                marker_times[marker.id] = (abs_start, abs_end)

        return marker_times

    def _find_marker_positions(
        self,
        text: str,
        marker_ids: list[str],
    ) -> dict[str, tuple[float, float]]:
        """Find relative positions of markers in text."""
        positions = {}

        # Find all marker positions
        total_len = len(text)
        if total_len == 0:
            return positions

        marker_locs = []
        for marker_id in marker_ids:
            pattern = rf'\[{re.escape(marker_id)}\]'
            match = re.search(pattern, text)
            if match:
                marker_locs.append((marker_id, match.start()))
            else:
                marker_locs.append((marker_id, 0))

        # Sort by position
        marker_locs.sort(key=lambda x: x[1])

        # Calculate relative positions
        for i, (marker_id, pos) in enumerate(marker_locs):
            rel_start = pos / total_len

            # End at next marker or end of segment
            if i + 1 < len(marker_locs):
                rel_end = marker_locs[i + 1][1] / total_len
            else:
                rel_end = 1.0

            positions[marker_id] = (rel_start, rel_end)

        return positions


def generate_audio(
    script: AnnotatedScript,
    output_dir: Path,
    voice: Optional[str] = None,
    generate_segments: bool = True,
) -> Optional[AudioOutput]:
    """
    Convenience function to generate audio from a script.

    Args:
        script: AnnotatedScript to convert to audio
        output_dir: Directory to save audio files
        voice: Optional voice override
        generate_segments: Whether to generate per-segment audio

    Returns:
        AudioOutput with timing information
    """
    generator = TTSGenerator(voice=voice)
    return generator.generate(script, output_dir, generate_segments)
