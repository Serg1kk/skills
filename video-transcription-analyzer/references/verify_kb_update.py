#!/usr/bin/env python3
"""
Post-pipeline verification for video-transcription-analyzer skill.
Runs after KB-UPDATE sub-agent completes. Checks data integrity,
no overwrites, correct file creation, and JSON↔MD consistency.

Usage (from Bash tool in Claude Code):
    python3 verify_kb_update.py <analysis_json_path> <kb_path> <youtube_id> <source_key> [--raw-original <path>] [--raw-archived <path>]

Example:
    python3 /path/to/verify_kb_update.py \
        "youtube/processed/2026-02-27_..._analysis.json" \
        "knowledge-base/" \
        "7XL8pqiDAxY" \
        "youtube_7XL8pqiDAxY_ai-talent-hub" \
        --raw-original "youtube/raw/2026-02-27_....md" \
        --raw-archived "youtube/raw/processed/2026-02-27_....md"

Exit codes:
    0 = ALL PASSED
    1 = FAILURES detected (see output)
"""

import json
import os
import sys
import argparse
from collections import Counter


def load_json(path):
    """Load JSON, handle both flat array and legacy wrapped format."""
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'items' in data:
        return data['items']
    return data


def run_tests(analysis_json_path, kb_path, youtube_id, source_key,
              raw_original=None, raw_archived=None, pre_snapshot=None):
    errors = []
    warnings = []
    passes = []

    # ── T1: Analysis JSON exists and is valid flat array ──
    try:
        analysis_items = load_json(analysis_json_path)
        assert isinstance(analysis_items, list), 'not a list'
        assert len(analysis_items) > 0, 'empty'
        passes.append(f'T1: analysis.json — {len(analysis_items)} items, flat array')
    except Exception as e:
        errors.append(f'T1 FAIL: analysis.json — {e}')
        analysis_items = []

    # ── T2: Analysis MD exists ──
    md_path = analysis_json_path.replace('.json', '.md')
    if os.path.exists(md_path):
        with open(md_path) as f:
            md_content = f.read()
        passes.append(f'T2: analysis.md — {len(md_content.splitlines())} lines')
    else:
        errors.append('T2 FAIL: analysis.md does not exist')
        md_content = ''

    # ── T3: All JSON items represented in MD (first 40 chars of summary) ──
    if analysis_items and md_content:
        missing = [item['id'] for item in analysis_items
                   if item.get('content', {}).get('summary', '')[:40] not in md_content]
        if missing:
            errors.append(f'T3 FAIL: {len(missing)} items missing from MD: {missing[:5]}')
        else:
            passes.append(f'T3: All {len(analysis_items)} items present in analysis.md')

    # ── T4: Required fields on every item ──
    req_top = ['id', 'type', 'source', 'content', 'tags', 'roles', 'sentiment', 'extracted_at']
    req_source = ['platform', 'title', 'url', 'date', 'channel', 'speaker']
    req_content = ['summary', 'details']
    bad = []
    for item in analysis_items:
        m = [f for f in req_top if f not in item]
        m += [f'source.{f}' for f in req_source if f not in item.get('source', {})]
        m += [f'content.{f}' for f in req_content if f not in item.get('content', {})]
        if m:
            bad.append((item.get('id', '?'), m))
    if bad:
        errors.append(f'T4 FAIL: {len(bad)} items missing fields: {bad[:3]}')
    else:
        passes.append(f'T4: All items have required fields')

    # ── T5: No duplicate IDs in analysis ──
    ids = [i['id'] for i in analysis_items]
    dupes = set(id for id in ids if ids.count(id) > 1)
    if dupes:
        errors.append(f'T5 FAIL: Duplicate IDs: {dupes}')
    else:
        passes.append(f'T5: No duplicate IDs ({len(ids)} unique)')

    # ── T6: Type counts from analysis ──
    type_counts = Counter(i['type'] for i in analysis_items)

    # ── T7: KB category JSONs contain this video's items, no duplicates ──
    categories = list(type_counts.keys())
    for cat in categories:
        cat_file = os.path.join(kb_path, f'{cat}.json')
        if not os.path.exists(cat_file):
            errors.append(f'T7 FAIL: {cat}.json missing')
            continue
        cat_items = load_json(cat_file)
        if not isinstance(cat_items, list):
            errors.append(f'T7 FAIL: {cat}.json not a flat array')
            continue

        # Our items present?
        our = [i for i in cat_items if youtube_id in i.get('source', {}).get('url', '')]
        exp = type_counts[cat]
        if len(our) != exp:
            errors.append(f'T7 FAIL: {cat}.json has {len(our)} video items, expected {exp}')

        # No duplicate IDs in category
        cat_ids = [i.get('id') for i in cat_items]
        cat_dupes = set(id for id in cat_ids if cat_ids.count(id) > 1)
        if cat_dupes:
            errors.append(f'T7 FAIL: {cat}.json duplicate IDs: {list(cat_dupes)[:3]}')

    if not any('T7' in e for e in errors):
        passes.append(f'T7: All {len(categories)} category JSONs correct')

    # ── T8: KB category MDs exist ──
    for cat in categories:
        md_file = os.path.join(kb_path, f'{cat}.md')
        if not os.path.exists(md_file):
            errors.append(f'T8 FAIL: {cat}.md missing')
        elif os.path.getsize(md_file) < 100:
            errors.append(f'T8 FAIL: {cat}.md too small')
    if not any('T8' in e for e in errors):
        passes.append(f'T8: All category MDs exist and non-empty')

    # ── T9: index.json — source entry ──
    idx_path = os.path.join(kb_path, 'index.json')
    with open(idx_path) as f:
        index = json.load(f)
    if source_key in index.get('sources', {}):
        src = index['sources'][source_key]
        if src.get('items_count', 0) != len(analysis_items):
            errors.append(f'T9 FAIL: index items_count={src.get("items_count")}, expected {len(analysis_items)}')
        idx_by_type = src.get('items_by_type', {})
        for cat, cnt in type_counts.items():
            if idx_by_type.get(cat, 0) != cnt:
                errors.append(f'T9 FAIL: index {cat}={idx_by_type.get(cat, 0)}, expected {cnt}')
        if not any('T9' in e for e in errors):
            passes.append(f'T9: index.json source entry correct')
    else:
        errors.append(f'T9 FAIL: {source_key} not in index.json')

    # ── T10: index.json category totals match file counts ──
    idx_cats = index.get('categories', {})
    for cat in categories:
        cat_file = os.path.join(kb_path, f'{cat}.json')
        if not os.path.exists(cat_file):
            continue
        actual = len(load_json(cat_file))
        cat_val = idx_cats.get(cat, {})
        declared = cat_val if isinstance(cat_val, int) else cat_val.get('total_items', -1)
        if actual != declared:
            errors.append(f'T10 FAIL: {cat} index={declared}, file={actual}')
    if not any('T10' in e for e in errors):
        passes.append(f'T10: index totals match file counts')

    # ── T11: Source in category sources lists ──
    for cat in categories:
        cat_val = idx_cats.get(cat, {})
        cat_sources = cat_val.get('sources', []) if isinstance(cat_val, dict) else []
        if cat_sources and source_key not in cat_sources:
            errors.append(f'T11 FAIL: {source_key} not in {cat} sources list')
    if not any('T11' in e for e in errors):
        passes.append(f'T11: Source in all category sources lists')

    # ── T12: Raw transcript archived ──
    if raw_original and raw_archived:
        if os.path.exists(raw_original):
            errors.append('T12 FAIL: Raw still in raw/ (not moved)')
        elif os.path.exists(raw_archived):
            passes.append('T12: Raw transcript archived')
        else:
            errors.append('T12 FAIL: Raw not found in either location')

    # ── T13: No overwrites — other sources intact ──
    if pre_snapshot:
        # pre_snapshot is a dict: {source_key: items_count, ...}
        for other_key, other_count in pre_snapshot.items():
            if other_key == source_key:
                continue
            actual = index.get('sources', {}).get(other_key, {}).get('items_count', -1)
            if actual != other_count:
                errors.append(f'T13 FAIL: {other_key} was {other_count}, now {actual} (OVERWRITE)')
    else:
        # Fallback: spot-check that other sources exist and have non-zero counts
        other_sources = {k: v.get('items_count', 0)
                        for k, v in index.get('sources', {}).items()
                        if k != source_key}
        zeroed = [k for k, v in other_sources.items() if v == 0]
        if zeroed:
            errors.append(f'T13 FAIL: Sources with 0 items (possible overwrite): {zeroed}')
        else:
            passes.append(f'T13: No overwrites detected ({len(other_sources)} other sources intact)')

    # ── RESULTS ──
    print('=' * 60)
    print('VERIFICATION RESULTS')
    print('=' * 60)
    print()
    for p in passes:
        print(f'  PASS  {p}')
    print()
    if warnings:
        for w in warnings:
            print(f'  WARN  {w}')
        print()
    if errors:
        for e in errors:
            print(f'  FAIL  {e}')
        print()
        print(f'RESULT: FAILED ({len(errors)} errors, {len(passes)} passed)')
        return False
    else:
        print(f'RESULT: ALL PASSED ({len(passes)} tests)')
        return True


