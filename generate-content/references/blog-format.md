# Blog Format - Content Pipeline

Markdown blog post format. Adapt paths and frontmatter fields to your project.

---

## Frontmatter

```yaml
---
title: "SEO title 45-60 characters"
date: YYYY-MM-DD
description: "One actionable sentence - what the reader gets"
tags: [tag1, tag2, tag3]
status: draft
author: Your Name
---
```

Rules:
- **title:** SEO-friendly, **45-60 characters**. Keep room for site suffix if your framework adds one. Google SERP truncates after ~60 characters.
- **description:** one actionable sentence, **110-160 characters**. Shorter than 110 - truncated in OG previews. Longer than 160 - truncated in Google SERP.
- **tags:** 3-7, lowercase, relevant
- **status:** `draft` on creation, `published` after publishing
- **date:** creation date in YYYY-MM-DD format

## Content Structure

```markdown
[HOOK - 1-2 sentences, specific result]

[CONTEXT - what was the task, what was the situation]

## What I Did

[Specific steps with details, tools, numbers]

## Result

[Measurable outcome]

## What I Learned

[Insight, conclusion, lesson]

## Sources

1. [Title](URL)
2. [Title](URL)
```

Rules:
- 600-1200 words
- Practical "take and use" format
- Code blocks where appropriate (prompts, configs, commands)
- Sources section is mandatory - URLs from Researcher (Phase 3)
- h2 headings for structure, h3 for subsections
- No h1 in body (title comes from frontmatter)

## Slug

File: `YYYY-MM-DD-slug.md`
Slug: lowercase, hyphens, English. Example: `2026-02-09-n8n-product-hunt-digest`

## Save Paths

Adapt to your project structure. Recommended convention:
- Draft: `content/posts/in_progress/YYYY-MM-DD_topic/blog.md`
- Published: `content/posts/completed/YYYY-MM-DD_topic/blog.md`
