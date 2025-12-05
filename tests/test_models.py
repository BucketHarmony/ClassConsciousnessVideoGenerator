"""
Unit tests for data models.
"""

import pytest
from datetime import datetime


class TestResearchModels:
    """Tests for research pipeline models."""

    def test_news_story_creation(self, sample_news_story):
        """Test NewsStory model creation."""
        assert sample_news_story.title == "Workers Strike for Better Wages"
        assert sample_news_story.relevance_score == 0.8
        assert "labor" in sample_news_story.themes

    def test_historical_event_creation(self, sample_historical_event):
        """Test HistoricalEvent model creation."""
        assert sample_historical_event.name == "Pullman Strike of 1894"
        assert sample_historical_event.year == 1894
        assert len(sample_historical_event.key_figures) == 2

    def test_research_output_prompt_context(self, sample_research_output):
        """Test ResearchOutput.to_prompt_context()."""
        context = sample_research_output.to_prompt_context()
        assert "Workers Strike" in context
        assert "Pullman Strike" in context
        assert "thesis" in context.lower()


class TestScriptModels:
    """Tests for script generation models."""

    def test_visual_marker_creation(self, sample_visual_marker):
        """Test VisualMarker model creation."""
        assert sample_visual_marker.id == "v1"
        assert sample_visual_marker.visual_type.value == "historical_photo"
        assert sample_visual_marker.motion.value == "slow_zoom_in"

    def test_script_segment_plain_text(self, sample_script_segment):
        """Test ScriptSegment.get_plain_text()."""
        plain = sample_script_segment.get_plain_text()
        assert "[v1]" not in plain
        assert "1894" in plain

    def test_script_segment_word_count(self, sample_script_segment):
        """Test ScriptSegment.word_count()."""
        count = sample_script_segment.word_count()
        assert count > 0

    def test_script_segment_duration_estimate(self, sample_script_segment):
        """Test ScriptSegment.estimate_duration()."""
        duration = sample_script_segment.estimate_duration()
        assert duration > 0

    def test_annotated_script_properties(self, sample_script):
        """Test AnnotatedScript computed properties."""
        assert sample_script.segment_count == 1
        assert sample_script.marker_count == 1
        assert len(sample_script.all_markers) == 1

    def test_annotated_script_full_text(self, sample_script):
        """Test AnnotatedScript.full_text property."""
        full = sample_script.full_text
        assert "[v1]" in full

    def test_annotated_script_plain_text(self, sample_script):
        """Test AnnotatedScript.plain_text property."""
        plain = sample_script.plain_text
        assert "[v1]" not in plain


class TestAudioModels:
    """Tests for audio pipeline models."""

    def test_audio_segment_validity(self, sample_audio_output):
        """Test AudioSegment.is_valid property."""
        segment = sample_audio_output.segments[0]
        assert segment.is_valid

    def test_audio_output_properties(self, sample_audio_output):
        """Test AudioOutput computed properties."""
        assert sample_audio_output.segment_count == 1
        assert sample_audio_output.total_duration == 30.0

    def test_audio_output_marker_timing(self, sample_audio_output):
        """Test AudioOutput.get_marker_time()."""
        timing = sample_audio_output.get_marker_time("v1")
        assert timing is not None
        assert timing == (0.0, 30.0)


class TestImageModels:
    """Tests for image pipeline models."""

    def test_image_result_properties(self, sample_image_result):
        """Test ImageResult computed properties."""
        assert sample_image_result.aspect_ratio == 1920 / 1080
        assert sample_image_result.is_landscape
        assert sample_image_result.is_usable

    def test_image_collection_properties(self, sample_image_collection):
        """Test ImageCollection computed properties."""
        assert sample_image_collection.image_count == 1
        assert sample_image_collection.downloaded_count == 1
        assert sample_image_collection.markers_covered == 1

    def test_image_collection_get_image(self, sample_image_collection):
        """Test ImageCollection.get_image_for_marker()."""
        img = sample_image_collection.get_image_for_marker("v1")
        assert img is not None
        assert img.id == "img001"


class TestVideoModels:
    """Tests for video pipeline models."""

    def test_motion_params_defaults(self):
        """Test MotionParams default values."""
        from ai_ken_burns.video.models import MotionParams

        params = MotionParams()
        assert params.zoom_start == 1.0
        assert params.pattern == "slow_zoom_in"

    def test_video_segment_duration(self):
        """Test VideoSegment.duration property."""
        from ai_ken_burns.video.models import VideoSegment, MotionParams

        segment = VideoSegment(
            id="test",
            order=0,
            image_path="/path/to/image.jpg",
            start_time=0.0,
            end_time=10.0,
            motion=MotionParams(),
        )
        assert segment.duration == 10.0

    def test_render_spec_properties(self):
        """Test RenderSpec computed properties."""
        from ai_ken_burns.video.models import RenderSpec

        spec = RenderSpec(
            project_id="test",
            audio_file="/path/to/audio.mp3",
            total_duration=60.0,
        )
        assert spec.segment_count == 0
        assert spec.resolution == (1920, 1080)
