# MultiverseOne Class Consciousness Video Generator - Implementation Plan

**Version:** 1.0
**Date:** 2025-12-05
**Status:** Ready for Execution
**Project Location:** E:/AI/MultiverseOne

---

## Executive Summary

This plan transforms the MultiverseOne project from a basic Ken Burns video generator into an automated Class Consciousness Video Generator. The system will:

1. **Fetch current news** from Google News RSS (labor, economics, politics topics)
2. **Identify historical parallels** using GPT-4 (class struggle, labor movements, economic conflicts)
3. **Generate compelling scripts** that connect past and present
4. **Create narrated videos** with Ken Burns effects on relevant historical images

**Key Metrics:**
- **MVP Timeline:** 6.5 weeks (parallelized) / 8-9 weeks (single developer)
- **Cost per Video:** $2-5 (OpenAI API costs)
- **Pipeline Runtime:** <8 minutes (target: 5-7 minutes)
- **Success Rate:** 90% (9/10 runs complete without errors)

**Strategic Value:**
- Automates 8-hour manual workflow into 10-minute automated pipeline
- Enables daily content generation (365 videos/year vs. 12-20 manual)
- Vertical integration creates unique capability advantage

---

## Architecture Overview

### System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     BATCH 1: FOUNDATION                          │
│  Config │ Logging │ OpenAI Client │ CLI Enhancement             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────────┐
│                   BATCH 2: RESEARCH PIPELINE                     │
│                                                                   │
│  News Fetcher ──────┐                                           │
│   (RSS Parser)      │                                           │
│                     v                                           │
│               Research Artifact                                 │
│                     ^                                           │
│  Historical    ─────┘                                           │
│  Connector                                                      │
│  (GPT-4 Analysis)                                               │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────────┐
│                BATCH 3: SCRIPT & AUDIO PIPELINE                  │
│                                                                   │
│  Script Generator ──┐                                           │
│  (GPT-4 Narrative)  │                                           │
│                     v                                           │
│               Annotated Script                                  │
│                     │                                           │
│                     ├──> Preview Mode (optional)                │
│                     │                                           │
│                     v                                           │
│  TTS Generator ─────> Audio WAV File                            │
│  (OpenAI TTS)                                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────────┐
│               BATCH 4: VIDEO PIPELINE - PART 1                   │
│                                                                   │
│  Image Searcher ────┐  (Wikimedia + Bing)                       │
│                     v                                           │
│  Image Downloader ──┐  (Download + Resize)                      │
│                     v                                           │
│  Storyboard Gen ────┐  (Match Images to Script)                 │
│                     v                                           │
│               Video Spec (with images)                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────────┐
│               BATCH 5: VIDEO PIPELINE - PART 2                   │
│                                                                   │
│  Motion Planner ────┐  (Ken Burns patterns)                      │
│                     v                                           │
│  FFmpeg Renderer ───┐  (Apply effects, merge audio)             │
│                     v                                           │
│  Error Recovery ────┐  (Checkpointing, retry)                   │
│                     v                                           │
│               Final MP4 Video                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────────┐
│              BATCH 6: INTEGRATION & TESTING                      │
│                                                                   │
│  Pipeline Integration │ Quality Validation │ Documentation       │
└─────────────────────────────────────────────────────────────────┘
```

### Data Models

**Core Models (in ai_ken_burns/models.py):**

1. **NewsStory** (NEW)
   - headline, summary, url, publish_date, source
   - keywords (matched from filter list)

2. **HistoricalConnection** (NEW)
   - event_name, year, location, description
   - key_figures, outcome
   - connection_theme, parallels, contrast
   - relevance_score, confidence

3. **ResearchArtifact** (NEW)
   - news_story, historical_connection
   - created_at, research_id
   - Serialization methods (to_json_file, from_json_file)

4. **AnnotatedScript** (NEW)
   - sections (list of ScriptSection)
   - word_count, estimated_duration
   - tone, style_notes

5. **VideoSpec** (EXISTING - extend)
   - Add research_artifact reference
   - Add script sections metadata
   - Existing: audio_file, segments, images, motion

**Existing Models (already implemented):**
- VideoSpec, Segment, ImageItem, Motion, Keyframe, AudioMetadata

---

## Affected Systems & Components

### Existing Infrastructure (Will Extend)
- **E:/AI/MultiverseOne/ai_ken_burns/config.py** - Add research pipeline config
- **E:/AI/MultiverseOne/ai_ken_burns/models.py** - Add NewsStory, HistoricalConnection, ResearchArtifact, AnnotatedScript
- **E:/AI/MultiverseOne/ai_ken_burns/cli.py** - Add generate-full, research-only, script-only commands
- **E:/AI/MultiverseOne/ai_ken_burns/utils/logging_utils.py** - Extend with pipeline-specific loggers
- **E:/AI/MultiverseOne/ai_ken_burns/storyboard_generator.py** - Integrate with script sections
- **E:/AI/MultiverseOne/ai_ken_burns/motion_planner.py** - Add section-aware motion patterns
- **E:/AI/MultiverseOne/ai_ken_burns/renderer.py** - Integrate audio from TTS

### New Components (Will Create)

**Batch 1 - Foundation:**
- **E:/AI/MultiverseOne/ai_ken_burns/clients/openai_client.py** - Centralized OpenAI API wrapper

**Batch 2 - Research:**
- **E:/AI/MultiverseOne/ai_ken_burns/research/news_fetcher.py** - Google News RSS parser
- **E:/AI/MultiverseOne/ai_ken_burns/research/historical_connector.py** - GPT-4 historical analysis

**Batch 3 - Script/Audio:**
- **E:/AI/MultiverseOne/ai_ken_burns/content/script_generator.py** - GPT-4 narrative scriptwriter
- **E:/AI/MultiverseOne/ai_ken_burns/content/tts_generator.py** - OpenAI TTS integration

**Batch 4 - Images:**
- **E:/AI/MultiverseOne/ai_ken_burns/media/image_searcher.py** - Wikimedia + Bing image search
- **E:/AI/MultiverseOne/ai_ken_burns/media/image_downloader.py** - Download and resize images

**Batch 5 - Integration:**
- **E:/AI/MultiverseOne/ai_ken_burns/utils/checkpoint.py** - Checkpointing and error recovery

**Batch 6 - Testing:**
- **E:/AI/MultiverseOne/ai_ken_burns/pipeline.py** - Full pipeline orchestration
- **E:/AI/MultiverseOne/tests/test_quality.py** - Quality validation suite

**Agent Chat MCP (EXISTING - Available but Optional):**
- **E:/AI/MultiverseOne/agent-chat-mcp/** - NATS-based messaging (defer to Phase 5, not MVP-critical)

---

## Batch Structure & Parallelization Strategy

### Batch 1: Foundation (Week 1)
**Can all run in parallel** - No inter-dependencies

| Phase | Agent | Effort | Parallel Group |
|-------|-------|--------|----------------|
| 1.1 Config Management | @backend-engineer | S | A |
| 1.2 Enhanced Logging | @backend-engineer | S | A |
| 1.3 OpenAI Client | @backend-engineer | S | B (depends on 1.1) |
| 1.4 CLI Enhancement | @backend-engineer | S | A |

**Parallelization:** Run 1.1, 1.2, 1.4 simultaneously. Start 1.3 after 1.1 completes.

---

### Batch 2: Research Pipeline (Week 2)
**Partial parallelization** - News Fetcher and Historical Connector can run in parallel after models defined

| Phase | Agent | Effort | Parallel Group |
|-------|-------|--------|----------------|
| 2.3 Research Data Models | @backend-engineer | S | A (do first) |
| 2.1 News Fetcher | @backend-engineer | S | B (after 2.3) |
| 2.2 Historical Connector | @ai-researcher | M | B (after 2.3) |

**Parallelization:** 2.3 first (defines data contracts), then 2.1 and 2.2 simultaneously.

---

### Batch 3: Script & Audio Pipeline (Week 3)
**Sequential with optional parallel branch**

| Phase | Agent | Effort | Parallel Group |
|-------|-------|--------|----------------|
| 3.1 Script Generator | @ai-content-writer | M | A |
| 3.2 TTS Generator | @backend-engineer | S | B (after 3.1) |
| 3.3 Preview Mode | @backend-engineer | S | B (after 3.1, parallel to 3.2) |

**Parallelization:** 3.1 must complete first. Then 3.2 and 3.3 can run in parallel.

---

### Batch 4: Video Pipeline - Part 1 (Week 4-5)
**Mostly sequential** - Image pipeline flows downward

| Phase | Agent | Effort | Parallel Group |
|-------|-------|--------|----------------|
| 4.1 Image Searcher | @integration-engineer | M | A |
| 4.2 Image Downloader | @backend-engineer | S | B (after 4.1) |
| 4.3 Storyboard Generator | @backend-engineer | M | C (after 4.2) |

**Parallelization:** Minimal. Must flow: 4.1 → 4.2 → 4.3

---

### Batch 5: Video Pipeline - Part 2 (Week 5-6)
**Mostly sequential** - Rendering depends on all prior work

| Phase | Agent | Effort | Parallel Group |
|-------|-------|--------|----------------|
| 5.1 Motion Planner | @backend-engineer | S | A (after Batch 4) |
| 5.2 FFmpeg Renderer | @video-engineer | M | B (after 5.1) |
| 5.3 Error Recovery | @backend-engineer | M | C (wraps all, can start in parallel with 5.2) |

**Parallelization:** 5.1 first, then 5.2 and 5.3 can overlap (error recovery wraps renderer).

---

### Batch 6: Integration & Testing (Week 7)
**Partial parallelization** - Testing can happen alongside documentation

| Phase | Agent | Effort | Parallel Group |
|-------|-------|--------|----------------|
| 6.1 Pipeline Integration | @integration-engineer | M | A |
| 6.2 Quality Validation | @qa-engineer | M | B (after 6.1) |
| 6.3 Documentation | @technical-writer | S | B (parallel to 6.2) |

**Parallelization:** 6.1 first, then 6.2 and 6.3 simultaneously.

---

## Agent Assignment Guide

### Agent Roles & Responsibilities

**@backend-engineer** (Primary workhorse)
- Foundation components (config, logging, clients)
- Data models and serialization
- Image downloader, TTS generator
- Checkpointing and error recovery
- Most Batch 1, 4, 5 work

**@ai-researcher** (GPT-4 prompt engineering specialist)
- Historical connector prompt design
- Testing historical accuracy
- Tuning for quality and relevance
- Phase 2.2

**@ai-content-writer** (Narrative specialist)
- Script generator prompt design
- Narrative structure and tone
- Testing script quality
- Phase 3.1

**@integration-engineer** (API integration specialist)
- Image searcher (Wikimedia + Bing)
- Multi-source API integration
- Pipeline orchestration
- Phases 4.1, 6.1

**@video-engineer** (FFmpeg specialist)
- FFmpeg renderer enhancements
- Audio/video synchronization
- Motion effects implementation
- Phase 5.2

**@qa-engineer** (Testing specialist)
- Quality validation suite
- Manual review and rating
- Test case design
- Phase 6.2

**@technical-writer** (Documentation specialist)
- README updates
- Usage examples
- Troubleshooting guides
- Phase 6.3

---

## Coordination via NATS Channels

### Channel Usage

**#roadmap** - Phase status updates
```
Format: [PHASE X.X] <STATUS> - <MESSAGE>
Example: "[PHASE 2.1] COMPLETE - News fetcher tested on 10 topics"
```

**#coordination** - Parallel work synchronization
```
Format: [PHASE X.X] <AGENT> - <COORDINATION MESSAGE>
Example: "[PHASE 2.1] @backend-engineer - NewsStory model ready, Historical Connector can proceed"
```

**#errors** - Blockers and issues
```
Format: [PHASE X.X] ERROR - <DESCRIPTION> - <IMPACT>
Example: "[PHASE 4.1] ERROR - Wikimedia API rate limit hit - Blocking image search"
```

### Status Update Protocol

When completing a phase:
1. Post to #roadmap: "[PHASE X.X] COMPLETE - <summary>"
2. Update roadmap.md: Change status to 🟢 Complete
3. Trigger Archive Mode: Move phase to completed/roadmap-archive.md
4. Check dependencies: Update blocked phases to ⚪ Not Started if unblocked

When starting a phase:
1. Post to #roadmap: "[PHASE X.X] STARTED - <agent assigned>"
2. Update roadmap.md: Change status to 🟡 In Progress, add agent name

When blocked:
1. Post to #errors: "[PHASE X.X] ERROR - <description>"
2. Post to #coordination: Request help or clarification
3. Update roadmap.md: Change status to 🔴 Blocked, add blocker description

---

## Dependency Matrix

| Phase | Depends On | Blocks | Can Run in Parallel With |
|-------|------------|--------|--------------------------|
| 1.1 Config | None | 1.3, 2.1, 2.2 | 1.2, 1.4 |
| 1.2 Logging | None | None | 1.1, 1.4 |
| 1.3 OpenAI Client | 1.1 | 2.2, 3.1, 3.2 | 1.2, 1.4 (after 1.1) |
| 1.4 CLI | None | None | 1.1, 1.2, 1.3 |
| 2.3 Models | None | 2.1, 2.2 | - |
| 2.1 News Fetcher | 2.3, 1.1, 1.2 | 2.2 | 2.2 (after 2.3) |
| 2.2 Historical | 2.3, 1.3, 2.1 | 3.1 | 2.1 (after 2.3) |
| 3.1 Script Gen | 2.2, 1.3 | 3.2, 3.3, 4.1 | - |
| 3.2 TTS Gen | 3.1, 1.3 | 5.2 | 3.3 |
| 3.3 Preview | 3.1 | None | 3.2 |
| 4.1 Image Search | 3.1, 1.3 | 4.2 | 3.2, 3.3 |
| 4.2 Image Download | 4.1 | 4.3 | - |
| 4.3 Storyboard | 4.2, 3.2 | 5.1 | - |
| 5.1 Motion | 4.3 | 5.2 | 5.3 |
| 5.2 FFmpeg | 5.1, 3.2 | 6.1 | 5.3 |
| 5.3 Error Recovery | All prior | 6.1 | 5.2 |
| 6.1 Integration | All prior | 6.2, 6.3 | - |
| 6.2 Quality | 6.1 | None | 6.3 |
| 6.3 Docs | 6.1 | None | 6.2 |

---

## Configuration Requirements

### Environment Variables (.env)

```bash
# OpenAI API (Required)
OPENAI_API_KEY=sk-...

