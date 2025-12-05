# MultiverseOne Roadmap Documentation

**Project:** Class Consciousness Video Generator
**Status:** Ready for Execution
**Last Updated:** 2025-12-05

---

## Quick Start Guide

### For Project Coordinators

1. **Read the strategic analysis:** See `E:/AI/MultiverseOne/ROADMAP.md` for RICE scoring and prioritization
2. **Review the execution plan:** See `roadmap.md` for phase breakdown and agent assignments
3. **Understand the architecture:** See `plan.md` for detailed implementation guide

### For Agents Starting Work

1. **Find your assigned phase:** Check `roadmap.md` for your @agent-name
2. **Read phase details:** See "Tasks" and "Done When" criteria
3. **Check dependencies:** Ensure blocking phases are complete
4. **Review detailed plans:** Check `plans/` directory for prompt designs
5. **Start work and post updates:** Use NATS #roadmap, #coordination, #errors channels

### For Quality Reviewers

1. **Review completion criteria:** See "Done When" for each phase
2. **Run test cases:** See `plan.md` for quality metrics and test scenarios
3. **Validate against metrics:** Historical accuracy ≥80%, script quality ≥70%, etc.

---

## File Structure

```
.claude/roadmap/
├── README.md (THIS FILE)
│   Quick reference and navigation guide
│
├── roadmap.md
│   The active roadmap - tracks all in-progress and pending phases
│   UPDATE THIS as phases progress (status changes, agent assignments)
│   ARCHIVE phases here when complete (then move to archive)
│
├── plan.md
│   Comprehensive implementation plan with architecture, dependencies, coordination
│   READ THIS for understanding system design and agent roles
│
├── completed/
│   └── roadmap-archive.md
│       Archive of completed phases with metadata
│       ADD completed phases here (date, agent, notes)
│
└── plans/
    ├── historical-connector-prompt.md
    │   Detailed GPT-4 prompt design for historical analysis
    │
    └── script-generator-prompt.md
        Detailed GPT-4 prompt design for narrative scriptwriting
```

---

## Workflow

### When Starting a Phase

1. **Check roadmap.md:** Verify phase status is ⚪ Not Started and dependencies are met
2. **Post to #roadmap:** `[PHASE X.X] STARTED - @agent-name assigned`
3. **Update roadmap.md:** Change status to 🟡 In Progress, add agent name
4. **Begin work:** Follow tasks checklist in roadmap.md

### When Completing a Phase

1. **Verify "Done When" criteria met:** Check all acceptance criteria
2. **Post to #roadmap:** `[PHASE X.X] COMPLETE - <brief summary>`
3. **Archive phase:**
   - Copy phase block from roadmap.md to completed/roadmap-archive.md
   - Add completion metadata (date, agent, tasks count, notes)
   - Delete phase from roadmap.md
4. **Check for unblocked phases:** Update dependent phases to ⚪ Not Started if now unblocked

### When Blocked

1. **Post to #errors:** `[PHASE X.X] ERROR - <description> - <impact>`
2. **Post to #coordination:** Request help or clarification
3. **Update roadmap.md:** Change status to 🔴 Blocked, document blocker

### When Coordinating Parallel Work

1. **Post to #coordination:** Share completion of shared dependencies
   - Example: `[PHASE 2.3] @backend-engineer - NewsStory model ready, Phase 2.1 and 2.2 can proceed`
2. **Monitor #coordination:** Watch for updates from parallel work streams

---

## Batch Overview

### Batch 1: Foundation (Week 1)
**Parallel work:** Config, Logging, OpenAI Client, CLI
- All infrastructure needed for downstream work
- Must complete before Batch 2 starts

### Batch 2: Research Pipeline (Week 2)
**Parallel work:** News Fetcher, Historical Connector (after models defined)
- Fetches current news and identifies historical parallels
- Outputs: ResearchArtifact JSON files

### Batch 3: Script & Audio Pipeline (Week 3)
**Parallel work:** TTS Generator and Preview Mode (after script generated)
- Generates compelling narrative scripts
- Converts to narrated audio
- Preview mode for fast iteration

### Batch 4: Video Pipeline - Part 1 (Week 4-5)
**Sequential:** Image Search → Download → Storyboard
- Finds relevant historical images
- Downloads and prepares images
- Assigns images to script sections with timing

### Batch 5: Video Pipeline - Part 2 (Week 5-6)
**Sequential:** Motion → Render (Error Recovery in parallel)
- Plans Ken Burns motion effects
- Renders final video with audio
- Implements checkpointing and retry logic

### Batch 6: Integration & Testing (Week 7)
**Parallel work:** Quality Validation and Documentation (after integration)
- Orchestrates full end-to-end pipeline
- Validates quality metrics
- Documents usage and troubleshooting

