#!/usr/bin/env python3
"""
KB-UPDATE script for video-transcription-analyzer skill.
Handles: dynamic category loading from EXTRACTION_CONFIG.md, type normalization,
file locking for parallel safety, new category auto-creation,
analysis MD generation, index.json updates, raw transcript archiving.

Designed to be called by Opus after ANALYZE+EXPORT stages.
If this script fails (exit 1), Opus falls back to sonnet-worker agent.

Usage:
    python3 kb_update.py \
        --analysis-json PATH \
        --kb-path PATH \
        --source-key KEY \
        --youtube-id ID \
        --video-title TITLE \
        --video-date DATE \
        --channel-name NAME \
        --speaker-name NAME \
        [--extraction-config PATH]  ← reads categories dynamically!
        [--speaker-role ROLE] \
        [--speaker-company COMPANY] \
        [--raw-original PATH] \
        [--raw-archived PATH] \
        [--processing-index PATH] \
        [--author-code CODE] \
        [--video-id V-XX-N]

Exit codes:
    0 = SUCCESS
    1 = FAILURE (details in output, Opus should fall back to sonnet-worker)
"""

import json
import os
import sys
import re
import argparse
import shutil
import fcntl
import time
from collections import defaultdict
from datetime import datetime


def safe_dict(val, default=None):
    """Ensure val is a dict; if it's a string or other type, return default or empty dict."""
    if isinstance(val, dict):
        return val
    return default if default is not None else {}


def safe_get(d, key, default=None):
    """Safe .get() that handles non-dict values (strings, None, etc.)."""
    if isinstance(d, dict):
        return d.get(key, default)
    return default


# ============================================================
# DYNAMIC CONFIG LOADING
# ============================================================

def parse_extraction_config(config_path):
    """Parse EXTRACTION_CONFIG.md and return categories dict.

    Returns:
        {
            'categories': {
                'use-cases': {'display_name': 'Use Cases', 'description': '...'},
                'opinions': {'display_name': 'Мнения/Позиции', 'description': '...'},
                ...
            },
            'kb_path': 'knowledge-base/',  # relative path from config
        }
    """
    if not config_path or not os.path.exists(config_path):
        return None

    with open(config_path) as f:
        content = f.read()

    categories = {}

    # Find the categories table: lines starting with | that have at least 4 columns
    # Format: | ID | Название | Описание | Файл в knowledge-base |
    in_categories_section = False
    for line in content.split('\n'):
        if '## Категории' in line or '## Categories' in line:
            in_categories_section = True
            continue
        if in_categories_section and line.startswith('##'):
            break  # next section
        if not in_categories_section:
            continue

        # Parse table row
        if line.startswith('|') and '---' not in line:
            cols = [c.strip() for c in line.split('|')]
            # cols[0] is empty (before first |), cols[-1] is empty (after last |)
            cols = [c for c in cols if c]
            if len(cols) >= 2 and cols[0].lower() not in ('id', 'category', 'категория'):
                cat_id = cols[0].strip()
                display_name = cols[1].strip() if len(cols) > 1 else cat_id
                description = cols[2].strip() if len(cols) > 2 else ''
                categories[cat_id] = {
                    'display_name': display_name,
                    'description': description,
                }

    # Find kb_path from paths table
    kb_path = 'knowledge-base/'
    for line in content.split('\n'):
        if 'knowledge_base' in line and '|' in line:
            cols = [c.strip() for c in line.split('|')]
            cols = [c for c in cols if c]
            if len(cols) >= 2:
                kb_path = cols[-1].strip()

    return {
        'categories': categories,
        'kb_path': kb_path,
    }


def discover_kb_categories(kb_path):
    """Discover categories from existing KB JSON files.
    Returns dict of {cat_id: {'display_name': cat_id}} for any .json files
    that aren't index.json or processing_index.json.
    """
    categories = {}
    if not os.path.isdir(kb_path):
        return categories
    for f in os.listdir(kb_path):
        if f.endswith('.json') and f not in ('index.json', 'processing_index.json'):
            cat_id = f[:-5]  # strip .json
            categories[cat_id] = {'display_name': cat_id, 'description': ''}
    return categories