def main():
    parser = argparse.ArgumentParser(description='Verify KB-UPDATE pipeline output')
    parser.add_argument('analysis_json', help='Path to _analysis.json')
    parser.add_argument('kb_path', help='Path to knowledge-base/ directory')
    parser.add_argument('youtube_id', help='YouTube video ID (e.g. 7XL8pqiDAxY)')
    parser.add_argument('source_key', help='Source key in index.json (e.g. youtube_7XL8pqiDAxY_ai-talent-hub)')
    parser.add_argument('--raw-original', help='Path where raw transcript WAS')
    parser.add_argument('--raw-archived', help='Path where raw transcript SHOULD BE now')
    parser.add_argument('--pre-snapshot', help='JSON file with pre-processing source item counts for overwrite detection')

    args = parser.parse_args()

    pre_snapshot = None
    if args.pre_snapshot and os.path.exists(args.pre_snapshot):
        with open(args.pre_snapshot) as f:
            pre_snapshot = json.load(f)

    ok = run_tests(
        analysis_json_path=args.analysis_json,
        kb_path=args.kb_path,
        youtube_id=args.youtube_id,
        source_key=args.source_key,
        raw_original=args.raw_original,
        raw_archived=args.raw_archived,
        pre_snapshot=pre_snapshot,
    )
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