# Optional - Override defaults
LOG_LEVEL=INFO  # or DEBUG
GOOGLE_NEWS_RSS_URL=https://news.google.com/rss/topics/...

# Optional - LLM Configuration
GPT_MODEL=gpt-4-turbo  # or gpt-4, gpt-4o
TTS_MODEL=tts-1-hd
TTS_VOICE=onyx  # alloy, echo, fable, onyx, nova, shimmer

# Optional - Pipeline Settings
MAX_NEWS_STORIES=10
MIN_RELEVANCE_SCORE=0.5
MIN_CONFIDENCE_SCORE=0.6
```

### Directory Structure

```
E:/AI/MultiverseOne/
├── ai_ken_burns/
│   ├── clients/
│   │   └── openai_client.py (NEW)
│   ├── research/
│   │   ├── news_fetcher.py (NEW)
│   │   └── historical_connector.py (NEW)
│   ├── content/
│   │   ├── script_generator.py (NEW)
│   │   └── tts_generator.py (NEW)
│   ├── media/
│   │   ├── image_searcher.py (NEW)
│   │   └── image_downloader.py (NEW)
│   ├── utils/
│   │   └── checkpoint.py (NEW)
│   ├── config.py (EXTEND)
│   ├── models.py (EXTEND)
│   ├── cli.py (EXTEND)
│   ├── pipeline.py (NEW)
│   └── ... (existing files)
├── artifacts/
│   ├── research/ (NEW - JSON artifacts)
│   ├── scripts/ (NEW - Generated scripts)
│   ├── audio/ (NEW - TTS output)
│   ├── images/ (existing)
│   └── temp/
├── tests/
│   └── test_quality.py (NEW)
├── .claude/
│   └── roadmap/
│       ├── roadmap.md (THIS FILE)
│       ├── plan.md (CURRENT FILE)
│       ├── completed/
│       │   └── roadmap-archive.md
│       └── plans/
│           ├── historical-connector-prompt.md
│           └── script-generator-prompt.md
└── README.md (UPDATE)
```

---

## Quality Gates

### Phase Completion Criteria

Each phase must meet these criteria before marking complete:

**Code Quality:**
- [ ] Code follows existing style (type hints, docstrings)
- [ ] No linter errors (flake8, black)
- [ ] Type checking passes (mypy)
- [ ] Logging added at key points (INFO for major steps, DEBUG for details)

**Functionality:**
- [ ] All tasks in phase checklist completed
- [ ] "Done When" criteria met
- [ ] Error handling implemented (no unhandled exceptions)
- [ ] Edge cases considered (empty inputs, API failures, etc.)

**Testing:**
- [ ] Manual testing on 3+ test cases
- [ ] Success rate ≥ 80% on test cases
- [ ] Performance within targets (time, cost)

**Documentation:**
- [ ] Docstrings for all public functions/classes
- [ ] Inline comments for complex logic
- [ ] Update README if user-facing changes

**Integration:**
- [ ] Works with existing components (no breaking changes)
- [ ] Artifacts saved to correct locations
- [ ] Logging output clear and actionable

---

## Risk Mitigation Strategies

### Top Risks & Mitigations

**1. Historical Accuracy Issues (High Impact)**
- **Risk:** GPT-4 hallucinates or produces generic connections
- **Mitigation:**
  - Detailed prompt with examples and constraints
  - Confidence scoring in response
  - Manual review of low-confidence outputs
  - Test on 10 diverse topics before approving
  - Add disclaimer in videos ("AI-generated historical analysis")

**2. Image Search Quality (Medium Impact)**
- **Risk:** Wikimedia returns irrelevant or insufficient images
- **Mitigation:**
  - Multi-source strategy (Wikimedia primary, Bing fallback)
  - GPT-4 generates contextual search queries
  - Placeholder images for failed searches
  - Manual override capability (specify image directory)

**3. OpenAI API Rate Limits (High Impact)**
- **Risk:** Hit rate limits, block pipeline
- **Mitigation:**
  - Exponential backoff retry in OpenAI client
  - Request throttling (max 5/min)
  - Caching where possible
  - Budget alerts (track spend)

**4. FFmpeg Rendering Failures (Medium Impact)**
- **Risk:** FFmpeg commands fail on edge cases
- **Mitigation:**
  - Comprehensive error logging
  - Test diverse inputs (various image sizes, audio formats)
  - Graceful degradation (skip problematic images)
  - Clear error messages with recovery steps

**5. Script Quality Variability (Medium Impact)**
- **Risk:** Some scripts are boring or formulaic
- **Mitigation:**
  - A/B test prompts on 5+ topics
  - Manual quality rating (target 7/10)
  - Iterate prompt based on feedback
  - Add style randomization

---

## Success Metrics

### MVP Success (End of Batch 6)

**Technical:**
- ✅ Pipeline completes end-to-end (news → video) without crashes
- ✅ 90% success rate (9/10 test runs complete)
- ✅ Total runtime <8 minutes (target: 5-7 min)
- ✅ Cost per video <$5 (OpenAI API)

**Quality:**
- ✅ Historical accuracy ≥80% (manual fact-check on 10 videos)
- ✅ Script quality ≥70% (manual engagement rating)
- ✅ Image relevance ≥70% (manual review)
- ✅ Audio/video sync perfect (±100ms tolerance)

**Usability:**
- ✅ Single CLI command generates full video
- ✅ Preview mode works for fast iteration
- ✅ Documentation complete (README, troubleshooting)
- ✅ Error messages actionable

### Production Ready (Post-MVP)

- ✅ 50 videos generated successfully
- ✅ Average quality rating: 7.5/10
- ✅ Average runtime: <6 minutes
- ✅ Average cost: <$3/video (with optimizations)
- ✅ User satisfaction: 8/10 (if external users)

---

## Next Steps

### Immediate Actions (Next 48 Hours)

1. **Set up NATS channels** (#roadmap, #coordination, #errors)
2. **Create .env file** with OPENAI_API_KEY
3. **Assign agents to Batch 1 phases** (all can start immediately)
4. **Post to #roadmap:** "PROJECT KICKOFF - Batch 1 starting with 4 phases in parallel"

### First Week (Batch 1 Execution)

**Day 1-2:**
- Start Phase 1.1 (Config) and 1.2 (Logging) in parallel
- Start Phase 1.4 (CLI skeleton)

**Day 3-4:**
- Complete 1.1, start 1.3 (OpenAI Client)
- Continue 1.2, 1.4

**Day 5-7:**
- Complete all Batch 1 phases
- Test integration of foundation components
- Post completion to #roadmap
- Begin Batch 2

### Weekly Checkpoint (Every Friday)

Post to #roadmap:
```
WEEKLY STATUS REPORT - Week X

