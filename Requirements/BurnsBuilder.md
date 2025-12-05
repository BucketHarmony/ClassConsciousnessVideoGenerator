# Project Spec: Independent AI Video Generator (Audio → Ken-Burns Photo Montage)

## 0. Goal

Build a local-first Python tool that:

Takes an audio file and an optional style prompt (and optionally a folder of images)

Generates a Ken Burns–style video (pans/zooms on still images, synced to the audio timeline)

Uses an LLM (Claude/OpenAI/Ollama) only for planning & storyboard JSON, not for rendering

Uses FFmpeg (or equivalent) to render the final MP4

The result: a CLI tool (and optionally a minimal web UI) that can produce a video with no manual editing.

## 1. High-Level Architecture

### Components:

#### audio_analysis

Analyze audio duration, simple segmentation, and (later) beats / sections.

#### storyboard_generator

Use an LLM to generate a VideoSpec JSON describing segments, images, and motion based on:

- Audio duration
- Transcribed text (optional future)
- Style prompt
- No heavy external dependencies here except LLM API client.

#### image_provider

For each image slot from storyboard:

- If user-supplied image directory: pick from there.
- Else: create a placeholder / call out to an image generator (stub in v1).

#### motion_planner

Convert storyboard-level "motion intent" into concrete pan/zoom keyframes.

#### renderer

Use FFmpeg to:

- Build per-image "Ken Burns" motion video clips.
- Concatenate them.
- Overlay the original audio track.
- Output a final MP4.

#### cli (and optionally web_ui)

Manage config, run the pipeline, show logs, and write outputs.

## 2. Functional Requirements

### 2.1 Inputs

**Required:**

- `--audio PATH` (wav/mp3/etc.)

**Optional:**

- `--style "text style prompt"`
- `--images-dir PATH` (folder of still images, any common format)
- `--output PATH` (default: `./output/output.mp4`)
- `--duration-limit SECONDS` (for debugging shorter drafts)
- `--resolution WIDTHxHEIGHT` (default: `1920x1080`)
- `--fps N` (default: `30`)
- `--ken-burns-intensity FLOAT` 0–1 (amount of pan/zoom)

### 2.2 Outputs

**Final video file:** `output.mp4` (or as specified).

**Intermediate artifacts:**

- `./artifacts/video_spec.json` – the full storyboard/video spec
- `./artifacts/segments/` – optional per-segment info
- `./artifacts/images/` – copied/generated images
- `./artifacts/drafts/` – optional low-res preview video

### 2.3 Core Behavior

#### Audio load & analyze

Read audio file, measure:

- Duration (seconds)
- Optional: basic RMS loudness over time
- For MVP: split timeline into N equal segments (e.g., 6–12 segments, configurable).

#### Storyboard generation via LLM

Build a prompt with:

- Audio duration
- Number of segments
- Style prompt

LLM returns a strict JSON conforming to a given schema (see Section 3).

The storyboard must specify:

- Segments with `start`, `end`, `mood`, `short_description`
- For each segment:
  - `images` list with `duration`, `description`, and a simple `motion_type` (e.g. `zoom_in`, `pan_left`, `static`)

#### Image selection / generation

If user provided `--images-dir`:

- Choose images in sequence (round-robin, or weighted selection).
- Map each storyboard image placeholder to a filename.

If no images provided:

- For MVP: use a static placeholder image or generate simple colored backgrounds with text labels (using PIL).
- Provide a clear hook for future integration with external image models.

#### Motion planning

Convert `motion_type` and `ken-burns-intensity` into:

- `start_frame {x, y, scale}`
- `end_frame {x, y, scale}`
- Values expressed in normalized coordinates (0–1) relative to full frame.

#### Rendering

For each image:

- Generate a short mp4 clip of given duration using FFmpeg with zoom/pan filters (`zoompan` or equivalent).

Concatenate all segment clips to match the full audio duration:

- If video longer than audio: cut to audio length.
- If shorter: insert holds or fades to fill.

Combine with original audio:

- Ensure audio is not re-encoded unnecessarily if avoidable.
- Write final MP4.

#### CLI User Flow

```bash
python -m ai_ken_berns generate --audio song.wav --style "melancholic 70s family photos" --images-dir ./photos
```

Shows progress logs:

- Audio loaded, duration
- Storyboard generated
- - Images mapped
- Rendering %

On success, print:

```
Video written to ./output/output.mp4
```

## 3. Data Models (JSON Schemas)

