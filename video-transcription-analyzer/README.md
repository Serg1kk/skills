# video-transcription-analyzer

> Version: 1.0.0

7-stage pipeline for analyzing video transcriptions: deep content extraction, knowledge base updates, roadmap mapping, and automated verification. Designed for processing YouTube video transcripts into structured, searchable knowledge bases.

## What It Does

Takes `.md` transcription files and runs a full analysis pipeline:

1. **SETUP** — Collects project context (CLAUDE.md, roadmap, EXTRACTION_CONFIG.md), checks KB state, deduplicates by YouTube ID, assigns unique video IDs (V-PA-1, V-RK-2...)
2. **ANALYZE** — Deep extraction by Opus: use-cases, recommendations, opinions, trends, quotes, tools, pain-points, prompts, statistics — all attributed per speaker
3. **MAP** — Cross-references insights against product roadmap, finds gaps, proposes new features with exact module IDs
4. **EXPORT** — Writes `_analysis.json` (unified format), archives raw transcript
5. **KB-UPDATE** — Python script (0 LLM tokens): updates per-category JSON/MD files with file locking, generates `_analysis.md` deterministically from JSON
6. **ROLE-SYNC** — Python script (0 LLM tokens): distributes use-cases into per-role files (developer, product-manager, entrepreneur...)
7. **VERIFY** — Python script (0 LLM tokens): 13+ automated tests checking data integrity, no overwrites, correct counts, parallel safety

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  sonnet-worker       OPUS (main)          Python scripts           │
│  Stage 1: SETUP  →  Stage 2-4:         → Stage 5: kb_update.py    │
│  [model: sonnet]    ANALYZE+MAP+EXPORT    [0 LLM tokens]          │
│                                         → Stage 6: sync_use_cases  │
│  • read configs     • deep extraction     [0 LLM tokens]          │
│  • check KB state   • roadmap mapping   → Stage 7: verify.py      │
│  • dedup check      • write JSON only     [0 LLM tokens]          │
└─────────────────────────────────────────────────────────────────────┘
```

- **Opus** handles intellectually demanding work (analysis, mapping)
- **Sonnet** handles cheap context collection (setup)
- **Python scripts** handle all mechanical work (KB updates, verification) — zero LLM token cost

## Prerequisites

### Required
- **Claude Code** with Opus 4.6 model (recommended) or Sonnet 4.6
- **Python 3.6+** (stdlib only — no pip packages needed)

### Optional
- **EXTRACTION_CONFIG.md** — defines KB categories, roles, paths (without it, runs in one-off mode)
- **Product roadmap** (`docs/roadmap.md`) — enables gap analysis and feature mapping
- **sonnet-worker agent** (`.claude/agents/sonnet-worker.md`) — for cost-optimized SETUP stage

## Installation

### Option 1: Copy to user skills

```bash
cp -r video-transcription-analyzer ~/.claude/skills/
```

### Option 2: Symlink from cloned repo

```bash
git clone https://github.com/Serg1kk/skills.git ~/skills
ln -s ~/skills/video-transcription-analyzer ~/.claude/skills/video-transcription-analyzer
```

### sonnet-worker agent (recommended)

Create `.claude/agents/sonnet-worker.md` in your project with `model: sonnet` in frontmatter. This ensures the SETUP stage runs on Sonnet 4.6 instead of Opus, saving tokens.

## Trigger Phrases

- "analyze transcription", "video analysis", "map to roadmap"
- "extract from video", "knowledge base extraction"
- "analyze YouTube video", "process transcript"
- Providing `.md` transcription files for analysis

## Knowledge Base Output

### Unified JSON Format

Each extracted item follows a consistent schema:

```json
{
  "id": "yt-2026-03-01-video-slug-001",
  "type": "use-cases",
  "source": {
    "platform": "youtube",
    "title": "Video Title",
    "url": "https://youtube.com/watch?v=VIDEO_ID",
    "date": "2026-03-01",
    "channel": "Channel Name",
    "speaker": {
      "name": "Speaker Name",
      "role": "CTO",
      "company": "Acme Corp"
    }
  },
  "content": {
    "summary": "1-2 sentence description",
    "details": "Detailed context",
    "original_quote": "Exact quote if available"
  },
  "tags": ["tag1", "tag2"],
  "roles": ["developer", "product-manager"],
  "sentiment": "positive",
  "extracted_at": "2026-03-01"
}
```

### Supported Categories

`use-cases` | `opinions` | `trends` | `quotes` | `statistics` | `tools` | `pain-points` | `recommendations` | `prompts`

Custom categories can be added via EXTRACTION_CONFIG.md — the pipeline auto-discovers and creates new category files.

### KB Directory Structure

```
knowledge-base/
├── index.json                    # Master index of all processed videos
├── use-cases.json / .md          # Per-category files
├── opinions.json / .md
├── trends.json / .md
├── quotes.json / .md
├── tools.json / .md
├── pain-points.json / .md
├── recommendations.json / .md
├── prompts.json / .md
├── use-cases/                    # Per-role distribution
│   ├── use-cases-developer.json / .md
│   ├── use-cases-product-manager.json / .md
│   └── ...
└── sources/                      # Per-video analysis files
```

## Operating Modes

| Mode | Requires | What it does |
|------|----------|--------------|
| **Full pipeline** | EXTRACTION_CONFIG.md + roadmap | KB extraction + roadmap mapping + gap analysis |
| **KB-only** | EXTRACTION_CONFIG.md | KB extraction without roadmap mapping |
| **One-off** | Nothing | General analysis markdown only, no JSON, no KB updates |

## Parallel Safety

All KB files are shared resources. The pipeline uses `fcntl` file locking on every read-modify-write operation. Multiple agents (YouTube analyzer, Telegram processor, manual scripts) can safely write to the same KB simultaneously.

## Verification (Stage 7)

After every run, 13+ automated tests validate:

| Test | Checks |
|------|--------|
| T1-T5 | Analysis JSON/MD validity, required fields, no duplicate IDs |
| T7-T8 | Category files contain correct items, MDs exist |
| T9-T11 | index.json has correct source entry and totals |
| T12 | Raw transcript archived properly |
| T13 | No overwrites of other sources' data |
| T14 | Role sync: per-role files contain new use-cases |

## Bundled Scripts

| Script | Purpose | LLM Tokens |
|--------|---------|------------|
| `references/kb_update.py` | KB update pipeline: type normalization, category file updates, MD generation, index updates, raw archiving | 0 |
| `references/verify_kb_update.py` | Post-pipeline verification: 13+ data integrity tests | 0 |
| `references/gemini_prompt_template.md` | Template for Google Gemini visual research prompts | N/A |

## File Structure

```
video-transcription-analyzer/
├── SKILL.md                              # Main skill file (full pipeline instructions)
├── README.md                             # This file
└── references/
    ├── kb_update.py                      # KB-UPDATE script (Python 3, stdlib only)
    ├── verify_kb_update.py               # Verification script (Python 3, stdlib only)
    └── gemini_prompt_template.md         # Gemini visual research template
```

## Companion Skills

- **[youtube-transcript-ytdlp](../youtube-transcript-ytdlp/)** — Fetches transcripts locally via yt-dlp (input for this analyzer)
- **telegram-channel-processor** — Processes Telegram exports into the same KB format (shares index and category files)

## License

MIT
