# Testing Guide for AI Ken Burns Video Generator

This guide covers how to run and work with the unit test suite.

## Prerequisites

Ensure you have the development dependencies installed:

```bash
pip install pytest pytest-cov
```

## Running Tests

### Run All Tests

```bash
python -m pytest tests/ -v -p no:vcr
```

**Note:** The `-p no:vcr` flag disables the pytest-vcr plugin which can conflict with urllib3 on some systems.

### Run Specific Test Files

```bash
# Model tests (27 tests)
python -m pytest tests/test_models.py -v -p no:vcr

# Research pipeline tests (6 tests)
python -m pytest tests/test_research.py -v -p no:vcr

# Pipeline orchestrator tests (7 tests)
python -m pytest tests/test_pipeline.py -v -p no:vcr

# FFmpeg utility tests (8 tests)
python -m pytest tests/test_ffmpeg.py -v -p no:vcr
```

### Run Specific Test Classes

```bash
# Run all model tests for a specific domain
python -m pytest tests/test_models.py::TestResearchModels -v -p no:vcr
python -m pytest tests/test_models.py::TestScriptModels -v -p no:vcr
python -m pytest tests/test_models.py::TestAudioModels -v -p no:vcr
python -m pytest tests/test_models.py::TestImageModels -v -p no:vcr
python -m pytest tests/test_models.py::TestVideoModels -v -p no:vcr
```

### Run a Single Test

```bash
python -m pytest tests/test_models.py::TestResearchModels::test_news_story_creation -v -p no:vcr
```

## Test Coverage

### Generate Coverage Report

```bash
python -m pytest tests/ --cov=ai_ken_burns --cov-report=term-missing -p no:vcr
```

### Generate HTML Coverage Report

```bash
python -m pytest tests/ --cov=ai_ken_burns --cov-report=html -p no:vcr
```

This creates an `htmlcov/` directory. Open `htmlcov/index.html` in a browser to view the detailed coverage report.

## Test Structure

```
tests/
├── conftest.py        # Shared fixtures for all tests
├── test_models.py     # Data model tests (27 tests)
├── test_research.py   # Research pipeline tests (6 tests)
├── test_pipeline.py   # Pipeline orchestrator tests (7 tests)
└── test_ffmpeg.py     # FFmpeg utility tests (8 tests)
```

### Test Categories

| File | Tests | Description |
|------|-------|-------------|
| `test_models.py` | 27 | Tests for all Pydantic data models across research, script, audio, image, and video domains |
| `test_research.py` | 6 | Tests for news fetching, relevance scoring, theme identification, and historical connections |
| `test_pipeline.py` | 7 | Tests for pipeline errors, orchestrator initialization, and CLI commands |
| `test_ffmpeg.py` | 8 | Tests for FFmpeg availability checks, zoompan filter generation, and media processing |

## Available Fixtures

The `conftest.py` file provides these reusable fixtures:

| Fixture | Description |
|---------|-------------|
| `temp_dir` | Temporary directory for test artifacts |
| `sample_news_story` | Pre-populated NewsStory model |
| `sample_historical_event` | Pre-populated HistoricalEvent model |
| `sample_research_output` | Complete research output with story and event |
| `sample_visual_marker` | Visual marker with search terms |
| `sample_script_segment` | Script segment with embedded markers |
| `sample_script` | Complete annotated script |
| `sample_audio_output` | Audio output with timing data |
| `sample_image_result` | Image result with metadata |
| `sample_image_collection` | Collection of images for a project |
| `mock_openai_client` | Mocked OpenAI client (no API calls) |
| `mock_ffmpeg` | Mocked FFmpeg subprocess calls |

## Writing New Tests

### Example Test Using Fixtures

```python
class TestMyFeature:
    def test_with_fixture(self, sample_news_story, temp_dir):
        """Test using provided fixtures."""
        # sample_news_story is a NewsStory instance
        assert sample_news_story.title == "Workers Strike for Better Wages"

        # temp_dir is a Path to a temporary directory
        output_file = temp_dir / "output.txt"
        output_file.write_text("test")
        assert output_file.exists()
```

### Example Test with Mocking

```python
from unittest.mock import patch, MagicMock

class TestWithMocks:
    @patch("ai_ken_burns.module.external_function")
    def test_mocked_dependency(self, mock_func):
        """Test with mocked external dependency."""
        mock_func.return_value = {"result": "mocked"}

        # Your test code here
        from ai_ken_burns.module import function_under_test
        result = function_under_test()

        assert result == expected_value
        mock_func.assert_called_once()
```

## Troubleshooting

### pytest-vcr Conflict

If you see this error:
```
AttributeError: module 'urllib3.connectionpool' has no attribute 'VerifiedHTTPSConnection'
```

Add `-p no:vcr` to your pytest command to disable the vcr plugin.

### Import Errors

Ensure the package is installed in development mode:
```bash
pip install -e .
```

### Missing API Key Warnings

Tests mock external API calls, but some imports may check for API keys. The `conftest.py` sets a dummy key:
```python
os.environ.setdefault("OPENAI_API_KEY", "test-api-key-for-testing")
```

## Continuous Integration

For CI pipelines, use:

```bash
python -m pytest tests/ -v -p no:vcr --tb=short --junitxml=test-results.xml
```

This generates a JUnit XML report compatible with most CI systems.
