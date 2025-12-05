# MultiverseOne Class Consciousness Video Generator - Project Roadmap

**Last Updated:** 2025-12-05
**Status:** Ready for Execution

---

## Project Overview

Transform the MultiverseOne project from a basic Ken Burns video generator into a full Class Consciousness Video Generator that automatically connects current news to historical class struggle events. This roadmap breaks work into atomic, parallelizable phases based on RICE prioritization analysis.

**NATS Channels for Coordination:**
- `#roadmap` - Status updates and phase completion
- `#coordination` - Parallel work synchronization
- `#errors` - Issue reporting and blockers

---

## Batch 1: Foundation Layer (No Dependencies)

All components in this batch can be built in parallel. These are infrastructure components that other phases depend on.

### Phase 1.1: Config Management - COMPLETE FOUNDATION
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Extend existing config.py with news/research pipeline settings
  - [ ] Add GOOGLE_NEWS_RSS_URL configuration
  - [ ] Add OpenAI model selection for GPT-4 (research vs generation tasks)
  - [ ] Configure artifact paths for news/scripts/research
  - [ ] Add retry/timeout settings for external APIs
  - [ ] Validate all required API keys on startup
- **Done When:**
  - Config includes all Phase 1-2 settings
  - Environment variable validation catches missing keys
  - All artifact directories auto-created
  - Config accessible via get_config() globally
- **Dependencies:** None
- **Plan:** Extend E:/AI/MultiverseOne/ai_ken_burns/config.py

---

### Phase 1.2: Enhanced Logging System
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Extend logging_utils.py with component-specific loggers
  - [ ] Add structured logging for pipeline stages (research, script, video)
  - [ ] Add timing metrics (log duration of each pipeline stage)
  - [ ] Configure log rotation for production use
  - [ ] Add error context capture (stack traces, API responses)
- **Done When:**
  - Each pipeline component has named logger
  - Timing metrics auto-logged for major operations
  - Error logs include full context for debugging
  - Log files rotate to prevent disk bloat
- **Dependencies:** None
- **Plan:** Extend E:/AI/MultiverseOne/ai_ken_burns/utils/logging_utils.py

---

### Phase 1.3: OpenAI Client Wrapper
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Create centralized OpenAI client in ai_ken_burns/clients/openai_client.py
  - [ ] Implement exponential backoff retry logic (3 attempts, 1s/2s/4s delays)
  - [ ] Add rate limit handling (detect 429, wait and retry)
  - [ ] Implement structured error responses (API errors, network errors, timeouts)
  - [ ] Add request/response logging (DEBUG level with token counts)
  - [ ] Support GPT-4, GPT-4-turbo, and TTS API calls
- **Done When:**
  - Client handles transient failures gracefully
  - Logs include request/response metadata
  - Rate limits auto-handled with backoff
  - All OpenAI calls go through this client
- **Dependencies:** Phase 1.1 (config for API key)
- **Plan:** Create new E:/AI/MultiverseOne/ai_ken_burns/clients/openai_client.py

---

### Phase 1.4: CLI Enhancement - Research Commands
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Add `generate-full` command (end-to-end: news → script → video)
  - [ ] Add `research-only` command (news → historical connection → JSON artifact)
  - [ ] Add `script-only` command (load research artifact → generate script)
  - [ ] Add progress indicators using Rich library progress bars
  - [ ] Add --topic flag to filter news by topic
  - [ ] Add --save-artifacts flag to preserve intermediate JSON files
- **Done When:**
  - CLI supports full pipeline and sub-stages
  - Progress bars show current step and ETA
  - Users can resume from saved artifacts
  - Help text documents all new commands
- **Dependencies:** None (extends existing cli.py)
- **Plan:** Extend E:/AI/MultiverseOne/ai_ken_burns/cli.py

---

## Batch 2: Research Pipeline (Depends on Batch 1)

These components fetch and analyze news content. News Fetcher and Historical Connector can run in parallel after foundation is ready.