Completed:
- [List completed phases]

In Progress:
- [List current phases with % complete]

Blocked:
- [List blockers with resolution plan]

Next Week Plan:
- [List phases starting next week]

Metrics:
- Total videos generated: X
- Success rate: X%
- Average runtime: X min
- Cumulative cost: $X
```

---

## Questions & Clarifications

**Before starting, confirm:**

1. **OpenAI API access:** Do we have API key with sufficient credits?
2. **FFmpeg installed:** Is FFmpeg available on the development machine?
3. **Agent availability:** Which agents are available for Batch 1?
4. **NATS setup:** Should we use agent-chat-mcp now or defer to later?
5. **Quality bar:** What's acceptable for MVP? (e.g., 70% accuracy vs. 90%)

**Post to #coordination with any questions before starting work.**

---

## Appendix: File Paths Reference

**Roadmap Files:**
- Main roadmap: `E:/AI/MultiverseOne/.claude/roadmap/roadmap.md`
- This plan: `E:/AI/MultiverseOne/.claude/roadmap/plan.md`
- Archive: `E:/AI/MultiverseOne/.claude/roadmap/completed/roadmap-archive.md`
- Prompt designs: `E:/AI/MultiverseOne/.claude/roadmap/plans/`

**Source Code:**
- Project root: `E:/AI/MultiverseOne/`
- Main package: `E:/AI/MultiverseOne/ai_ken_burns/`
- Tests: `E:/AI/MultiverseOne/tests/`
- Artifacts: `E:/AI/MultiverseOne/artifacts/`

**Key Files to Extend:**
- Config: `ai_ken_burns/config.py`
- Models: `ai_ken_burns/models.py`
- CLI: `ai_ken_burns/cli.py`
- Storyboard: `ai_ken_burns/storyboard_generator.py`
- Motion: `ai_ken_burns/motion_planner.py`
- Renderer: `ai_ken_burns/renderer.py`

---

**END OF IMPLEMENTATION PLAN**

*Ready for agent assignment and execution. Post to #roadmap when starting.*
