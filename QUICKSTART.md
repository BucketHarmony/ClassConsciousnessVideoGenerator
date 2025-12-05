# Quick Start Guide

Generate documentary-style Ken Burns videos connecting current news to historical class struggles.

## Installation

```bash
# Clone and install
git clone <repository-url>
cd MultiverseOne
pip install -e .
```

## Requirements

1. **Python 3.10+**
2. **FFmpeg** - Install from https://ffmpeg.org/download.html
3. **OpenAI API Key** - Get from https://platform.openai.com/api-keys

## Setup

Set your OpenAI API key:

```bash
# Windows
set OPENAI_API_KEY=sk-your-key-here

# Linux/Mac
export OPENAI_API_KEY=sk-your-key-here
```

## Verify Installation

```bash
# Check system status
python -m ai_ken_burns info

# Validate all dependencies
python -m ai_ken_burns validate
```

## Generate Your First Video

### Full Pipeline (Recommended)

```bash
python -m ai_ken_burns generate --topic "labor" --duration 60 --output my_video.mp4
```

This runs all stages:
1. **Research** - Fetches news, finds historical connections
2. **Script** - Generates narration with visual markers
3. **Audio** - Creates TTS narration
4. **Images** - Searches historical image archives
5. **Render** - Produces Ken Burns video with audio

### Step-by-Step Generation

Run each stage individually for more control:

```bash
# 1. Research only - find news and historical connections
python -m ai_ken_burns research-only --topic "labor" --output research.json

# 2. Generate script from research
python -m ai_ken_burns script-only --research research.json --output script.json

# 3. Generate audio from script
python -m ai_ken_burns audio-only --script script.json --output narration.mp3

# 4. Search and download images
python -m ai_ken_burns images-only --script script.json --output-dir ./images

# 5. Render final video
python -m ai_ken_burns render-only \
    --audio narration.mp3 \
    --images ./images \
    --script script.json \
    --output final_video.mp4
```

## Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--topic` | News topic to search | `"labor"` |
| `--duration` | Target video length (seconds) | `60` |
| `--style` | Video style | `"documentary"` |
| `--output` | Output file path | `"output.mp4"` |
| `--verbose` | Show detailed progress | `False` |

## Example Topics

```bash
# Labor and unions
python -m ai_ken_burns generate --topic "union strike" --duration 90

# Housing and rent
python -m ai_ken_burns generate --topic "housing crisis" --duration 60

# Economic inequality
python -m ai_ken_burns generate --topic "wealth inequality" --duration 120

# Worker organizing
python -m ai_ken_burns generate --topic "gig workers" --duration 60
```

## Output Structure

After running, you'll find:

```
output/
├── research.json      # News story + historical connection
├── script.json        # Annotated narration script
├── audio/
│   └── narration.mp3  # TTS audio file
├── images/
│   ├── v1_*.jpg       # Images for each visual marker
│   ├── v2_*.jpg
│   └── ...
└── output.mp4         # Final rendered video
```

## Troubleshooting

### "FFmpeg not found"
Install FFmpeg and add it to your PATH:
- Windows: `winget install ffmpeg` or download from ffmpeg.org
- Mac: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### "OpenAI API key not set"
```bash
set OPENAI_API_KEY=sk-your-key-here
```

### "No news stories found"
Try a different topic or check your internet connection.

### Tests
```bash
python -m pytest tests/ -v -p no:vcr
```

## Next Steps

- Read `CLAUDE.md` for detailed architecture
- Read `TESTING.md` for test documentation
- Explore CLI help: `python -m ai_ken_burns --help`
