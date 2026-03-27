# youtube-transcript-ytdlp

> Version: 1.0.0

Fetch YouTube video transcripts locally using **yt-dlp** — no external APIs, no credits, no running services required. Produces markdown files with YAML frontmatter identical to the SupaData-based fetcher, sharing the same index and file format.

## What It Does

1. Takes one or more YouTube URLs
2. Downloads subtitles via `yt-dlp` (prefers Russian, falls back to English)
3. Converts VTT subtitles to clean readable markdown with paragraph flow
4. Saves transcript files with rich metadata frontmatter (title, channel, duration, views, tags, etc.)
5. Maintains a shared `fetch-index.json` to prevent duplicate fetches across sessions

## When to Use

- As a **free alternative** to SupaData API-based transcript fetching
- As a **fallback** when SupaData returns errors
- When you need transcripts **offline** or without running n8n
- Trigger phrases: "через yt-dlp", "ytdlp", "локально скачай транскрипцию"

## Prerequisites

### yt-dlp

```bash
# macOS
brew install yt-dlp

# Linux
pip install yt-dlp

# Windows
winget install yt-dlp
```

### Python 3

The fetch script requires Python 3.6+. No additional pip packages needed — uses only stdlib modules.

## Installation

### Option 1: Copy to user skills

```bash
cp -r youtube-transcript-ytdlp ~/.claude/skills/
```

### Option 2: Symlink from cloned repo

```bash
git clone https://github.com/Serg1kk/skills.git ~/skills
ln -s ~/skills/youtube-transcript-ytdlp ~/.claude/skills/youtube-transcript-ytdlp
```

## Usage

Once installed, Claude Code will automatically use this skill when you:

- Provide YouTube URLs and ask to fetch transcripts "через yt-dlp"
- Say "скачай транскрипцию локально"
- Want to retry a failed SupaData fetch

The skill runs the bundled Python script:

```bash
python3 ~/.claude/skills/youtube-transcript-ytdlp/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"
```

Returns JSON with `transcript_status`, `filename`, `content` (full markdown), and `note` (error info if failed).

## Output Format

Each transcript is saved as a markdown file:

```
YYYY-MM-DD_VIDEO-ID_channel-slug_title-slug.md
```

With YAML frontmatter containing:

| Field | Description |
|-------|-------------|
| `title` | Video title |
| `channel` | Channel name |
| `youtube_id` | Video ID |
| `url` | Full YouTube URL |
| `published_at` | Upload date |
| `duration` | Video length |
| `views`, `likes`, `comments` | Engagement stats |
| `has_captions` | Whether subtitles were found |
| `transcript_status` | `success` or `error` |
| `fetched_via` | Always `yt-dlp` (distinguishes from SupaData) |

## Shared Index

Both `youtube-transcript-fetcher` (SupaData) and this skill share a single `fetch-index.json`. This prevents duplicate downloads regardless of which fetcher was used.

## Comparison with youtube-transcript-fetcher

| | youtube-transcript-fetcher | youtube-transcript-ytdlp |
|---|---|---|
| Source | SupaData API via n8n | yt-dlp locally |
| Cost | SupaData credits | Free |
| Requires | n8n running | yt-dlp installed |
| File format | Identical | Identical |
| Index | Shared | Shared |
| Frontmatter marker | — | `fetched_via: yt-dlp` |

## File Structure

```
youtube-transcript-ytdlp/
├── SKILL.md                          # Skill instructions for Claude Code
├── README.md                         # This file
└── scripts/
    └── fetch_transcript.py           # Main fetching script (Python 3, stdlib only)
```

## License

MIT