### Phase 2.1: News Fetcher (Google News RSS)
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Create ai_ken_burns/research/news_fetcher.py
  - [ ] Implement RSS feed parsing (feedparser library)
  - [ ] Target Google News RSS topics: Business, Economics, Politics
  - [ ] Extract: headline, summary, URL, publish_date, source
  - [ ] Add keyword filtering (configurable: "labor", "union", "strike", "workers", etc.)
  - [ ] Return NewsStory Pydantic model (create in models.py)
  - [ ] Handle feed parsing errors gracefully
- **Done When:**
  - Fetches top 10 news stories from Google News RSS
  - Filters by relevance keywords (min 1 keyword match)
  - Returns structured NewsStory objects
  - Runs in <2 seconds
  - Handles feed unavailability with fallback
- **Dependencies:** Phase 1.1 (config), Phase 1.2 (logging)
- **Plan:** Create E:/AI/MultiverseOne/ai_ken_burns/research/news_fetcher.py

---

### Phase 2.2: Historical Connector (GPT-4 Reasoning)
- **Status:** Not Started
- **Agent:** @ai-researcher
- **Effort:** M
- **Tasks:**
  - [ ] Create ai_ken_burns/research/historical_connector.py
  - [ ] Design GPT-4 prompt for historical analysis (see detailed prompt in plan doc)
  - [ ] Implement JSON schema validation for GPT-4 response
  - [ ] Return HistoricalConnection model (event, year, description, relevance_score)
  - [ ] Add fact-checking validation (check year is reasonable, event is not generic)
  - [ ] Test with 10 diverse news topics (labor, economics, technology, politics)
  - [ ] Tune prompt to avoid hallucinations and generic responses
- **Done When:**
  - GPT-4 returns structured historical connection
  - Connections are specific (not "people have always struggled")
  - Accuracy verified manually on 8/10 test cases
  - Response includes confidence score
  - API call completes in <10 seconds
- **Dependencies:** Phase 1.3 (OpenAI client), Phase 2.1 (NewsStory model)
- **Plan:** Create E:/AI/MultiverseOne/ai_ken_burns/research/historical_connector.py
- **Detailed Prompt:** See E:/AI/MultiverseOne/.claude/roadmap/plans/historical-connector-prompt.md

---

### Phase 2.3: Research Pipeline Data Models
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Add NewsStory model to models.py (headline, summary, url, date, source)
  - [ ] Add HistoricalConnection model (event_name, year, description, relevance, confidence)
  - [ ] Add ResearchArtifact model (news_story, historical_connection, created_at)
  - [ ] Add JSON serialization methods (to_json_file, from_json_file)
  - [ ] Add validation (year bounds 1750-2024, relevance 0-1)
- **Done When:**
  - All models have Pydantic validation
  - Artifacts can be saved/loaded from JSON
  - Models include all metadata for downstream pipeline
- **Dependencies:** Phase 2.1, Phase 2.2 (understanding of data structure)
- **Plan:** Extend E:/AI/MultiverseOne/ai_ken_burns/models.py

---

## Batch 3: Script & Audio Pipeline (Depends on Batch 2)

Generate narrative scripts and convert to audio. Script and TTS can run in parallel after script generation completes.

### Phase 3.1: Script Generator (GPT-4 Narrative)
- **Status:** Not Started
- **Agent:** @ai-content-writer
- **Effort:** M
- **Tasks:**
  - [ ] Create ai_ken_burns/content/script_generator.py
  - [ ] Design 6-section script structure: Hook, News Context, Historical Event, Connection, Modern Relevance, Call to Action
  - [ ] Implement GPT-4 prompt for compelling narrative (400-600 words, 2-4 min read time)
  - [ ] Target emotional tone: urgent, educational, empowering
  - [ ] Add section markers for audio analysis (segment boundaries)
  - [ ] Return AnnotatedScript model (sections, word_count, estimated_duration)
  - [ ] Test narrative quality on 5 diverse topics
