# AI Ken Burns - Class Consciousness Video Generator

## Project Overview

This project generates Ken Burns style documentary videos that connect current news stories to historical class struggle events. The pipeline:

1. **Research**: Fetch news, find class-consciousness-relevant stories
2. **Historical Connection**: Use LLM to find parallel historical events
3. **Script Generation**: Create narration script with visual markers
4. **Audio**: Generate TTS audio from script
5. **Images**: Search and download relevant historical images
6. **Video**: Render Ken Burns effect video with pan/zoom effects

## Tech Stack

- **Python 3.10+** with type hints
- **OpenAI API** (GPT-4o for LLM, TTS-1 for voice) - uses `OPENAI_API_KEY` env var
- **FFmpeg** for video rendering (zoompan filter for Ken Burns effect)
- **Typer** for CLI
- **Rich** for console output
- **Pydantic** for data models
- **httpx** for HTTP requests
- **Pillow** for image processing

## Project Structure

```
ai_ken_burns/
  __init__.py           # Package init with version
  config.py             # Central configuration (LLM, TTS, Video, Paths)
  models.py             # Core Pydantic data models
  cli.py                # Typer CLI commands (8 commands)

  clients/
    openai_client.py    # OpenAI wrapper with retry logic

  utils/
    logging_utils.py    # Rich logging, timing metrics
    ffmpeg_utils.py     # FFmpeg helpers, Ken Burns filters

  research/
    models.py           # NewsStory, HistoricalEvent, ResearchOutput
    news_fetcher.py     # RSS fetching, relevance scoring
    historical_connector.py  # LLM historical connection

  script/
    models.py           # VisualMarker, ScriptSegment, AnnotatedScript
    generator.py        # LLM script generation

  audio/
    models.py           # AudioSegment, AudioOutput
    tts_generator.py    # OpenAI TTS generation

  images/
    models.py           # ImageResult, ImageCollection
    searcher.py         # Wikimedia/LoC image search
    manager.py          # Download, cache, manage images

  video/
    models.py           # VideoSegment, RenderSpec, MotionParams
    ken_burns.py        # Motion parameter generation
    renderer.py         # FFmpeg video rendering

  pipeline/
    orchestrator.py     # Centralized pipeline management
    errors.py           # Error handling and recovery
```

## CLI Commands

```bash
# Full pipeline - generates complete video from news
python -m ai_ken_burns.cli generate --topic labor --style "urgent documentary"

# Step-by-step pipeline
python -m ai_ken_burns.cli research-only --topic workers -o research.json
python -m ai_ken_burns.cli script-only research.json --duration 120 -o script.json
python -m ai_ken_burns.cli audio-only script.json --voice nova -o ./audio
python -m ai_ken_burns.cli images-only script.json --per-marker 5 -o ./images
python -m ai_ken_burns.cli render-only script.json audio.json images.json -o video.mp4

# Utility commands
python -m ai_ken_burns.cli info      # Show configuration and status
python -m ai_ken_burns.cli validate  # Validate dependencies
```

## Pipeline Flow

```
[generate --topic labor]
         |
         v
[Stage 1: Research] --> research.json
    - Fetch news from RSS
    - Score relevance to class consciousness
    - Find historical parallel via LLM
         |
         v
[Stage 2: Script] --> script.json
    - Generate narration with visual markers [v1], [v2]
    - Each marker has search terms, mood, motion suggestion
         |
         v
[Stage 3: Audio] --> audio/*.mp3 + audio_metadata.json
    - OpenAI TTS generation
    - Per-segment audio for precise timing
    - Calculate marker timing
         |
         v
[Stage 4: Images] --> images/*.jpg + collection.json
    - Search Wikimedia Commons, Library of Congress
    - Download and cache images
    - Map images to markers
         |
         v
[Stage 5: Motion] --> render_spec.json
    - Generate Ken Burns motion parameters
    - Zoom start/end, pan direction
    - Variety to avoid repetition
         |
         v
[Stage 6: Render] --> output.mp4
    - FFmpeg zoompan filter per segment
    - Concatenate segments
    - Merge audio track
```

## Configuration

Environment variables:
- `OPENAI_API_KEY` - Required for LLM and TTS

Default settings in `config.py`:
- Models: gpt-4o (research/generation), tts-1-hd (audio)
- Default voice: "onyx"
- Default resolution: 1920x1080 @ 30fps
- Ken Burns intensity: 0.5

## Testing

```bash
# Run all tests
python -m pytest tests/ -v -p no:vcr

# Run specific test file
python -m pytest tests/test_models.py -v

# With coverage
python -m pytest tests/ --cov=ai_ken_burns
```

## Development Status

**All Batches Complete:**

- Batch 1: Foundation (Config, Logging, OpenAI Client, CLI)
- Batch 2: Research Pipeline (News Fetcher, Historical Connector)
- Batch 3: Script & Audio (Script Generator, TTS Pipeline)
- Batch 4: Image Pipeline (Image Search, Image Manager)
- Batch 5: Video Pipeline (Ken Burns Engine, Video Renderer)
- Batch 6: Pipeline Polish (Orchestrator, Error Recovery)
- Batch 7: Testing (43 unit tests passing)

## Code Style

- Type hints everywhere
- Docstrings for public functions
- ASCII-only in output (Windows compatibility)
- Pydantic for data validation
- Rich for console output (no raw print)
- Exponential backoff for API retries