---

## Status Icons

- ⚪ **Not Started** - Ready to begin (dependencies met) or waiting on dependencies
- 🟡 **In Progress** - Currently being worked on by assigned agent
- 🟢 **Complete** - Finished and archived (should not appear in roadmap.md, only in archive)
- 🔴 **Blocked** - Cannot proceed due to blocker (dependency not met, issue encountered)

---

## Agent Roles

- **@backend-engineer** - Foundation, data models, core pipeline components
- **@ai-researcher** - Historical connector prompt engineering and validation
- **@ai-content-writer** - Script generator prompt engineering and narrative design
- **@integration-engineer** - Multi-source API integration (images, pipeline orchestration)
- **@video-engineer** - FFmpeg rendering and audio/video synchronization
- **@qa-engineer** - Quality validation and testing
- **@technical-writer** - Documentation and usage guides

---

## NATS Channels

### #roadmap
**Purpose:** Phase status updates and milestone announcements

**Format:**
- `[PHASE X.X] STARTED - @agent-name assigned`
- `[PHASE X.X] COMPLETE - <summary>`
- `BATCH X COMPLETE - All phases finished`
- `WEEKLY STATUS REPORT - Week X`

### #coordination
**Purpose:** Synchronize parallel work, share dependency completion

**Format:**
- `[PHASE X.X] @agent - <coordination message>`
- Example: `[PHASE 2.3] @backend-engineer - Models ready, research phases can start`

### #errors
**Purpose:** Report blockers, issues, and critical errors

**Format:**
- `[PHASE X.X] ERROR - <description> - <impact>`
- `[PHASE X.X] RESOLVED - <resolution summary>`

---

## Key Metrics

### MVP Success Criteria
- ✅ 90% success rate (9/10 runs complete end-to-end)
- ✅ Pipeline runtime <8 minutes
- ✅ Cost per video <$5
- ✅ Historical accuracy ≥80%
- ✅ Script quality ≥70%
- ✅ Image relevance ≥70%

### Timeline Target
- **MVP:** 6.5 weeks (parallelized)
- **Single developer:** 8-9 weeks

---

## Common Tasks Reference

### Update roadmap.md Status
```markdown
### Phase X.X: Component Name
- **Status:** 🟡 In Progress | Agent: @agent-name
```

### Archive Completed Phase
1. Copy entire phase block from roadmap.md
2. Paste into completed/roadmap-archive.md under today's date
3. Add metadata:
```markdown
## 2025-12-05

### Phase X.X: Component Name - COMPLETE
- **Completed by:** @agent-name
- **Tasks:** 6/6 complete
- **Notes:** [Any relevant context]

[Original phase content...]
```
4. Delete phase from roadmap.md

### Post Status Update
```
#roadmap channel:
[PHASE 2.1] COMPLETE - News fetcher tested on 10 topics, 100% success rate
```

---

## Getting Help

1. **Unclear about a phase?** Post to #coordination with specific question
2. **Need architectural guidance?** Review `plan.md` or ask in #coordination
3. **Encountered a blocker?** Post to #errors immediately
4. **Unsure about quality bar?** Check "Done When" criteria or ask in #coordination

---

## Example Workflow (Phase 2.1)

**Starting:**
1. Check `roadmap.md` - Phase 2.1 status is ⚪ Not Started
2. Check dependencies - Phase 1.1 (Config) and 2.3 (Models) are complete
3. Post to #roadmap: `[PHASE 2.1] STARTED - @backend-engineer assigned`
4. Edit `roadmap.md`: Change status to `🟡 In Progress | Agent: @backend-engineer`

**Working:**
5. Review tasks in Phase 2.1
6. Create `ai_ken_burns/research/news_fetcher.py`
7. Implement RSS parsing, keyword filtering, NewsStory creation
8. Test on 10 different news topics
9. Verify all "Done When" criteria met

**Completing:**
10. Post to #roadmap: `[PHASE 2.1] COMPLETE - News fetcher tested on 10 topics, 100% success rate`
11. Copy Phase 2.1 block to `completed/roadmap-archive.md` under `## 2025-12-05`
12. Add: `- **Completed by:** @backend-engineer - **Tasks:** 7/7 complete`
13. Delete Phase 2.1 from `roadmap.md`
14. Check if Phase 2.2 was blocked on 2.1 - if so, update status to ⚪ Not Started

---

## Questions Before Starting?

Post to #coordination with:
- Which phase you're assigned to
- Your specific question
- Any context needed

**Ready to begin? Start with Batch 1 - all phases can run in parallel!**

---

**Good luck and happy coding!**