- **Done When:**
  - Scripts are coherent and engaging (7/10 manual quality rating)
  - Word count consistently 400-600
  - Section structure preserved
  - Narrative flows naturally from news → history → connection
  - API call completes in <15 seconds
- **Dependencies:** Phase 2.3 (ResearchArtifact model), Phase 1.3 (OpenAI client)
- **Plan:** Create E:/AI/MultiverseOne/ai_ken_burns/content/script_generator.py
- **Detailed Prompt:** See E:/AI/MultiverseOne/.claude/roadmap/plans/script-generator-prompt.md

---

### Phase 3.2: TTS Generator (OpenAI TTS)
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Create ai_ken_burns/content/tts_generator.py
  - [ ] Integrate OpenAI TTS API (tts-1-hd model, onyx voice)
  - [ ] Clean text for TTS (remove markdown, special chars, normalize whitespace)
  - [ ] Save audio as WAV format (44.1kHz, mono)
  - [ ] Extract audio duration from WAV metadata
  - [ ] Add voice selection support (alloy, echo, fable, onyx, nova, shimmer)
  - [ ] Handle API errors (retry on failure, fallback to cached audio if available)
- **Done When:**
  - Converts script text to high-quality audio
  - Audio saved to artifacts/audio/
  - Duration extracted accurately
  - Supports multiple voice options
  - API call completes in <10 seconds
- **Dependencies:** Phase 3.1 (script text), Phase 1.3 (OpenAI client)
- **Plan:** Create E:/AI/MultiverseOne/ai_ken_burns/content/tts_generator.py

---

### Phase 3.3: Preview Mode (Fast Iteration)
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Add --preview flag to CLI (skip TTS and video rendering)
  - [ ] Output: script text with section markers
  - [ ] Output: planned image search queries
  - [ ] Output: storyboard plan (segment timings without images)
  - [ ] Save preview artifacts to artifacts/previews/
  - [ ] Add rich formatting (colored sections, timing markers)
- **Done When:**
  - Preview completes in <30 seconds (vs. full pipeline 5-7 min)
  - Users can review content before committing to full render
  - Preview output is human-readable
- **Dependencies:** Phase 3.1 (script), existing storyboard logic
- **Plan:** Extend E:/AI/MultiverseOne/ai_ken_burns/cli.py

---

## Batch 4: Video Pipeline - Part 1 (Depends on Batch 3)

Image acquisition and storyboard generation. These can run partially in parallel.

### Phase 4.1: Image Searcher (Wikimedia + Fallbacks)
- **Status:** Not Started
- **Agent:** @integration-engineer
- **Effort:** M
- **Tasks:**
  - [ ] Create ai_ken_burns/media/image_searcher.py
  - [ ] Integrate Wikimedia Commons API (primary source)
  - [ ] Generate search queries per script section using GPT-4
  - [ ] Parse API results, filter by CC/public domain license
  - [ ] Implement fallback: Bing Image Search (if Wikimedia fails)
  - [ ] Return ImageAsset model (url, license, description, source)
  - [ ] Handle search failures gracefully (placeholder images)
  - [ ] Limit to 3-5 images per section (configurable)
- **Done When:**
  - Searches return relevant images 70% of the time (manual review)
  - Prioritizes historical images from Wikimedia
  - Falls back to modern images if historical unavailable
  - All images have valid licenses
  - Search completes in <20 seconds for full video
- **Dependencies:** Phase 3.1 (script sections), Phase 1.3 (OpenAI for query generation)
- **Plan:** Create E:/AI/MultiverseOne/ai_ken_burns/media/image_searcher.py

---

### Phase 4.2: Image Downloader (Download + Resize)
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Create ai_ken_burns/media/image_downloader.py
  - [ ] Download images from URLs (requests library with timeout)
  - [ ] Resize to 1920x1080 maintaining aspect ratio (Pillow)
  - [ ] Add letterboxing for non-16:9 images (black bars)
  - [ ] Save to artifacts/images/ with hash-based filenames
  - [ ] Implement retry logic (3 attempts with backoff)
  - [ ] Validate downloaded images (check format, size, corruption)
  - [ ] Generate placeholder images for failed downloads
