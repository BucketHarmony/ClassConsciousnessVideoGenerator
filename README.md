# AI Ken Burns - Class Consciousness Video Generator

Automatically generate documentary-style videos connecting today's news to historical class struggles. Uses AI to research, write scripts, generate narration, find/create images, and render Ken Burns effect videos ready for TikTok, YouTube Shorts, or Instagram Reels.

## Features

- **Automated Research**: Fetches current news and finds historically relevant class consciousness stories
- **AI Script Generation**: GPT-4o writes compelling documentary narration with visual cues
- **Text-to-Speech**: High-quality OpenAI TTS narration with multiple voice options
- **Smart Image Sourcing**: Google Images search with AI-generated fallback via DALL-E
- **Ken Burns Effect**: Professional pan/zoom animations on still images
- **Multi-Format Output**: Supports TikTok vertical (9:16), landscape (16:9), and square (1:1)
- **Auto-Publish**: Direct upload to TikTok with browser automation

## Quick Start

### Prerequisites

- Python 3.10+
- FFmpeg (must be in PATH)
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/ai-ken-burns.git
cd ai-ken-burns

# Install dependencies
pip install -e .

# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."  # Linux/Mac
$env:OPENAI_API_KEY="sk-..."    # Windows PowerShell
```

### Generate Your First Video

```bash
# Generate a standard 16:9 documentary video
ai-ken-burns generate

# Generate a TikTok-ready vertical video
ai-ken-burns generate --resolution tiktok

# Generate with AI images only (no web search)
ai-ken-burns generate --resolution tiktok --ai-images-only

# Generate and auto-publish to TikTok
ai-ken-burns generate --resolution tiktok --publish
```

## Usage

### Full Pipeline Commands

```bash
# Basic generation
ai-ken-burns generate

# Filter by topic
ai-ken-burns generate --topic labor
ai-ken-burns generate --topic housing
ai-ken-burns generate --topic economy

# Custom style
ai-ken-burns generate --style "urgent, passionate documentary"

# Video format options
ai-ken-burns generate --resolution tiktok      # 1080x1920 (vertical)
ai-ken-burns generate --resolution 1080p       # 1920x1080 (landscape)
ai-ken-burns generate --resolution square      # 1080x1080
ai-ken-burns generate --resolution 4k          # 3840x2160

# Image options
ai-ken-burns generate --ai-images              # Use DALL-E as fallback (default)
ai-ken-burns generate --no-ai-images           # Web search only
ai-ken-burns generate --ai-images-only         # DALL-E only, skip web search

# Output options
ai-ken-burns generate --output my_video.mp4
ai-ken-burns generate --fps 60
ai-ken-burns generate --ken-burns-intensity 0.8
```

### Step-by-Step Pipeline

Run each stage separately for more control:

```bash
# Stage 1: Research - fetch news and find historical connection
ai-ken-burns research-only --topic workers -o research.json

# Stage 2: Script - generate narration with visual markers
ai-ken-burns script-only research.json --duration 120 -o script.json

# Stage 3: Audio - generate TTS narration
ai-ken-burns audio-only script.json --voice nova -o ./audio

# Stage 4: Images - gather images for visual markers
ai-ken-burns images-only script.json --per-marker 5 -o ./images

# Stage 5: Render - create final video
ai-ken-burns render-only script.json audio/audio_metadata.json images/collection.json -o video.mp4
```

### Publishing to TikTok

```bash
# Setup TikTok (shows cookie export instructions)
ai-ken-burns tiktok-setup

# Publish existing video
ai-ken-burns publish video.mp4 -d "History repeats itself"

# Publish with custom hashtags
ai-ken-burns publish video.mp4 -d "Labor history" --hashtags "history,labor,documentary"

# Generate and publish in one command
ai-ken-burns generate --resolution tiktok --publish
```

See [TIKTOK_SETUP.md](TIKTOK_SETUP.md) for detailed TikTok publishing instructions.

### Utility Commands

```bash
# Show configuration and system status
ai-ken-burns info

