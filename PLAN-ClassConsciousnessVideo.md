# Class Consciousness Video Generator - Project Plan

## Document Information
- **Project**: MultiverseOne - Class Consciousness Video Generator
- **Version**: 1.0
- **Created**: 2025-12-05
- **Status**: Planning Phase (NO BUILD)

---

## Executive Summary

An automated video production pipeline that:
1. Researches current news for a compelling top story
2. Connects it to a historical event in class struggle/labor history
3. Generates a narrative script promoting class consciousness
4. Produces a professional narrated video with Ken Burns-style visuals

**Primary LLM**: OpenAI (via OPENAI_API_KEY environment variable)

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE ORCHESTRATOR                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    │                               │                               │
    v                               v                               v
┌─────────┐    ┌─────────────────────────────────┐    ┌─────────────────┐
│ PHASE 1 │    │           PHASE 2               │    │     PHASE 3     │
│ RESEARCH│───>│      SCRIPT GENERATION          │───>│  AUDIO + VIDEO  │
└─────────┘    └─────────────────────────────────┘    └─────────────────┘
    │                       │                               │
    v                       v                               v
┌─────────┐    ┌─────────────────────────────────┐    ┌─────────────────┐
│ News    │    │ Historical Connection           │    │ TTS Generation  │
│ Search  │    │ Script Writing                  │    │ Image Search    │
│ API     │    │ Voice Annotation                │    │ Ken Burns Render│
└─────────┘    └─────────────────────────────────┘    └─────────────────┘
```

---

## Phase 1: News Research & Historical Connection

### 1.1 News Search Component

**Objective**: Find today's top news story relevant to workers, economics, or social issues

**Implementation Options**:
| Option | API | Cost | Notes |
|--------|-----|------|-------|
| NewsAPI | newsapi.org | Free tier: 100 req/day | Good for headlines |
| Google News RSS | None | Free | Parse RSS feed |
| Bing News Search | Azure | Pay-per-use | Comprehensive |
| Web Search via OpenAI | Browsing plugin | Included | If available |

**Recommended**: Use web scraping of Google News RSS (free, no API key needed)

**Data Model**:
```python
@dataclass
class NewsStory:
    headline: str
    summary: str
    source: str
    url: str
    published_date: datetime
    category: str  # economics, labor, politics, etc.
```

### 1.2 Historical Connection via LLM

**Objective**: Use OpenAI to find a parallel historical event in class struggle

**Prompt Template**:
```
SYSTEM:
You are a historian specializing in labor history and class struggle.
Your task is to connect current events to historical parallels that
illuminate patterns of class dynamics.

USER:
Today's news story:
{headline}
{summary}

Find a historical event (preferably 50+ years ago) that parallels this
story in terms of class dynamics. Consider:
- Labor strikes and union movements
- Economic crises and their impact on workers
- Corporate/government actions affecting working class
- Revolutionary moments and social movements

Respond with JSON:
{
  "historical_event": "Name of the event",
  "year": "Year or period",
  "location": "Where it happened",
  "summary": "2-3 sentence summary",
  "class_dynamics": "How class struggle manifested",
  "parallel_to_today": "Why this connects to today's story",
  "key_figures": ["List of notable people involved"],
  "outcome": "What happened and lessons learned"
}
```

**Output Data Model**:
```python
@dataclass
class HistoricalConnection:
    event_name: str
    year: str
    location: str
    summary: str
    class_dynamics: str
    parallel_to_today: str
    key_figures: list[str]
    outcome: str
```

---

## Phase 2: Script Generation & Annotation

### 2.1 Narrative Script Generation

**Objective**: Create a compelling 2-4 minute narration script

**Script Structure**:
```
1. HOOK (15-20 seconds)
   - Attention-grabbing opening about today's news

2. TODAY'S STORY (45-60 seconds)
   - Present the current news event
   - Humanize with specific details

3. HISTORICAL BRIDGE (15-20 seconds)
   - Transition: "This echoes a moment in history..."

4. HISTORICAL NARRATIVE (60-90 seconds)
   - Tell the historical story vividly
   - Focus on human elements and struggle

5. CONNECTION & ANALYSIS (30-45 seconds)
   - Draw explicit parallels
   - Highlight patterns of class dynamics

6. CALL TO CONSCIOUSNESS (15-20 seconds)
   - Concluding thought promoting awareness
   - Leave viewer thinking
```

**Prompt Template**:
```
SYSTEM:
You are a documentary scriptwriter creating narration for a video
about class consciousness. Your style is:
- Engaging and accessible (not academic)
- Emotionally resonant but factual
- Uses vivid imagery and specific details
- Builds narrative tension and resolution

USER:
Create a narration script (2-4 minutes when read aloud) connecting:

TODAY'S NEWS:
{news_story}

HISTORICAL EVENT:
{historical_connection}