# ============================================================
# TYPE NORMALIZATION (dynamic)
# ============================================================

def build_normalize_map(canonical_ids):
    """Auto-generate normalization map from canonical category IDs.

    For each canonical ID like 'use-cases', generates:
    - use-case (singular without s)
    - usecase, usecases (no separator)
    - use_case, use_cases (underscore)
    - use case, use cases (space)
    """
    normalize = {}
    for cat_id in canonical_ids:
        # Already canonical
        normalize[cat_id] = cat_id

        # Singular form (strip trailing 's' if present)
        if cat_id.endswith('s') and not cat_id.endswith('ss'):
            singular = cat_id[:-1]
            normalize[singular] = cat_id

        # Underscore variant
        underscore = cat_id.replace('-', '_')
        normalize[underscore] = cat_id
        if underscore.endswith('s') and not underscore.endswith('ss'):
            normalize[underscore[:-1]] = cat_id

        # Space variant
        spaced = cat_id.replace('-', ' ')
        normalize[spaced] = cat_id
        if spaced.endswith('s') and not spaced.endswith('ss'):
            normalize[spaced[:-1]] = cat_id

        # No separator variant
        nosep = cat_id.replace('-', '')
        normalize[nosep] = cat_id
        if nosep.endswith('s') and not nosep.endswith('ss'):
            normalize[nosep[:-1]] = cat_id

    return normalize


def normalize_type(item_type, normalize_map, canonical_ids):
    """Normalize item type. If unknown, return as-is (new category will be created)."""
    t = item_type.strip().lower()
    if t in canonical_ids:
        return t
    if t in normalize_map:
        return normalize_map[t]
    return t


# ============================================================
# FILE LOCKING
# ============================================================