# Validate all dependencies
ai-ken-burns validate
```

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Ken Burns Pipeline                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [News RSS]  ──►  [Research]  ──►  [Script]  ──►  [Audio]       │
│                       │              │              │            │
│                       ▼              ▼              ▼            │
│               research.json    script.json    audio.mp3         │
│                                      │                           │
│                                      ▼                           │
│                               [Image Search]                     │
│                               + [DALL-E AI]                      │
│                                      │                           │
│                                      ▼                           │
│                               [Ken Burns]                        │
│                               [Renderer]                         │
│                                      │                           │
│                                      ▼                           │
│                               output.mp4  ──►  [TikTok]         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

1. **Research**: Fetches news from Google News RSS, scores stories for class consciousness relevance, and uses GPT-4o to find historical parallels (strikes, labor movements, economic struggles)

2. **Script Generation**: GPT-4o creates a documentary narration script with embedded visual markers `[v1]`, `[v2]`, etc. Each marker includes image search terms, mood, and camera motion suggestions

3. **Audio Generation**: OpenAI TTS-1-HD generates high-quality narration. Segments are timed to calculate when each visual marker should appear

4. **Image Gathering**:
   - Primary: Google Images search prioritizing news sites (fair use)
   - Fallback: DALL-E 3 generates documentary-style images
   - Images are matched to visual markers from the script

5. **Ken Burns Rendering**: FFmpeg applies pan/zoom effects to each image segment, concatenates them, and merges the audio track

6. **Publishing** (Optional): Browser automation uploads the finished video to TikTok with auto-generated description and hashtags

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT-4, TTS, and DALL-E |
| `TIKTOK_COOKIES_PATH` | No | Path to TikTok cookies file for publishing |
| `LOG_LEVEL` | No | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Default Settings

- **LLM Model**: gpt-4o (research and script generation)
- **TTS Model**: tts-1-hd with "onyx" voice
- **Video**: 1920x1080 @ 30fps, H.264 codec
- **Ken Burns Intensity**: 0.5 (range: 0.0-1.0)
- **Default Hashtags**: #history #classconsciousness #laborhistory #documentary

### Resolution Presets

| Preset | Resolution | Aspect Ratio | Use Case |
|--------|------------|--------------|----------|
| `tiktok` | 1080x1920 | 9:16 | TikTok, Reels, Shorts |
| `reels` | 1080x1920 | 9:16 | Instagram Reels |
| `shorts` | 1080x1920 | 9:16 | YouTube Shorts |
| `vertical` | 1080x1920 | 9:16 | Generic vertical |
| `square` | 1080x1080 | 1:1 | Instagram feed |
| `1080p` | 1920x1080 | 16:9 | YouTube, standard |
| `4k` | 3840x2160 | 16:9 | High resolution |

## Project Structure

```
ai_ken_burns/
├── __init__.py           # Package version
├── cli.py                # Typer CLI (11 commands)
├── config.py             # Configuration management
│
├── clients/
│   └── openai_client.py  # OpenAI API wrapper with retry logic
│
├── prompts/              # Centralized prompt templates
│   ├── templates.py      # PromptTemplate class
│   ├── research.py       # Historical connection prompts
│   ├── script.py         # Script generation prompts
│   └── image.py          # DALL-E image prompts
│
├── research/
│   ├── models.py         # NewsStory, HistoricalEvent
│   ├── news_fetcher.py   # RSS fetching, relevance scoring
│   └── historical_connector.py  # LLM historical analysis
│
├── script/
│   ├── models.py         # VisualMarker, AnnotatedScript
│   └── generator.py      # LLM script generation
│
├── audio/
│   ├── models.py         # AudioSegment, AudioOutput
│   └── tts_generator.py  # OpenAI TTS generation
│
├── images/
│   ├── models.py         # ImageResult, ImageCollection
│   ├── searcher.py       # Google Images search
│   ├── ai_generator.py   # DALL-E image generation
│   └── manager.py        # Image download/caching
│
├── video/
│   ├── models.py         # VideoSegment, RenderSpec
│   ├── ken_burns.py      # Motion parameter generation
│   └── renderer.py       # FFmpeg video rendering
│
├── publish/
│   └── tiktok.py         # TikTok auto-upload
│
└── utils/
    ├── logging_utils.py  # Rich logging, timing
    └── ffmpeg_utils.py   # FFmpeg helpers
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=ai_ken_burns --cov-report=term-missing
```

### Code Style

```bash
# Format code
black ai_ken_burns/

# Lint
ruff check ai_ken_burns/

# Type check
mypy ai_ken_burns/
```

## Requirements

- **Python**: 3.10 or higher
- **FFmpeg**: Must be installed and in PATH
- **OpenAI API**: GPT-4o access for best results
- **Storage**: ~500MB per video (temporary files cleaned up after)
- **Chrome**: Required for TikTok publishing (Selenium)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- OpenAI for GPT-4, TTS, and DALL-E APIs
- FFmpeg for video processing
- The labor movement and class consciousness educators who inspire this project