### 3.1 VideoSpec (top-level)

```json
{
  "audio_file": "path/to/audio.wav",
  "fps": 30,
  "resolution": [1920, 1080],
  "total_duration": 123.45,
  "style_prompt": "melancholic 70s family photos",
  "segments": [
    {
      "id": 1,
      "start": 0.0,
      "end": 10.0,
      "mood": "nostalgic",
      "short_description": "slow opening establishing mood",
      "images": [
        {
          "id": "1-1",
          "description": "sunlit dust in an old living room, warm grain",
          "file": "artifacts/images/seg1_img1.png",
          "start": 0.0,
          "end": 10.0,
          "motion": {
            "type": "ken_burns",
            "pattern": "zoom_in_right",
            "start_frame": { "x": 0.0, "y": 0.0, "scale": 1.0 },
            "end_frame": { "x": 0.4, "y": 0.2, "scale": 1.3 }
          }
        }
      ]
    }
  ]
}
```

### 3.2 LLM Storyboard Response (pre-image-mapping)

The LLM returns JSON missing `file`, `start_frame`, `end_frame`; those will be filled in by code.

```json
{
  "segments": [
    {
      "id": 1,
      "relative_start": 0.0,
      "relative_end": 0.2,
      "mood": "nostalgic",
      "short_description": "slow, warm introduction",
      "images": [
        {
          "description": "old family photo on a wooden table, sunbeam, dust in air",
          "relative_duration": 1.0,
          "motion_type": "slow_zoom_in"
        }
      ]
    }
  ]
}
```

Code then:

- Scales `relative_*` to actual seconds.
- Assigns image files.
- Computes concrete motion frames.

## 4. Non-Functional Requirements

**Local-first:** Should run fully locally except for LLM and (optional) image-generation calls.

**Configurable:**

- YAML/JSON config file for defaults (fps, resolution, Ken Burns intensity).

**Extensible:**

- `image_provider` must be pluggable to support future Stable Diffusion / DALL·E backends.

**Robust JSON handling:**

- Strict validation of LLM output.
- If invalid, retry with a "fix JSON" pass or fail gracefully.

## 5. Tech Stack & Dependencies

**Language:** Python 3.10+

**Dependencies (suggested):**

**Core:**

- `pydantic` or `dataclasses-json` for data models
- `typer` or `click` for CLI
- `python-dotenv` for API keys

**Audio:**

- `librosa` (optional for advanced analysis)
- `soundfile` or `pydub` for duration

**LLM:**

- `openai` / `anthropic` / `ollama` client (abstracted behind an interface)

**Images:**

- `Pillow` for placeholder image creation

**Video:**

- System FFmpeg dependency
- `ffmpeg-python` wrapper OR build command strings directly

## 6. Directory Structure

```
ai_ken_berns/
  __init__.py
  cli.py
  config.py
  models.py           # Pydantic models for VideoSpec, Segment, ImageItem, Motion
  audio_analysis.py
  storyboard_generator.py
  image_provider.py
  motion_planner.py
  renderer.py
  llm_client.py
  utils/
    ffmpeg_utils.py
    json_utils.py
    logging_utils.py

artifacts/
  images/
  drafts/
  video_spec.json

output/
  output.mp4

tests/
  test_models.py
  test_storyboard_generator.py
  test_motion_planner.py
  test_renderer.py

pyproject.toml / requirements.txt
README.md
```

## 7. Development Phases (for Claude)

### Phase 1: Skeleton & Dumb Pipeline

Create project structure and empty modules.

Implement:

- CLI with arguments.
- `audio_analysis.get_audio_duration(path)`.
- Simple segmentation: e.g., 6 equal segments.
- A fake storyboard generator that creates a trivial VideoSpec with:
  - One image per segment.
  - Static motion.
- Placeholder image provider: generate simple colored PNG files.
- Renderer:
  - For each placeholder image, create short static video.
  - Concatenate with FFmpeg.
  - Attach audio.

**Goal:** Audio + solid-color slides video with Ken Burns disabled.

### Phase 2: LLM Storyboard

Implement `llm_client` with an interface + one backend.

Implement real `storyboard_generator`:

- Builds a prompt from duration + style prompt.
- Ensures the LLM returns valid JSON.
- Converts relative durations to actual times.

Validate with tests:

- JSON is valid and parsed into models.
- Total segment durations ≈ audio duration.

**Goal:** Video spec driven by LLM, still using placeholder images.