Requirements:
1. Open with a compelling hook about today's news
2. Tell today's story with human details
3. Bridge naturally to the historical parallel
4. Narrate the historical event vividly
5. Draw explicit connections showing patterns
6. End with a thought-provoking conclusion

Write the script as continuous prose meant to be read aloud.
Mark natural paragraph breaks with [BEAT].
Target: 400-600 words (approximately 3 minutes)
```

### 2.2 Voice Annotation Format

**Objective**: Add TTS control markers for natural-sounding speech

**Annotation Specification**:

| Marker | Meaning | Example |
|--------|---------|---------|
| `[PAUSE:short]` | 0.3 second pause | After a comma |
| `[PAUSE:medium]` | 0.7 second pause | After a sentence |
| `[PAUSE:long]` | 1.2 second pause | Between sections |
| `[PAUSE:dramatic]` | 2.0 second pause | For emphasis |
| `[SLOW]...[/SLOW]` | Reduce speech rate 20% | Important points |
| `[EMPHASIS]...[/EMPHASIS]` | Slight stress | Key words |
| `[SOMBER]...[/SOMBER]` | Lower, serious tone | Heavy topics |
| `[RISING]...[/RISING]` | Building intensity | Building to climax |

**Annotation Prompt**:
```
SYSTEM:
You are a voice director preparing a script for text-to-speech.
Add annotations to make the narration sound natural and engaging.

Available markers:
- [PAUSE:short] - brief pause (0.3s)
- [PAUSE:medium] - sentence pause (0.7s)
- [PAUSE:long] - section pause (1.2s)
- [PAUSE:dramatic] - dramatic pause (2.0s)
- [SLOW]...[/SLOW] - slow down for emphasis
- [EMPHASIS]...[/EMPHASIS] - stress these words
- [SOMBER]...[/SOMBER] - serious/grave tone
- [RISING]...[/RISING] - building intensity

USER:
Annotate this script for text-to-speech:

{raw_script}

Add appropriate markers. Don't change the words, only add markers.
```

**Example Annotated Script**:
```
[PAUSE:medium] Today, [PAUSE:short] as Amazon workers in Alabama
cast their votes, [PAUSE:short] they stand at a crossroads
[EMPHASIS]familiar to generations before them.[/EMPHASIS]

[PAUSE:long]

[SLOW]Ninety years ago, [PAUSE:short] in the textile mills of
Gastonia, North Carolina,[/SLOW] [PAUSE:medium] workers faced
the same choice. [PAUSE:dramatic]

[RISING]They chose to fight.[/RISING]
```

### 2.3 Script Data Model

```python
@dataclass
class AnnotatedScript:
    raw_text: str                    # Original script
    annotated_text: str              # With TTS markers
    estimated_duration_seconds: float # ~150 words/minute
    sections: list[ScriptSection]    # For image timing

@dataclass
class ScriptSection:
    section_type: str   # hook, today, bridge, history, analysis, closing
    text: str
    start_word_index: int
    end_word_index: int
    estimated_duration: float
```

---

## Phase 3: Audio & Video Production

### 3.1 Text-to-Speech Generation

**API**: OpenAI TTS API

**Configuration**:
```python
TTS_CONFIG = {
    "model": "tts-1-hd",      # High quality
    "voice": "onyx",          # Deep, authoritative voice
    "response_format": "wav", # Uncompressed for editing
    "speed": 1.0              # Normal speed (adjust per markers)
}
```

**Marker Processing**:
The annotated script needs preprocessing before TTS:

1. **Strip markers, track timings**:
   - Parse markers and their positions
   - Send clean text to TTS API
   - Insert silence at pause positions post-generation

2. **Alternative: SSML (if supported)**:
   ```xml
   <speak>
     Today, <break time="300ms"/> as Amazon workers vote,
     <break time="700ms"/>
     <prosody rate="slow">they stand at a crossroads</prosody>
   </speak>
   ```

**Audio Pipeline**:
```
Annotated Script
      │
      v
┌─────────────────┐
│ Parse Markers   │──> Timing Map
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Clean Text      │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ OpenAI TTS API  │──> Raw WAV
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Insert Pauses   │──> Final WAV (with silences)
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Audio Analysis  │──> Duration, Segments
└─────────────────┘
```

### 3.2 Image Search & Acquisition

**Objective**: Find relevant images for each script section

**Image Requirements per Section**:
| Section | Image Type | Quantity |
|---------|------------|----------|
| Hook | Current news photo | 1-2 |
| Today's Story | News photos, context | 2-3 |
| Historical Bridge | Transition/symbolic | 1 |
| Historical Narrative | Archival photos | 3-5 |
| Connection | Split/comparison | 1-2 |
| Closing | Symbolic/powerful | 1 |

**Search Strategy**:

1. **For Current News**:
   - Bing Image Search API
   - Filter: News, recent dates
   - Query: Extract key entities from news story

2. **For Historical Images**:
   - Wikimedia Commons API (free, CC licensed)
   - Library of Congress API (public domain)
   - Query: Historical event name + key figures + year

**Image Search Prompt** (for generating queries):
```
SYSTEM:
Generate image search queries for a documentary video.