- **Done When:**
  - All images downloaded and resized correctly
  - Images saved with unique filenames (hash of URL)
  - Failed downloads use placeholder (solid color + text)
  - Download completes in <15 seconds for 20 images
- **Dependencies:** Phase 4.1 (image URLs)
- **Plan:** Create E:/AI/MultiverseOne/ai_ken_burns/media/image_downloader.py

---

### Phase 4.3: Storyboard Generator (Image-to-Section Matching)
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** M
- **Tasks:**
  - [ ] Extend existing storyboard_generator.py for research pipeline
  - [ ] Match downloaded images to script sections
  - [ ] Calculate display duration per image (based on section audio duration)
  - [ ] Distribute images evenly within each section
  - [ ] Add timing validation (no gaps, no overlaps)
  - [ ] Update VideoSpec model with image file paths
  - [ ] Handle edge cases (more images than time, fewer images than sections)
- **Done When:**
  - Every second of audio has assigned image
  - Image timings align with section boundaries
  - Storyboard validates without timing errors
  - Edge cases handled gracefully (duplicate last image if needed)
- **Dependencies:** Phase 4.2 (downloaded images), Phase 3.2 (audio duration)
- **Plan:** Extend E:/AI/MultiverseOne/ai_ken_burns/storyboard_generator.py

---

## Batch 5: Video Pipeline - Part 2 (Depends on Batch 4)

Motion planning and rendering. These must run sequentially.

### Phase 5.1: Motion Planner Enhancement
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Extend motion_planner.py with section-aware patterns
  - [ ] Map section moods to motion patterns (intro=zoom_in, tension=pan, conclusion=zoom_out)
  - [ ] Add randomization (avoid repetitive patterns)
  - [ ] Ensure smooth motion (no jarring jumps)
  - [ ] Validate motion parameters (zoom limits, pan limits)
- **Done When:**
  - Motion patterns match narrative mood
  - Patterns vary across video (not all zoom_in)
  - All motion parameters within safe bounds
  - Visual flow feels professional (manual review)
- **Dependencies:** Phase 4.3 (storyboard with images)
- **Plan:** Extend E:/AI/MultiverseOne/ai_ken_burns/motion_planner.py

---

### Phase 5.2: FFmpeg Renderer (Full Pipeline Integration)
- **Status:** Not Started
- **Agent:** @video-engineer
- **Effort:** M
- **Tasks:**
  - [ ] Extend renderer.py to handle research pipeline output
  - [ ] Integrate audio file from TTS (merge with video track)
  - [ ] Apply Ken Burns effects per image (zoompan filter)
  - [ ] Concatenate image clips (concat demuxer)
  - [ ] Encode final video (H.264, AAC, 1080p30)
  - [ ] Add progress tracking (parse FFmpeg stderr output)
  - [ ] Comprehensive error handling (FFmpeg crashes, encoding errors)
  - [ ] Validate output video (check duration, audio sync, playable)
- **Done When:**
  - Renders complete video without crashes
  - Audio perfectly synchronized (±100ms tolerance)
  - Video plays in VLC, Chrome, mobile devices
  - Render completes in <5 minutes for 3-minute video
  - Errors logged with actionable messages
- **Dependencies:** Phase 5.1 (motion planning), Phase 3.2 (audio file)
- **Plan:** Extend E:/AI/MultiverseOne/ai_ken_burns/renderer.py

---

