# generate-content

> Version: 1.0.0

6-phase content generation pipeline for Claude Code. Turns session logs or raw ideas into polished blog posts, Telegram posts, and LinkedIn posts - with built-in AI-marker detection and removal ("deaification").

## What It Does

0. **Setup** (first run) - deep onboarding: asks about your role, domain, expertise, unique perspective, audience, platforms, tone - then suggests content angles tailored to your profile and creates config, directory structure, brand voice guide, and platform style guides
1. **Analyze** - scans Claude Code session logs, extracts themes and topics
2. **Questions** - interactive theme selection, angle, audience targeting
3. **Research** - finds sources and verifies facts via Exa MCP (or WebSearch fallback)
4. **Draft** - writes blog + Telegram + LinkedIn versions following your brand voice
5. **Deaify** - 4 parallel critics detect AI markers (cliches, monotone rhythm, generic phrases, outdated facts), then a rewriter fixes everything
6. **Save** - stores drafts to your content directory, updates session tracker

## Key Features

- **Deep onboarding**: First run interviews you about role, domain, expertise, unique perspective - then suggests 8-12 content angles tailored to your profile. Creates project config, directory structure, brand voice guide, and platform guides automatically
- **Role-aware angles**: Content angles are generated based on YOUR role and domain (developer, designer, founder, marketer, educator, etc.) - not hardcoded
- **Multi-platform output**: Blog (600-1200 words) + Telegram (1000-2000 chars) + LinkedIn (1000-2000 chars)
- **AI marker removal**: 4 specialized critics run in parallel to catch AI-typical patterns
- **Fact checking**: Verifies tool versions, statistics, and claims via web search
- **SEO compliance**: Validates title (45-60 chars) and description (110-160 chars) lengths
- **Brand voice enforcement**: Checks content against your custom brand voice guide
- **Session log analysis**: Automatically discovers new Claude Code sessions to write about
- **Multi-project ready**: Install once at user level, use across different projects - each gets its own config

## Workflow

```
First run in new project
        |
  Phase 0: SETUP - interview user, suggest angles, create config + directories
        |
Session logs / External content
        |
  Phase 1: ANALYZE (opus) - extract themes
        |
  Phase 2: QUESTIONS (interactive) - pick topics, angle, audience
        |
  Phase 3: RESEARCH (sonnet + Exa) - find sources
        |
  Phase 4: DRAFT (opus) - write blog + TG + LI
        |
  Phase 5: DEAIFY
        |-- Critic A (sonnet): Generic detector - cliches, empty phrases
        |-- Critic B (sonnet): Rhythm analyzer - monotone patterns
        |-- Critic C (sonnet): Brand voice - compliance check
        |-- Critic D (sonnet): Fact checker - verify claims
        |
        +-> Rewriter (opus) - apply all fixes
        |
  Phase 6: SAVE - files + tracker update
```

## Installation

```bash
# Copy to your user skills directory
cp -r generate-content ~/.claude/skills/

# Or symlink from cloned repo
ln -s ~/skills/generate-content ~/.claude/skills/generate-content
```

## Prerequisites

- **No manual setup required!** On first run, the skill interviews you and creates everything automatically
- **(Optional) Exa MCP server** - for web research. Falls back to WebSearch if not configured
- **(Optional) Existing brand voice guide** - if you have one, the skill will merge it with its template

### What gets created on first run:

```
.content-pipeline/
  config.json             # Project settings (role, domain, angles, audience, platforms, paths)
  brand-voice.md          # Your brand voice guide (from interview)
  negative-patterns.md    # Prohibited AI patterns
  telegram-style.md       # Telegram formatting (if enabled)
  linkedin-style.md       # LinkedIn formatting (if enabled)
  session-tracker.json    # Session tracking (if enabled)

content/
  ideas/inbox/            # New ideas
  ideas/processed/        # Ideas that became posts
  posts/in_progress/      # Active drafts
  posts/scheduled/        # Ready for publication
  posts/completed/        # Published
```

## Customization

The `references/` folder contains both **pipeline rules** (used as-is) and **templates** (meant to be customized):

### Pipeline rules (use as-is or tweak):
| File | Purpose |
|------|---------|
| `writing-guide.md` | Rules for the Writer subagent |
| `deaify-rules.md` | Rules for 4 critics + rewriter |
| `blog-format.md` | Blog post markdown format |
| `platform-adapters.md` | Blog-to-Telegram and Blog-to-LinkedIn adaptation |
| `negative-patterns.md` | Prohibited words and patterns |

### Templates (customize for your brand):
| File | Purpose |
|------|---------|
| `brand-voice-template.md` | Tone of voice, vocabulary, prohibited phrases |
| `telegram-style-template.md` | Telegram channel post formatting |
| `linkedin-style-template.md` | LinkedIn post formatting |

You don't need to manually customize these - the onboarding process (Phase 0) generates project-specific versions automatically based on your interview answers. Templates are here for reference if you want to edit the generated files later.

## Trigger Phrases

- "generate content from sessions"
- "write a blog post from my CC logs"
- "turn this into a post"
- "process CC Insights into content"
- `/generate-content`

## Arguments

```
/generate-content                          # Scan session logs for new sessions
/generate-content --external "text"        # Use provided text instead of sessions
/generate-content --setup                  # Re-run project setup (update config)
/generate-content path/to/session.jsonl    # Process specific session file
```

## License

MIT