USER:
Script section: {section_type}
Content: {section_text}
Time period: {modern/historical}

Generate 3 specific image search queries that would find:
- Relevant photographs (not illustrations)
- Emotionally resonant images
- Images that support the narrative

Return as JSON array of query strings.
```

**Image Data Model**:
```python
@dataclass
class ImageAsset:
    url: str
    local_path: str
    source: str           # wikimedia, bing, etc.
    license: str          # CC-BY, public domain, etc.
    caption: str
    section_id: str       # Which script section
    display_duration: float
    motion_pattern: MotionPattern  # zoom_in, pan_left, etc.
```

### 3.3 Ken Burns Video Rendering

**Objective**: Combine audio + images into final video

**Motion Pattern Assignment**:
```python
SECTION_MOTION_PATTERNS = {
    "hook": ["zoom_in"],           # Draw viewer in
    "today": ["pan_left", "pan_right", "zoom_in"],
    "bridge": ["slow_zoom_out"],   # Pull back for perspective
    "history": ["pan_right", "zoom_in", "pan_left"],  # Movement through time
    "analysis": ["slow_zoom_in"],  # Focus
    "closing": ["slow_zoom_out"],  # Final perspective
}
```

**FFmpeg Ken Burns Filter**:
```
zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1920x1080:fps=30
```

**Rendering Pipeline**:
```
Images + Motion Specs + Audio
           │
           v
┌─────────────────────────┐
│ Per-Image Processing    │
│ - Resize to 1920x1080   │
│ - Apply Ken Burns       │
│ - Generate clip         │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ Concatenate Clips       │
│ - Match audio duration  │
│ - Crossfade transitions │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ Merge Audio             │
│ - Sync to video         │
│ - Normalize levels      │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ Final Encode            │
│ - H.264, AAC            │
│ - 1080p @ 30fps         │
└───────────┬─────────────┘
            │
            v
        output.mp4
```

---

## Data Flow Summary

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              INPUT                                        │
│                         (User triggers)                                   │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  v
┌──────────────────────────────────────────────────────────────────────────┐
│  STEP 1: NEWS RESEARCH                                                    │
│  ─────────────────────                                                    │
│  - Fetch top news stories                                                │
│  - Filter for class-relevant topics                                      │
│  - Select most compelling story                                          │
│                                                                          │
│  Output: NewsStory object                                                │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  v
┌──────────────────────────────────────────────────────────────────────────┐
│  STEP 2: HISTORICAL CONNECTION (OpenAI)                                   │
│  ──────────────────────────────────────                                   │
│  - Send news story to GPT-4                                              │
│  - Request historical parallel                                           │
│  - Validate response                                                     │
│                                                                          │
│  Output: HistoricalConnection object                                     │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  v
┌──────────────────────────────────────────────────────────────────────────┐
│  STEP 3: SCRIPT GENERATION (OpenAI)                                       │
│  ──────────────────────────────────                                       │
│  - Generate narrative script                                             │
│  - Structure: hook → today → bridge → history → analysis → close         │
│  - Target: 400-600 words (~3 minutes)                                    │
│                                                                          │
│  Output: Raw script text                                                 │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  v
┌──────────────────────────────────────────────────────────────────────────┐
│  STEP 4: VOICE ANNOTATION (OpenAI)                                        │
│  ─────────────────────────────────                                        │
│  - Add pause markers                                                     │
│  - Add emphasis/inflection markers                                       │
│  - Add pacing markers                                                    │
│                                                                          │
│  Output: AnnotatedScript object                                          │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  v
┌──────────────────────────────────────────────────────────────────────────┐
│  STEP 5: TEXT-TO-SPEECH (OpenAI TTS)                                      │
│  ───────────────────────────────────                                      │
│  - Process annotations → timing map                                      │
│  - Call TTS API with clean text                                          │
│  - Post-process: insert pauses                                           │
│                                                                          │
│  Output: narration.wav                                                   │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  v
┌──────────────────────────────────────────────────────────────────────────┐
│  STEP 6: IMAGE ACQUISITION                                                │
│  ─────────────────────────                                                │
│  - Generate search queries per section                                   │
│  - Search Wikimedia Commons (historical)                                 │
│  - Search Bing/news (current)                                            │
│  - Download and resize images                                            │
│                                                                          │
│  Output: List[ImageAsset]                                                │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  v
┌──────────────────────────────────────────────────────────────────────────┐
│  STEP 7: VIDEO STORYBOARD                                                 │
│  ────────────────────────                                                 │
│  - Match images to script sections                                       │
│  - Calculate display durations                                           │
│  - Assign Ken Burns motion patterns                                      │
│                                                                          │
│  Output: VideoSpec object                                                │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  v
┌──────────────────────────────────────────────────────────────────────────┐
│  STEP 8: VIDEO RENDERING (FFmpeg)                                         │
│  ────────────────────────────────                                         │
│  - Generate Ken Burns clips per image                                    │
│  - Concatenate with transitions                                          │
│  - Merge with audio track                                                │
│  - Encode final video                                                    │
│                                                                          │
│  Output: output.mp4                                                      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
ai_ken_burns/
├── __init__.py
├── cli.py                    # Main entry point
├── config.py                 # OpenAI config, paths
├── models.py                 # All data models
├── pipeline.py               # Orchestrator
│
├── research/
│   ├── __init__.py
│   ├── news_fetcher.py       # News API/RSS integration
│   └── historical_connector.py  # LLM historical research
│
├── script/
│   ├── __init__.py
│   ├── generator.py          # Script generation LLM
│   ├── annotator.py          # Voice annotation LLM
│   └── models.py             # Script-specific models
│
├── audio/
│   ├── __init__.py
│   ├── tts_generator.py      # OpenAI TTS integration
│   ├── audio_processor.py    # Pause insertion, analysis
│   └── models.py
│
├── visual/
│   ├── __init__.py
│   ├── image_searcher.py     # Image search APIs
│   ├── image_downloader.py   # Download & resize
│   └── models.py
│
├── video/
│   ├── __init__.py
│   ├── storyboard.py         # Image-to-section matching
│   ├── motion_planner.py     # Ken Burns patterns
│   ├── renderer.py           # FFmpeg rendering
│   └── models.py
│
├── prompts/
│   ├── historical_connection.txt
│   ├── script_generation.txt
│   └── voice_annotation.txt
│
└── utils/
    ├── __init__.py
    ├── openai_client.py      # Unified OpenAI interface
    ├── ffmpeg_utils.py
    └── logging_utils.py

artifacts/
├── research/
│   ├── news_story.json
│   └── historical_connection.json
├── script/
│   ├── raw_script.txt
│   └── annotated_script.json
├── audio/
│   └── narration.wav
├── images/
│   ├── section_1_img_1.jpg
│   └── ...
└── video/
    ├── video_spec.json
    └── clips/

output/
└── class_consciousness_YYYYMMDD_HHMMSS.mp4
```

