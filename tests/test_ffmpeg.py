"""
Unit tests for FFmpeg utilities.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestFFmpegUtils:
    """Tests for FFmpeg utility functions."""

    @patch("ai_ken_burns.utils.ffmpeg_utils.subprocess.run")
    def test_check_ffmpeg_available(self, mock_run):
        """Test FFmpeg availability check when available."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ffmpeg version 5.1.2 Copyright (c) 2000-2022\n",
        )

        from ai_ken_burns.utils.ffmpeg_utils import check_ffmpeg

        available, version = check_ffmpeg()
        assert available
        assert "5.1.2" in version

    @patch("ai_ken_burns.utils.ffmpeg_utils.subprocess.run")
    def test_check_ffmpeg_not_found(self, mock_run):
        """Test FFmpeg availability check when not found."""
        mock_run.side_effect = FileNotFoundError("ffmpeg not found")

        from ai_ken_burns.utils.ffmpeg_utils import check_ffmpeg

        available, message = check_ffmpeg()
        assert not available
        assert "not found" in message.lower()

    def test_zoompan_filter_generation(self):
        """Test zoompan filter string generation."""
        from ai_ken_burns.utils.ffmpeg_utils import generate_zoompan_filter

        filter_str = generate_zoompan_filter(
            width=1920,
            height=1080,
            duration_seconds=5.0,
            fps=30,
            zoom_start=1.0,
            zoom_end=1.2,
        )

        assert "zoompan" in filter_str
        assert "1920x1080" in filter_str
        assert "fps=30" in filter_str

    def test_ken_burns_pattern_filters(self):
        """Test named Ken Burns pattern filters."""
        from ai_ken_burns.utils.ffmpeg_utils import get_ken_burns_filter_for_pattern

        patterns = [
            "zoom_in",
            "zoom_out",
            "pan_left",
            "pan_right",
            "static",
        ]

        for pattern in patterns:
            filter_str = get_ken_burns_filter_for_pattern(
                pattern=pattern,
                width=1920,
                height=1080,
                duration=5.0,
                fps=30,
            )
            assert "zoompan" in filter_str

    def test_ken_burns_intensity_scaling(self):
        """Test intensity affects zoom range."""
        from ai_ken_burns.utils.ffmpeg_utils import get_ken_burns_filter_for_pattern

        low_intensity = get_ken_burns_filter_for_pattern(
            pattern="zoom_in",
            width=1920,
            height=1080,
            duration=5.0,
            fps=30,
            intensity=0.1,
        )

        high_intensity = get_ken_burns_filter_for_pattern(
            pattern="zoom_in",
            width=1920,
            height=1080,
            duration=5.0,
            fps=30,
            intensity=1.0,
        )

        # Different intensities should produce different filters
        assert low_intensity != high_intensity

    @patch("ai_ken_burns.utils.ffmpeg_utils.subprocess.run")
    def test_get_media_duration(self, mock_run):
        """Test media duration extraction."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="45.123456\n",
            stderr="",
        )

        from ai_ken_burns.utils.ffmpeg_utils import get_media_duration

        duration = get_media_duration("/path/to/audio.mp3")
        assert duration == pytest.approx(45.123456)

    @patch("ai_ken_burns.utils.ffmpeg_utils.subprocess.run")
    def test_run_ffmpeg_success(self, mock_run):
        """Test successful FFmpeg command execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success",
            stderr="",
        )

        from ai_ken_burns.utils.ffmpeg_utils import run_ffmpeg

        success, output = run_ffmpeg(["-version"])
        assert success

    @patch("ai_ken_burns.utils.ffmpeg_utils.subprocess.run")
    def test_run_ffmpeg_failure(self, mock_run):
        """Test FFmpeg command failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: invalid option",
        )

        from ai_ken_burns.utils.ffmpeg_utils import run_ffmpeg

        success, error = run_ffmpeg(["--invalid-option"])
        assert not success
        assert "invalid" in error.lower()
