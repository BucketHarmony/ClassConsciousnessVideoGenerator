"""
Pytest configuration and shared fixtures for AI Ken Burns tests.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


# Set test environment
os.environ.setdefault("OPENAI_API_KEY", "test-api-key-for-testing")


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test artifacts."""
    return tmp_path


@pytest.fixture
def sample_news_story():
    """Sample news story for testing."""
    from ai_ken_burns.research.models import NewsStory

    return NewsStory(
        title="Workers Strike for Better Wages",
        summary="Thousands of workers walked off the job demanding higher pay and better conditions.",
        link="https://example.com/news/strike",
        source="Test News",
        relevance_score=0.8,
        relevance_keywords=["workers", "strike", "wages"],
        themes=["labor", "activism"],
    )


@pytest.fixture
def sample_historical_event():
    """Sample historical event for testing."""
    from ai_ken_burns.research.models import HistoricalEvent

    return HistoricalEvent(
        name="Pullman Strike of 1894",
        year=1894,
        location="Chicago, Illinois",
        summary="A nationwide railroad strike that began at the Pullman Company.",
        significance="One of the most significant labor disputes in American history.",
        connection_rationale="Both involve workers striking for fair wages.",
        parallel_themes=["labor", "wages", "worker solidarity"],
        key_figures=["Eugene V. Debs", "George Pullman"],
        key_facts=["Involved 250,000 workers", "Led to federal intervention"],
        suggested_imagery=["railroad workers", "strike protest", "Pullman town"],
    )


@pytest.fixture
def sample_research_output(sample_news_story, sample_historical_event):
    """Sample research output for testing."""
    from ai_ken_burns.research.models import ResearchOutput

    return ResearchOutput(
        news_story=sample_news_story,
        historical_event=sample_historical_event,
        thesis="History repeats as workers organize for fair treatment.",
        narrative_angle="Documentary connecting past and present labor struggles.",
        confidence_score=0.85,
        stories_analyzed=5,
    )


@pytest.fixture
def sample_visual_marker():
    """Sample visual marker for testing."""
    from ai_ken_burns.script.models import VisualMarker, VisualType, MotionSuggestion

    return VisualMarker(
        id="v1",
        description="Historical photo of striking workers",
        search_terms=["1894 strike", "railroad workers", "labor protest"],
        visual_type=VisualType.HISTORICAL_PHOTO,
        mood="determined",
        motion=MotionSuggestion.SLOW_ZOOM_IN,
        era="1890s",
        location="Chicago",
    )


@pytest.fixture
def sample_script_segment(sample_visual_marker):
    """Sample script segment for testing."""
    from ai_ken_burns.script.models import ScriptSegment

    return ScriptSegment(
        id=1,
        text="[v1] In 1894, workers at the Pullman Company faced impossible conditions.",
        visual_markers=[sample_visual_marker],
        mood="somber",
        pacing="slow",
    )


@pytest.fixture
def sample_script(sample_script_segment):
    """Sample annotated script for testing."""
    from ai_ken_burns.script.models import AnnotatedScript

    return AnnotatedScript(
        title="Class Consciousness: Then and Now",
        news_title="Workers Strike for Better Wages",
        historical_event="Pullman Strike of 1894",
        thesis="History repeats as workers organize.",
        style="documentary",
        tone="thoughtful",
        segments=[sample_script_segment],
    )


@pytest.fixture
def sample_audio_output(temp_dir):
    """Sample audio output for testing."""
    from ai_ken_burns.audio.models import AudioOutput, AudioSegment

    # Create a dummy audio file
    audio_file = temp_dir / "narration.mp3"
    audio_file.write_bytes(b"fake audio data")

    return AudioOutput(
        audio_file=str(audio_file),
        total_duration=30.0,
        segments=[
            AudioSegment(
                id=1,
                file_path=str(audio_file),
                start_time=0.0,
                end_time=30.0,
                duration=30.0,
                text="Test narration text",
                word_count=3,
            )
        ],
        marker_times={"v1": (0.0, 30.0)},
        model="tts-1",
        voice="onyx",
        total_words=100,
        average_wpm=200,
    )


@pytest.fixture
def sample_image_result(temp_dir):
    """Sample image result for testing."""
    from ai_ken_burns.images.models import ImageResult

    # Create a dummy image file
    image_file = temp_dir / "test_image.jpg"
    image_file.write_bytes(b"fake image data")

    return ImageResult(
        id="img001",
        marker_id="v1",
        source_url="https://example.com/image.jpg",
        source_name="Test Source",
        title="Test Image",
        local_path=str(image_file),
        is_downloaded=True,
        width=1920,
        height=1080,
        description="A test image",
        relevance_score=0.9,
    )


@pytest.fixture
def sample_image_collection(sample_image_result, temp_dir):
    """Sample image collection for testing."""
    from ai_ken_burns.images.models import ImageCollection

    return ImageCollection(
        project_id="test123",
        script_title="Test Script",
        images=[sample_image_result],
        marker_images={"v1": "img001"},
        images_dir=str(temp_dir),
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing without API calls."""
    with patch("ai_ken_burns.clients.openai_client.OpenAI") as mock:
        client = MagicMock()
        mock.return_value = client

        # Mock chat completion
        chat_response = MagicMock()
        chat_response.choices = [MagicMock()]
        chat_response.choices[0].message.content = '{"test": "response"}'
        chat_response.usage.total_tokens = 100
        client.chat.completions.create.return_value = chat_response

        yield client


@pytest.fixture
def mock_ffmpeg():
    """Mock FFmpeg for testing without actual video processing."""
    with patch("ai_ken_burns.utils.ffmpeg_utils.subprocess.run") as mock:
        result = MagicMock()
        result.returncode = 0
        result.stdout = "ffmpeg version 5.0"
        result.stderr = ""
        mock.return_value = result
        yield mock