---

## Implementation Phases

### Phase 0: Environment Setup
- [ ] Verify OPENAI_API_KEY in environment
- [ ] Install FFmpeg
- [ ] Set up project dependencies
- [ ] Create directory structure

### Phase 1: Research Pipeline
- [ ] Implement news fetcher (RSS/API)
- [ ] Implement historical connector (OpenAI)
- [ ] Create research models
- [ ] Test with sample news stories

### Phase 2: Script Pipeline
- [ ] Implement script generator (OpenAI)
- [ ] Implement voice annotator (OpenAI)
- [ ] Create annotation parser
- [ ] Test full script generation

### Phase 3: Audio Pipeline
- [ ] Implement TTS generator (OpenAI)
- [ ] Implement pause insertion
- [ ] Implement audio analysis
- [ ] Test audio output quality

### Phase 4: Visual Pipeline
- [ ] Implement Wikimedia Commons searcher
- [ ] Implement image downloader
- [ ] Implement image resizing
- [ ] Test image acquisition

### Phase 5: Video Pipeline
- [ ] Implement storyboard generator
- [ ] Implement motion planner
- [ ] Implement FFmpeg renderer
- [ ] Test video output

### Phase 6: Integration
- [ ] Wire all components together
- [ ] Implement CLI interface
- [ ] Error handling & logging
- [ ] End-to-end testing

---

## API Dependencies

| Service | Purpose | Auth |
|---------|---------|------|
| OpenAI GPT-4 | Historical connection, script, annotation | OPENAI_API_KEY |
| OpenAI TTS | Voice generation | OPENAI_API_KEY |
| Wikimedia Commons | Historical images | None (free) |
| Google News RSS | News fetching | None (free) |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| OpenAI rate limits | Implement retry with exponential backoff |
| Poor image search results | Fallback to placeholder images |
| TTS quality issues | Allow voice selection, manual review |
| Historical inaccuracies | Add disclaimer in video |
| Long render times | Show progress, allow preview |

---

## Success Criteria

1. **Functional**: System produces watchable video from single command
2. **Quality**: Audio is clear, images are relevant, timing is synchronized
3. **Content**: Historical connections are accurate and compelling
4. **Performance**: Full pipeline completes in < 10 minutes

---

*This is a PLANNING DOCUMENT. No code implementation until approved.*