class FileLock:
    """Context manager for file locking with fcntl. Parallel-agent safe."""

    def __init__(self, filepath, timeout=15):
        self.lock_path = filepath + '.lock'
        self.timeout = timeout
        self.lock_fd = None

    def __enter__(self):
        for attempt in range(self.timeout * 2):
            try:
                self.lock_fd = open(self.lock_path, 'w')
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except (IOError, OSError):
                if self.lock_fd:
                    self.lock_fd.close()
                time.sleep(0.5)
        raise TimeoutError(f"Could not acquire lock: {self.lock_path}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_fd:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            self.lock_fd.close()
            try:
                os.remove(self.lock_path)
            except OSError:
                pass
        return False


# ============================================================
# JSON I/O
# ============================================================

def load_json_items(filepath):
    """Load JSON, handle both flat array and legacy wrapped format."""
    if not os.path.exists(filepath):
        return []
    with open(filepath) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'items' in data:
        return data['items']  # legacy format - auto-migrate on write
    return []


def save_json_items(filepath, items):
    """Save as flat array (canonical format). Always."""
    with open(filepath, 'w') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def load_json_dict(filepath):
    """Load JSON as dict."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath) as f:
        return json.load(f)


def save_json_dict(filepath, data):
    """Save JSON dict."""
    with open(filepath, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# MD GENERATION
# ============================================================

def generate_category_md(cat_id, items, display_names):
    """Generate category markdown from flat array of items."""
    display_name = display_names.get(cat_id, cat_id)
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# {display_name}",
        "",
        f"Последнее обновление: {today}",
        f"Всего айтемов: {len(items)}",
        "",
        "---",
        "",
    ]
    for item in items:
        if not isinstance(item, dict):
            continue
        src = safe_dict(item.get("source"))
        content = safe_dict(item.get("content"))
        speaker = safe_dict(src.get("speaker"))

        # If content was a plain string, use it as summary
        raw_content = item.get("content", "")
        if isinstance(raw_content, str):
            content = {"summary": raw_content, "details": "", "original_quote": None}

        lines.append(f"## {safe_get(src, 'date', 'unknown')} | {safe_get(src, 'title', 'unknown')} | {safe_get(src, 'platform', 'unknown')}")
        lines.append("")
        lines.append(f"### {safe_get(content, 'summary', 'No summary')}")

        sp_name = safe_get(speaker, "name", "unknown")
        sp_role = safe_get(speaker, "role", "")
        lines.append(f"- **Спикер:** {sp_name}{', ' + sp_role if sp_role else ''}")
        lines.append(f"- **Sentiment:** {item.get('sentiment', 'neutral')}")

        roles = item.get("roles", [])
        if isinstance(roles, list) and roles:
            lines.append(f"- **Роли:** {', '.join(str(r) for r in roles)}")

        quote = safe_get(content, "original_quote")
        if quote:
            lines.append(f'- **Цитата:** "{quote}"')

        details = safe_get(content, "details", "")
        if details:
            lines.append(f"- **Детали:** {details}")

        tags = item.get("tags", [])
        if isinstance(tags, list) and tags:
            lines.append(f"- **Теги:** {', '.join(str(t) for t in tags)}")

        url = safe_get(src, "url", "")
        if url:
            lines.append(f"- **Источник:** [{url}]({url})")

        lines.extend(["", "---", ""])

    return "\n".join(lines)


def generate_analysis_md(items, video_meta, display_names):
    """Generate _analysis.md from _analysis.json items."""
    lines = []
    lines.append(f"# Анализ: {video_meta['title']}")
    lines.append("")
    lines.append(f"**Источник:** Транскрипция видео `{video_meta['filename']}`")
    speakers_str = ", ".join(
        f"{s['name']} ({s.get('role', '')}, {s.get('company', '')})"
        for s in video_meta['speakers']
    )
    lines.append(f"**Спикер(ы):** {speakers_str}")
    lines.append(f"**Дата анализа:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**YouTube ID:** {video_meta.get('youtube_id', 'N/A')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Group items by speaker, then by type
    by_speaker = defaultdict(lambda: defaultdict(list))
    for item in items:
        if not isinstance(item, dict):
            continue
        src = safe_dict(item.get("source"))
        spk = safe_dict(src.get("speaker"))
        speaker_name = safe_get(spk, "name", "Unknown")
        item_type = item.get("type", "other")
        by_speaker[speaker_name][item_type].append(item)

    lines.append("## Спикеры")
    lines.append("")

    for speaker_name, types_dict in by_speaker.items():
        first_item = next(iter(next(iter(types_dict.values()))))
        sp = safe_dict(safe_dict(first_item.get("source")).get("speaker"))
        role = safe_get(sp, "role", "")
        company = safe_get(sp, "company", "")
        lines.append(f"### {speaker_name} — {role}, {company}")
        lines.append("")

        # Render all categories found for this speaker
        for cat_id, cat_items in types_dict.items():
            cat_name = display_names.get(cat_id, cat_id)
            lines.append(f"#### {cat_name} ({len(cat_items)})")
            lines.append("")
            for item in cat_items:
                raw_content = item.get("content", {})
                content = safe_dict(raw_content)
                if isinstance(raw_content, str):
                    content = {"summary": raw_content}
                summary = safe_get(content, "summary", "")
                details = safe_get(content, "details", "")
                quote = safe_get(content, "original_quote")
                lines.append(f"- **{summary}**")
                if details:
                    lines.append(f"  {details}")
                if quote:
                    lines.append(f'  > "{quote}"')
                lines.append("")

        lines.append("---")
        lines.append("")

    # Statistics table (if any)
    stats_items = [i for i in items if isinstance(i, dict) and i.get("type") == "statistics"]
    if stats_items:
        lines.append("## Ключевые метрики")
        lines.append("")
        lines.append("| Метрика | Значение/Контекст | Спикер |")
        lines.append("|---|---|---|")
        for item in stats_items:
            c = safe_dict(item.get("content"))
            if isinstance(item.get("content"), str):
                c = {"summary": item["content"], "details": ""}
            sp_src = safe_dict(item.get("source"))
            sp = safe_get(safe_dict(sp_src.get("speaker")), "name", "")
            lines.append(f"| {safe_get(c, 'summary', '')} | {safe_get(c, 'details', '')} | {sp} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Summary
    type_counts = defaultdict(int)
    for item in items:
        type_counts[item.get("type", "other")] += 1

    lines.append("## Сводка")
    lines.append("")
    lines.append(f"Всего извлечено айтемов: {len(items)}")
    lines.append("")
    for cat_id, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        cat_name = display_names.get(cat_id, cat_id)
        lines.append(f"- {cat_name}: {count}")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# MAIN PIPELINE
# ============================================================

def update_kb(args):
    """Main KB-UPDATE pipeline. Returns (success: bool, report: dict)."""
    report = {
        'items_per_category': {},
        'totals_per_category': {},
        'new_categories_created': [],
        'files_updated': [],
        'errors': [],
        'warnings': [],
        'total_kb_items': 0,
    }

    # ── 0. Load categories dynamically ──
    # Priority: EXTRACTION_CONFIG > existing KB files > empty
    config = parse_extraction_config(args.extraction_config) if args.extraction_config else None
    config_categories = config['categories'] if config else {}

    # Also discover categories from existing KB files
    kb_categories = discover_kb_categories(args.kb_path)

    # Merge: config takes priority, KB fills gaps
    all_categories = {**kb_categories, **config_categories}

    # Build canonical IDs set and normalization map
    canonical_ids = set(all_categories.keys())
    normalize_map = build_normalize_map(canonical_ids)

    # Build display names dict
    display_names = {
        cat_id: info.get('display_name', cat_id)
        for cat_id, info in all_categories.items()
    }

    report['warnings'].append(
        f"Categories loaded: {len(canonical_ids)} "
        f"(config: {len(config_categories)}, KB: {len(kb_categories)})"
    )

    # ── 1. Read analysis JSON ──
    try:
        with open(args.analysis_json) as f:
            items = json.load(f)
        if not isinstance(items, list):
            report['errors'].append(f"analysis.json is not a flat array: {type(items)}")
            return False, report
    except Exception as e:
        report['errors'].append(f"Failed to read analysis.json: {e}")
        return False, report

    # ── 2. Normalize types on all items ──
    type_changes = {}
    for item in items:
        original = item.get('type', '')
        normalized = normalize_type(original, normalize_map, canonical_ids)
        if normalized != original:
            type_changes[original] = normalized
            item['type'] = normalized

    if type_changes:
        report['warnings'].append(f"Type normalization applied: {type_changes}")
        # Write back normalized items
        save_json_items(args.analysis_json, items)

    # Detect truly new categories (not in config or KB)
    item_types = set(i['type'] for i in items)
    new_types = item_types - canonical_ids
    if new_types:
        report['warnings'].append(f"New categories discovered from Opus output: {new_types}")
        for nt in new_types:
            canonical_ids.add(nt)
            display_names[nt] = nt  # use ID as display name for new categories
            normalize_map = build_normalize_map(canonical_ids)  # rebuild

    # ── 3. Group items by type ──
    by_type = defaultdict(list)
    for item in items:
        by_type[item['type']].append(item)

    # ── 4. Generate _analysis.md ──
    try:
        analysis_md_path = args.analysis_json.replace('.json', '.md')
        video_meta = {
            'title': args.video_title,
            'filename': os.path.basename(args.analysis_json).replace('_analysis.json', '.md'),
            'youtube_id': args.youtube_id,
            'speakers': [{
                'name': args.speaker_name,
                'role': args.speaker_role or '',
                'company': args.speaker_company or '',
            }],
        }
        md_content = generate_analysis_md(items, video_meta, display_names)
        with open(analysis_md_path, 'w') as f:
            f.write(md_content)
        report['files_updated'].append(os.path.basename(analysis_md_path))
    except Exception as e:
        report['errors'].append(f"Failed to generate analysis.md: {e}")
        return False, report

    # ── 5. Update per-category KB files ──
    for cat_id, cat_items in by_type.items():
        cat_json_path = os.path.join(args.kb_path, f'{cat_id}.json')
        cat_md_path = os.path.join(args.kb_path, f'{cat_id}.md')

        is_new_category = not os.path.exists(cat_json_path)

        try:
            with FileLock(cat_json_path):
                # Read existing (handles flat array, wrapped, or missing file)
                existing = load_json_items(cat_json_path)

                # Dedup by ID (skip non-dict items)
                existing_ids = {i.get('id') for i in existing if isinstance(i, dict)}
                new_items = [i for i in cat_items if isinstance(i, dict) and i.get('id') not in existing_ids]

                if not new_items:
                    report['items_per_category'][cat_id] = 0
                    report['totals_per_category'][cat_id] = len(existing)
                    continue

                # Append and sort by date (newest first)
                existing.extend(new_items)
                existing.sort(
                    key=lambda i: safe_get(safe_dict(i.get('source') if isinstance(i, dict) else {}), 'date', ''),
                    reverse=True,
                )

                # Write JSON (always flat array)
                save_json_items(cat_json_path, existing)
                report['items_per_category'][cat_id] = len(new_items)
                report['totals_per_category'][cat_id] = len(existing)

                if is_new_category:
                    report['new_categories_created'].append(cat_id)

            # Regenerate MD (separate lock to minimize lock hold time)
            with FileLock(cat_md_path):
                all_items = load_json_items(cat_json_path)
                md = generate_category_md(cat_id, all_items, display_names)
                with open(cat_md_path, 'w') as f:
                    f.write(md)

            report['files_updated'].append(f"{cat_id}.json")
            report['files_updated'].append(f"{cat_id}.md")

        except Exception as e:
            report['errors'].append(f"Failed to update {cat_id}: {e}")

    # ── 6. Update index.json ──
    try:
        idx_path = os.path.join(args.kb_path, 'index.json')
        with FileLock(idx_path):
            index = load_json_dict(idx_path)

            if 'sources' not in index:
                index['sources'] = {}
            if 'categories' not in index:
                index['categories'] = {}

            # Build items_by_type
            items_by_type = {}
            for cat_id, cat_items in by_type.items():
                items_by_type[cat_id] = len(cat_items)

            # Add/update source entry
            index['sources'][args.source_key] = {
                'youtube_id': args.youtube_id,
                'title': args.video_title,
                'url': f"https://www.youtube.com/watch?v={args.youtube_id}",
                'channel': args.channel_name,
                'date': args.video_date,
                'speakers': [args.speaker_name],
                'items_count': len(items),
                'items_by_type': items_by_type,
                'analysis_path': os.path.relpath(
                    args.analysis_json.replace('.json', '.md'),
                    args.kb_path,
                ),
                'analysis_json_path': os.path.relpath(args.analysis_json, args.kb_path),
                'processed_at': datetime.now().strftime('%Y-%m-%d'),
            }

            # Update ALL category totals from actual file counts (not just touched ones)
            for cat_file in os.listdir(args.kb_path):
                if cat_file.endswith('.json') and cat_file not in ('index.json', 'processing_index.json'):
                    cat_id = cat_file[:-5]
                    actual = load_json_items(os.path.join(args.kb_path, cat_file))
                    index['categories'][cat_id] = len(actual)

            # Update global totals
            total = sum(
                v if isinstance(v, int) else v.get('total_items', 0)
                for v in index.get('categories', {}).values()
            )
            index['total_items'] = total
            index['total_sources'] = len(index.get('sources', {}))
            index['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            save_json_dict(idx_path, index)
        report['files_updated'].append('index.json')

    except Exception as e:
        report['errors'].append(f"Failed to update index.json: {e}")

    # ── 7. Update processing_index.json (if provided) ──
    if args.processing_index:
        try:
            with FileLock(args.processing_index):
                pidx = load_json_dict(args.processing_index)

                if 'author_codes' not in pidx:
                    pidx['author_codes'] = {}
                if 'videos' not in pidx:
                    pidx['videos'] = {}

                if args.author_code and args.speaker_name:
                    pidx['author_codes'][args.speaker_name] = args.author_code

                if args.video_id:
                    pidx['videos'][args.video_id] = {
                        'title': args.video_title,
                        'speaker': args.speaker_name,
                        'youtube_id': args.youtube_id,
                        'source_file': args.raw_archived or '',
                        'analysis_file': args.analysis_json.replace('.json', '.md'),
                        'analysis_json': args.analysis_json,
                        'status': 'completed',
                        'gaps_found': 0,
                        'kb_items_extracted': len(items),
                        'roadmap_refs_added': 0,
                        'processing_date': datetime.now().strftime('%Y-%m-%d'),
                    }

                save_json_dict(args.processing_index, pidx)
            report['files_updated'].append('processing_index.json')

        except Exception as e:
            report['errors'].append(f"Failed to update processing_index.json: {e}")

    # ── 8. Archive raw transcript ──
    if args.raw_original and args.raw_archived:
        try:
            if os.path.exists(args.raw_original):
                os.makedirs(os.path.dirname(args.raw_archived), exist_ok=True)
                shutil.move(args.raw_original, args.raw_archived)
                report['files_updated'].append(f"Archived: {os.path.basename(args.raw_original)}")
            elif os.path.exists(args.raw_archived):
                report['warnings'].append("Raw already archived")
            else:
                report['errors'].append("Raw transcript not found in either location")
        except Exception as e:
            report['errors'].append(f"Failed to archive raw: {e}")

    success = len(report['errors']) == 0
    return success, report


def main():
    parser = argparse.ArgumentParser(description='KB-UPDATE pipeline for video-transcription-analyzer')
    parser.add_argument('--analysis-json', required=True, help='Path to _analysis.json')
    parser.add_argument('--kb-path', required=True, help='Path to knowledge-base/ directory')
    parser.add_argument('--source-key', required=True, help='Source key for index.json')
    parser.add_argument('--youtube-id', required=True, help='YouTube video ID')
    parser.add_argument('--video-title', required=True, help='Video title')
    parser.add_argument('--video-date', required=True, help='Video date YYYY-MM-DD')
    parser.add_argument('--channel-name', required=True, help='Channel name')
    parser.add_argument('--speaker-name', required=True, help='Speaker name')
    parser.add_argument('--extraction-config', help='Path to EXTRACTION_CONFIG.md (for dynamic categories)')
    parser.add_argument('--speaker-role', default='', help='Speaker role')
    parser.add_argument('--speaker-company', default='', help='Speaker company')
    parser.add_argument('--raw-original', help='Path to raw transcript (to archive)')
    parser.add_argument('--raw-archived', help='Path where raw transcript should be moved')
    parser.add_argument('--processing-index', help='Path to processing_index.json')
    parser.add_argument('--author-code', help='Author code (e.g. ET)')
    parser.add_argument('--video-id', help='Video ID (e.g. V-ET-1)')

    args = parser.parse_args()

    success, report = update_kb(args)

    # Output report
    print("=" * 60)
    print("KB-UPDATE REPORT")
    print("=" * 60)
    print()

    if report['items_per_category']:
        print("Items added per category:")
        for cat, count in sorted(report['items_per_category'].items()):
            total = report['totals_per_category'].get(cat, '?')
            print(f"  {cat}: +{count} (total: {total})")
        total_kb = sum(report['totals_per_category'].values())
        report['total_kb_items'] = total_kb
        print(f"\n  KB total after update: {total_kb} items")
        print()

    if report['new_categories_created']:
        print(f"New categories created: {report['new_categories_created']}")
        print()

    if report['files_updated']:
        print(f"Files updated: {len(report['files_updated'])}")
        for f in report['files_updated']:
            print(f"  {f}")
        print()

    if report['warnings']:
        print("Warnings:")
        for w in report['warnings']:
            print(f"  WARN: {w}")
        print()

    if report['errors']:
        print("ERRORS:")
        for e in report['errors']:
            print(f"  ERROR: {e}")
        print()
        print("RESULT: FAILED")
        sys.exit(1)
    else:
        print("RESULT: SUCCESS")
        sys.exit(0)


if __name__ == '__main__':
    main()
