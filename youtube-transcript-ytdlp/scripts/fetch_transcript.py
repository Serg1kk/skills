#!/usr/bin/env python3
"""
Fetch YouTube transcript via yt-dlp.
Outputs JSON matching SupaData/n8n webhook format.

Usage: python3 fetch_transcript.py <youtube_url>
"""

import html
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def slugify(text, max_len=60):
    """Matches n8n sanitize() logic exactly."""
    text = (text or '').lower()
    text = re.sub(r'[/\\:*?"<>|#@!&()\[\]{}]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text[:max_len].rstrip('-')


def parse_vtt(vtt_text):
    """Convert VTT subtitle file to clean plain text with proper paragraph flow.
    Matches SupaData/n8n logic: join segments with space unless sentence ends (. ? !),
    then double newline — producing wide readable paragraphs instead of narrow subtitle chunks.
    """
    lines = vtt_text.splitlines()
    segments = []
    prev = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        if re.match(r'^\d{2}:\d{2}:\d{2}', line) or re.match(r'^[\d:.]+ --> ', line):
            continue
        if re.match(r'^\d+$', line):
            continue
        # Strip HTML tags (<c>, </c>, <00:00:00.000>, etc.)
        line = re.sub(r'<[^>]+>', '', line).strip()
        # Decode HTML entities (&gt; → >, &amp; → &, etc.)
        line = html.unescape(line)
        if not line:
            continue
        # Deduplicate adjacent identical segments (auto-captions repeat)
        if line != prev:
            segments.append(line)
            prev = line

    if not segments:
        return ''

    # Join segments: space if previous doesn't end sentence, \n\n if it does
    # Mirrors n8n's VTT to Text node logic exactly
    result = segments[0]
    for i in range(1, len(segments)):
        last_char = result.rstrip()[-1] if result.rstrip() else ''
        if last_char in '.?!':
            result += '\n\n' + segments[i]
        else:
            result += ' ' + segments[i]

    return result


def build_filename(meta):
    published = meta.get('upload_date', '')  # YYYYMMDD
    if len(published) == 8:
        date_str = f"{published[:4]}-{published[4:6]}-{published[6:]}"
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    video_id = meta.get('id', 'unknown')
    channel = slugify(meta.get('channel', meta.get('uploader', 'unknown')), 30)
    title = slugify(meta.get('title', 'untitled'), 60)

    return f"{date_str}_{video_id}_{channel}_{title}.md"


def format_duration(seconds):
    if not seconds:
        return ''
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def build_markdown(meta, transcript_text, url, transcript_status, error_msg=''):
    published = meta.get('upload_date', '')
    if len(published) == 8:
        published_at = f"{published[:4]}-{published[4:6]}-{published[6:]}"
    else:
        published_at = ''

    title = meta.get('title', '')
    channel = meta.get('channel', meta.get('uploader', ''))
    video_id = meta.get('id', '')
    duration = format_duration(meta.get('duration'))
    description = (meta.get('description', '') or '')[:500]
    tags = meta.get('tags', []) or []
    views = meta.get('view_count', 0) or 0
    likes = meta.get('like_count', 0) or 0
    comments = meta.get('comment_count', 0) or 0
    fetched_at = datetime.now().strftime('%Y-%m-%d')

    tags_str = '[' + ', '.join(tags[:10]) + ']' if tags else '[]'

    frontmatter = f"""---
title: "{title}"
channel: "{channel}"
youtube_id: {video_id}
url: {url}
published_at: {published_at}
duration: "{duration}"
description: "{description.replace(chr(10), ' ').replace('"', "'")}"
tags: {tags_str}
views: {views}
likes: {likes}
comments: {comments}
has_captions: {str(bool(transcript_text)).lower()}
fetched_at: {fetched_at}
transcript_status: {transcript_status}
fetched_via: yt-dlp
---"""

    if transcript_status == 'success':
        body = f"\n# {title}\n\n**Канал:** {channel}\n**Опубликовано:** {published_at}\n**URL:** {url}\n\n---\n\n{transcript_text}"
    else:
        body = f"\n# {title}\n\n**Канал:** {channel}\n**Опубликовано:** {published_at}\n**URL:** {url}\n\n---\n\n**Ошибка транскрипции:** {error_msg}"

    return frontmatter + body


def fetch(url):
    # 1. Get metadata
    meta_result = run(['yt-dlp', '--dump-json', '--no-warnings', url])
    if meta_result.returncode != 0:
        return {
            'filename': f"error_{url.split('=')[-1]}.md",
            'content': f"# Error\n\n{meta_result.stderr}",
            'transcript_status': 'error',
            'note': meta_result.stderr[:200]
        }

    try:
        meta = json.loads(meta_result.stdout)
    except json.JSONDecodeError:
        return {
            'filename': 'error_metadata.md',
            'content': '# Error\n\nFailed to parse metadata',
            'transcript_status': 'error',
            'note': 'metadata parse error'
        }

    video_id = meta.get('id', 'unknown')

    # 2. Download subtitles to temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        sub_result = run([
            'yt-dlp',
            '--skip-download',
            '--write-auto-subs',
            '--write-subs',
            '--sub-langs', 'ru,ru-RU,en,en-US',
            '--sub-format', 'vtt',
            '--no-warnings',
            '-o', os.path.join(tmpdir, '%(id)s.%(ext)s'),
            url
        ])

        # Find VTT file
        vtt_files = [f for f in os.listdir(tmpdir) if f.endswith('.vtt')]

        if not vtt_files:
            filename = build_filename(meta)
            content = build_markdown(meta, '', url, 'error', 'yt-dlp: no subtitles found')
            return {
                'filename': filename,
                'content': content,
                'transcript_status': 'error',
                'has_captions': False,
                'note': 'no subtitle files downloaded'
            }

        # Prefer Russian, fallback to first found
        ru_files = [f for f in vtt_files if '.ru' in f or '-ru' in f.lower()]
        vtt_file = ru_files[0] if ru_files else vtt_files[0]

        with open(os.path.join(tmpdir, vtt_file), encoding='utf-8') as f:
            vtt_text = f.read()

    transcript_text = parse_vtt(vtt_text)

    if not transcript_text.strip():
        filename = build_filename(meta)
        content = build_markdown(meta, '', url, 'error', 'yt-dlp: subtitle file was empty')
        return {
            'filename': filename,
            'content': content,
            'transcript_status': 'error',
            'has_captions': True,
            'note': 'empty subtitle content'
        }

    filename = build_filename(meta)
    content = build_markdown(meta, transcript_text, url, 'success')

    return {
        'filename': filename,
        'content': content,
        'transcript_status': 'success',
        'has_captions': True,
        'note': ''
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: fetch_transcript.py <url>'}))
        sys.exit(1)

    url = sys.argv[1]
    result = fetch(url)
    print(json.dumps(result, ensure_ascii=False))