### Phase 3: Ken Burns Motion

Implement `motion_planner`:

- For each `motion_type`, use `ken_burns_intensity` to compute `start_frame` and `end_frame`.
- Implement typical patterns: `zoom_in`, `zoom_out`, `pan_left`, `pan_right`.

Update renderer to:

- Use FFmpeg `zoompan` filter for each image.
- Ensure duration matches spec.

**Goal:** Proper Ken Burns movement from JSON spec.

### Phase 4: Image Folder Integration

Implement real `image_provider`:

- If `--images-dir` set, assign sequential images to storyboard image slots.
- Fallback to placeholder if images run out.
- Optional: simple heuristics (e.g., random shuffle) for variety.

**Goal:** Video uses real user images.

### Phase 5: Polish

Add:

- Config file support.
- Logging with levels.
- Basic error messages when FFmpeg fails or files missing.

Write README with:

- Setup instructions
- Example commands
- Notes on how to plug in image models later.

## 8. LLM Prompt Template (for Claude)

Claude Code should embed something like this (paraphrased to its style) in `storyboard_generator`:

```
You are a video director AI.
Given: total audio duration (in seconds) and a style prompt, create a JSON storyboard.

Divide the video into between 5 and 12 segments.

Each segment has: id, relative_start, relative_end, mood, short_description.

Each segment contains between 1 and 3 images.

Each image has: description, relative_duration (0–1 fraction of segment), motion_type (slow_zoom_in, slow_zoom_out, pan_left, pan_right, static).

The sum of relative_duration in each segment must be 1.

The last segment must end at 1.0 relative end.
Return ONLY valid JSON matching this structure. No extra text.
```

Claude Code should then write parsing/validation around this.
  video_spec.json

output/
  output.mp4

tests/
  test_models.py
  test_storyboard_generator.py
  test_motion_planner.py
  test_renderer.py

pyproject.toml / requirements.txt
README.md

7. Development Phases (for Claude)
Phase 1: Skeleton & Dumb Pipeline

Create project structure and empty modules.

Implement:

CLI with arguments.

audio_analysis.get_audio_duration(path).

Simple segmentation: e.g., 6 equal segments.

A fake storyboard generator that creates a trivial VideoSpec with:

One image per segment.

Static motion.

Placeholder image provider: generate simple colored PNG files.

Renderer:

For each placeholder image, create short static video.

Concatenate with FFmpeg.

Attach audio.

Goal: Audio + solid-color slides video with Ken Burns disabled.

Phase 2: LLM Storyboard

Implement llm_client with an interface + one backend.

Implement real storyboard_generator:

Builds a prompt from duration + style prompt.

Ensures the LLM returns valid JSON.

Converts relative durations to actual times.

Validate with tests:

JSON is valid and parsed into models.

Total segment durations ≈ audio duration.

Goal: Video spec driven by LLM, still using placeholder images.

Phase 3: Ken Burns Motion

Implement motion_planner:

For each motion_type, use ken_burns_intensity to compute start_frame and end_frame.

Implement typical patterns: zoom_in, zoom_out, pan_left, pan_right.

Update renderer to:

Use FFmpeg zoompan filter for each image.

Ensure duration matches spec.

Goal: Proper Ken Burns movement from JSON spec.

Phase 4: Image Folder Integration

Implement real image_provider:

If --images-dir set, assign sequential images to storyboard image slots.

Fallback to placeholder if images run out.

Optional: simple heuristics (e.g., random shuffle) for variety.

Goal: Video uses real user images.

Phase 5: Polish

Add:

Config file support.

Logging with levels.

Basic error messages when FFmpeg fails or files missing.

Write README with:

Setup instructions

Example commands

Notes on how to plug in image models later.

8. LLM Prompt Template (for Claude)

Claude Code should embed something like this (paraphrased to its style) in storyboard_generator:

You are a video director AI.
Given: total audio duration (in seconds) and a style prompt, create a JSON storyboard.

Divide the video into between 5 and 12 segments.

Each segment has: id, relative_start, relative_end, mood, short_description.

Each segment contains between 1 and 3 images.

Each image has: description, relative_duration (0–1 fraction of segment), motion_type (slow_zoom_in, slow_zoom_out, pan_left, pan_right, static).

The sum of relative_duration in each segment must be 1.

The last segment must end at 1.0 relative end.
Return ONLY valid JSON matching this structure. No extra text.

Claude Code should then write parsing/validation around this.