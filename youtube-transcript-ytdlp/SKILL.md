---
name: youtube-transcript-ytdlp
description: Fetch YouTube transcripts locally via yt-dlp (no SupaData, no n8n required). Use as manual alternative or fallback when youtube-transcript-fetcher (SupaData) returns errors. Triggers when user explicitly says "через yt-dlp", "ytdlp", "локально скачай транскрипцию", or when SupaData previously failed and user wants to retry via local tool. Produces identical file format and filename convention as youtube-transcript-fetcher — same .md structure, same fetch-index.json shared index.
---

# YouTube Transcript Fetcher (yt-dlp)

Local fetcher using yt-dlp. Same workflow as `youtube-transcript-fetcher` — same index, same file format — but runs entirely on your machine without SupaData or n8n.

**Requires:** `yt-dlp` installed (`brew install yt-dlp`).
**Script:** `~/.claude/skills/youtube-transcript-ytdlp/scripts/fetch_transcript.py`

---

## Step 1: Check yt-dlp

```bash
yt-dlp --version
```

If not found: `brew install yt-dlp`. Then proceed.

## Step 2: Find Save Directory

Look for existing `youtube/raw/` path in the project (e.g. `AI stuff/youtube/raw/`). Same directory as `youtube-transcript-fetcher` — both skills share it.

## Step 3: Check Index for Duplicates

Read `raw/fetch-index.json` (shared index with youtube-transcript-fetcher).

| Index status | Action |
|---|---|
| `success` | Skip — already fetched |
| `no_captions` | Skip |
| `error` | Retry — yt-dlp may succeed where SupaData failed |
| Not in index | Fetch |

## Step 4: Fetch via Script

Run for each URL (sequentially, one at a time):

```bash
python3 ~/.claude/skills/youtube-transcript-ytdlp/scripts/fetch_transcript.py "URL"
```

Returns JSON:
- `transcript_status`: `success` | `error`
- `filename`: ready-to-use filename (same convention as SupaData)
- `content`: full markdown with frontmatter
- `note`: error description if failed

## Step 5: Save and Update Index

| `transcript_status` | Action |
|---|---|
| `success` | Save `content` to `raw/{filename}` + update index |
| `error` | Update index as `error`, do NOT save file |

Index entry format (identical to youtube-transcript-fetcher):
```json
{
  "VIDEO_ID": {
    "status": "success",
    "filename": "YYYY-MM-DD_ID_channel_title.md",
    "fetched_at": "YYYY-MM-DD",
    "title": "Video Title",
    "channel": "Channel Name"
  }
}
```

## Step 6: Report

```
Готово [yt-dlp]:
✓ Сохранено (N):
  • filename.md

↩ Уже скачано ранее (N):
  • VIDEO_ID — "Title"

✗ Ошибки (N):
  • VIDEO_ID — "Title" — причина
```

## Step 7: Next Steps

Show only if at least one file saved:

1. Готово — файлы сохранены
2. Запустить анализ (video-transcription-analyzer)
3. Получить промпт для анализа в новом чате

---

## Key Differences vs youtube-transcript-fetcher

| | youtube-transcript-fetcher | youtube-transcript-ytdlp |
|---|---|---|
| Source | SupaData API via n8n | yt-dlp locally |
| Cost | SupaData credits | Free |
| Requires | n8n running | yt-dlp installed |
| File format | identical | identical |
| Index | shared fetch-index.json | shared fetch-index.json |
| Frontmatter marker | — | `fetched_via: yt-dlp` |