### Phase 5.3: Error Recovery & Checkpointing
- **Status:** Not Started
- **Agent:** @backend-engineer
- **Effort:** M
- **Tasks:**
  - [ ] Create ai_ken_burns/utils/checkpoint.py
  - [ ] Implement checkpoint system (save state after each major step)
  - [ ] Add --resume flag to CLI (resume from last checkpoint)
  - [ ] Retry logic for API calls (already in OpenAI client)
  - [ ] Graceful degradation (use cached results if available)
  - [ ] Error reporting (log to #errors NATS channel)
  - [ ] Cleanup on failure (remove partial artifacts)
- **Done When:**
  - Pipeline can resume from any major step
  - API failures auto-retry 3 times
  - Transient failures don't require full restart
  - Error messages include recovery instructions
- **Dependencies:** All previous phases (wraps entire pipeline)
- **Plan:** Create E:/AI/MultiverseOne/ai_ken_burns/utils/checkpoint.py

---

## Batch 6: Integration & Testing (Depends on Batch 5)

End-to-end testing and polish. Can parallelize testing different scenarios.

### Phase 6.1: End-to-End Pipeline Integration
- **Status:** Not Started
- **Agent:** @integration-engineer
- **Effort:** M
- **Tasks:**
  - [ ] Create ai_ken_burns/pipeline.py (orchestrates all components)
  - [ ] Wire together: news → historical → script → tts → images → render
  - [ ] Add pipeline-level error handling
  - [ ] Implement progress tracking (emit to #roadmap NATS channel)
  - [ ] Add timing metrics (log duration of each phase)
  - [ ] Create integration tests (end-to-end smoke tests)
  - [ ] Test with 5 diverse news topics (labor, tech, politics, economics, culture)
- **Done When:**
  - Full pipeline runs end-to-end without manual intervention
  - Progress updates posted to NATS #roadmap
  - Pipeline completes in <8 minutes for single video
  - 90% success rate on test topics
  - All artifacts saved to correct locations
- **Dependencies:** All Batch 1-5 phases
- **Plan:** Create E:/AI/MultiverseOne/ai_ken_burns/pipeline.py

---

### Phase 6.2: Quality Validation Suite
- **Status:** Not Started
- **Agent:** @qa-engineer
- **Effort:** M
- **Tasks:**
  - [ ] Create tests/test_quality.py
  - [ ] Test historical accuracy (manual fact-check on 10 outputs)
  - [ ] Test script quality (readability, coherence, engagement)
  - [ ] Test image relevance (manual review of image-section matches)
  - [ ] Test audio quality (TTS clarity, no distortion)
  - [ ] Test video quality (sync, motion smoothness, playability)
  - [ ] Document quality metrics (accuracy %, engagement score, relevance %)
- **Done When:**
  - Historical accuracy >80% (fact-checked)
  - Script quality >70% (manual rating)
  - Image relevance >70% (manual rating)
  - Audio quality >80% (clarity rating)
  - All test videos play correctly
- **Dependencies:** Phase 6.1 (integration)
- **Plan:** Create E:/AI/MultiverseOne/tests/test_quality.py

---

### Phase 6.3: Documentation & Examples
- **Status:** Not Started
- **Agent:** @technical-writer
- **Effort:** S
- **Tasks:**
  - [ ] Update README.md with Class Consciousness features
  - [ ] Add usage examples (CLI commands with real outputs)
  - [ ] Document configuration options (.env template)
  - [ ] Create troubleshooting guide (common errors and fixes)
  - [ ] Add architecture diagram (data flow through pipeline)
  - [ ] Document API cost estimates ($2-5 per video)
  - [ ] Add example videos (upload 3 sample outputs)
- **Done When:**
  - README has clear setup instructions
  - Users can run first video in <10 minutes
  - Troubleshooting covers 80% of likely errors
  - Examples demonstrate all major features
- **Dependencies:** Phase 6.1 (working pipeline)
- **Plan:** Update E:/AI/MultiverseOne/README.md

---

## Batch 7: Polish & Optimization (Optional - Defer to Phase 4 from ROADMAP)

Nice-to-have features that improve quality but aren't MVP-critical.

### Phase 7.1: Crossfade Transitions
- **Status:** Blocked
- **Depends On:** Phase 5.2 (FFmpeg renderer)
- **Agent:** @video-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Add crossfade filter to FFmpeg command (0.5s fade)
  - [ ] Update VideoSpec to include transition_duration
  - [ ] Test crossfade doesn't cause timing issues
- **Done When:**
  - Images transition smoothly (no hard cuts)
  - Total duration unchanged
  - Visual flow improved (manual review)

---

### Phase 7.2: Image Caching
- **Status:** Blocked
- **Depends On:** Phase 4.2 (image downloader)
- **Agent:** @backend-engineer
- **Effort:** S
- **Tasks:**
  - [ ] Implement hash-based cache (URL → file path)
  - [ ] Check cache before downloading
  - [ ] Add cache expiration (7 days)
  - [ ] Add --clear-cache CLI flag
- **Done When:**
  - Re-runs skip image downloads (use cached)
  - Cache limited to 1GB disk usage
  - Stale images auto-purged

---

### Phase 7.3: Voice Annotator (Experimental)
- **Status:** Blocked
- **Depends On:** Phase 3.1 (script generator)
- **Agent:** @ai-content-writer
- **Effort:** S
- **Tasks:**
  - [ ] Add pause markers (... → 1s pause)
  - [ ] Add emphasis markers (**word** → emphasize)
  - [ ] Test if OpenAI TTS respects markers (may not work)
  - [ ] If successful, integrate into script generation
- **Done When:**
  - Markers added to script
  - TTS output tested (confirm effect)
  - If no effect, document and defer

---

## Backlog (Future Work)

- [ ] Agent Chat NATS integration (microservices architecture)
- [ ] Audio post-processing (normalization, EQ, background music)
- [ ] Web UI for video generation
- [ ] Multi-video batch processing
- [ ] Custom fine-tuned model for historical connections
- [ ] Fact-checking layer (validate historical claims)
- [ ] Social media export (optimized for YouTube, TikTok, Twitter)
- [ ] Analytics dashboard (track video quality over time)

---

## Success Metrics

### MVP Success (End of Batch 6)
- ✅ Generate complete video from news → history → script → video
- ✅ Pipeline completes in <8 minutes
- ✅ 90% success rate (9/10 runs complete without errors)
- ✅ Historical accuracy >80% (manual review)
- ✅ Video quality: audio synced, smooth motion, 1080p30
- ✅ Cost per video <$5 (API costs)

### Production Ready (End of Batch 6)
- ✅ 10 test videos generated successfully
- ✅ Documentation complete (README, troubleshooting)
- ✅ Error recovery handles transient failures
- ✅ Quality validated (accuracy, relevance, engagement)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Poor historical accuracy | Medium | High | Prompt refinement, fact-check layer, human review |
| Image search returns irrelevant results | High | Medium | Multiple sources, fallback to placeholders, manual override |
| OpenAI API rate limits | Medium | High | Request throttling, caching, budget alerts |
| FFmpeg rendering failures | Medium | High | Comprehensive error logging, test diverse inputs, graceful degradation |
| Script quality too formulaic | Medium | Medium | A/B test prompts, narrative variation, style randomization |

---

## Timeline Estimate

**Batch-by-Batch (Parallelized):**
- Batch 1 (Foundation): 1 week (4 phases in parallel)
- Batch 2 (Research): 1 week (3 phases, 2 in parallel)
- Batch 3 (Script/Audio): 1 week (3 phases, some parallelization)
- Batch 4 (Video Part 1): 1 week (3 phases, some parallelization)
- Batch 5 (Video Part 2): 1.5 weeks (3 phases, mostly sequential)
- Batch 6 (Integration): 1 week (3 phases, testing/docs)

**Total MVP Timeline: 6.5 weeks** (with parallel work and multiple agents)

**Single Developer Timeline: 8-9 weeks** (matches ROADMAP.md estimate)

---

## Next Steps

1. **Approve this roadmap** (or request changes)
2. **Set up NATS channels** (#roadmap, #coordination, #errors)
3. **Assign agents to Batch 1 phases** (can all start in parallel)
4. **Begin execution** starting with Phase 1.1-1.4

**Questions?** Post to #coordination NATS channel.
