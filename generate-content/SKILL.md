---
name: generate-content
description: Use when generating blog posts, Telegram posts, or LinkedIn posts from Claude Code session logs or external content. Triggers on requests like "generate content from sessions", "write a blog post from my CC logs", "turn this into a post", or when user wants to process CC Insights into publishable content with deaification.
---

# Content Generation Pipeline

Thin dispatcher that orchestrates 7 phases via subagents: Project setup (first run) -> Analyze sessions -> Interactive questions -> Research via Exa MCP -> Draft content -> Deaify with 4 parallel critics + rewriter -> Save to repos.

**For web research (fact-checking, sources): use Exa MCP server. Instruct subagents to call `ToolSearch` with query `"exa"` to load tools, then use `mcp__exa__web_search_exa`.** If Exa MCP is not available, fall back to `WebSearch`/`WebFetch`.

## Arguments

`$ARGUMENTS` - optional:
- Empty: scan session logs for new sessions
- `--external "text or path"`: skip Phase 1, use provided content
- `--setup`: force re-run project setup (Phase 0)
- Path to specific session log file

## Pipeline Overview

```
Phase 0: SETUP (first run only) - interview user, create project config + content structure
    |
Phase 1: ANALYZE (subagent) - scan session logs, extract themes
    |
Phase 2: QUESTIONS (interactive) - theme selection, angle, audience
    |
Phase 3: RESEARCH (subagent + Exa MCP) - sources, fact-check
    |
Phase 4: DRAFT (subagent) - blog + TG + LinkedIn
    |
Phase 5: DEAIFY (4x parallel critics + rewriter) - kill AI markers
    |
Phase 6: SAVE - files to repos + update tracker
```

## Phase 0: PROJECT SETUP (first run / --setup)

**Trigger:** Run automatically on first use in a project (no `.content-pipeline/config.json` found) or when `--setup` is passed.

### Step 1: Project Interview

Ask the user IN CHAT (one question at a time, conversational). Wait for each answer before asking the next.

**Block A - Who you are:**
1. "What's your role? (e.g., developer, designer, PM, founder, marketer, educator, freelancer...)"
2. "What industry/domain are you in? (e.g., SaaS, fintech, e-commerce, AI/ML, education, consulting...)"
3. "How many years of experience? What's your expertise level in this domain?"
4. "What makes your perspective unique? What do you do differently from others in your space?"

**Block B - Your project/brand:**
5. "What's your project/brand about? (1-2 sentences)"
6. "Who's your target audience? Be specific - their role, level, what problems they face"
7. "What value do you give your audience? What do they come to you for?"
8. "Do you have sub-projects or multiple content streams? (e.g., main blog + newsletter + product updates)"

**Block C - Content style:**
9. "What language do you write in? (English, Russian, other?)"
10. "How formal is your tone? (casual/balanced/professional)"
11. "Any specific vocabulary, phrases, or jargon you always use? Words you never use?"
12. "Do you have an existing brand voice guide? (path or 'no')"
13. "What platforms do you publish on? (Telegram, LinkedIn, Twitter, blog, YouTube?)"

**Block D - Structure:**
14. "Where should content files live? (default: `content/`)"
15. "Do you have a blog/site? If yes, what's the URL and blog path structure?"
16. "Do you want session log tracking? (scans CC sessions for content ideas)"
17. "Author name for frontmatter?"
18. "Brief author bio (for LinkedIn context)?"

### Step 1b: Suggest Content Angles

Based on the user's role, domain, audience, and unique perspective, **generate a list of 8-12 content angle suggestions** tailored to their context. Present them as a numbered list and ask the user to pick the ones that resonate, modify them, or add their own.

**Angle generation logic:**

For each angle, consider:
- The user's role (what they do daily that others would learn from)
- Their domain (what's happening in their industry)
- Their audience (what problems the audience needs solved)
- Their unique perspective (what separates them from generic content)

**Example angle sets by role (DO NOT copy these verbatim - generate fresh ones based on actual interview answers):**

*Developer:*
- practical-guide: "How I built X" step-by-step walkthroughs
- tool-review: Hands-on comparison of tools/frameworks
- debugging-story: "This bug took me N hours" post-mortems
- architecture-decision: Why I chose X over Y for real projects
- open-source-contribution: What I learned contributing to X

*Designer:*
- design-process: From brief to final design, showing iterations
- tool-workflow: How I use Figma/tool for specific tasks
- design-system: Building and maintaining design systems
- client-feedback: Navigating revisions and stakeholder input
- trend-analysis: What's actually working vs. what's hype

*Founder/Entrepreneur:*
- build-in-public: Revenue, decisions, failures - transparent
- zero-to-one: How I went from idea to first users
- automation-story: What I automated and time/money saved
- hiring-firing: Team building decisions and lessons
- market-analysis: What I see in my niche that others miss

*Marketer:*
- campaign-breakdown: What worked, what didn't, actual numbers
- channel-strategy: Why I chose these channels over others
- content-experiment: A/B tests and surprising results
- tool-stack: My actual marketing automation setup
- audience-insight: What my audience data tells me

*Educator/Consultant:*
- myth-busting: Common misconceptions in my field
- framework-intro: Mental models I teach my clients
- case-study: Client transformation stories (anonymized)
- behind-the-scenes: How I prepare courses/workshops
- industry-trend: What's changing and how to adapt

After the user confirms their angles, save them to config.

**The user can always add, remove, or rename angles later via `--setup`.**

### Step 2: Create Project Config

Create `.content-pipeline/config.json` in the project root:

```json
{
  "version": "1.0.0",
  "project": {
    "name": "Project Name",
    "description": "What the project is about",
    "language": "en",
    "url": "https://example.com"
  },
  "author": {
    "name": "Author Name",
    "bio": "Brief bio for LinkedIn context"
  },
  "author_role": "developer",
  "domain": "SaaS / AI tooling",
  "experience": "5 years, senior level",
  "unique_perspective": "What makes this author's view different",
  "audience": {
    "primary": "developers",
    "segments": ["developers", "PMs", "AI enthusiasts"],
    "problems": ["How to ship faster with AI", "Which tools actually work"]
  },
  "angles": [
    {"id": "practical-guide", "label": "How I built X - step-by-step walkthroughs"},
    {"id": "tool-review", "label": "Hands-on comparison of tools/frameworks"},
    {"id": "debugging-story", "label": "This bug took me N hours - post-mortems"},
    {"id": "architecture-decision", "label": "Why I chose X over Y for real projects"}
  ],
  "platforms": {
    "blog": true,
    "telegram": true,
    "linkedin": true,
    "twitter": false
  },
  "tone": "balanced",
  "content_dir": "content",
  "blog_url_pattern": "https://example.com/blog/YYYY-MM-DD-slug",
  "session_tracking": true,
  "paths": {
    "brand_voice": ".content-pipeline/brand-voice.md",
    "negative_patterns": ".content-pipeline/negative-patterns.md",
    "session_tracker": ".content-pipeline/session-tracker.json",
    "ideas_inbox": "content/ideas/inbox",
    "ideas_processed": "content/ideas/processed",
    "posts_in_progress": "content/posts/in_progress",
    "posts_scheduled": "content/posts/scheduled",
    "posts_completed": "content/posts/completed"
  }
}
```

### Step 3: Create Content Directory Structure

Based on user's answers, create:

```
content/
  ideas/
    inbox/          # New ideas
    processed/      # Ideas that became posts
  posts/
    in_progress/    # Active drafts (blog.md + telegram.md + linkedin.md)
    scheduled/      # Ready, waiting for publication
    completed/      # Published

.content-pipeline/
  config.json           # Project config (created above)
  brand-voice.md        # Brand voice guide (generated from interview)
  negative-patterns.md  # Prohibited patterns (copied from skill references + user additions)
  session-tracker.json  # Session tracking (if enabled): {"last_scan": null, "sessions": []}
```

### Step 4: Generate Brand Voice Guide

Based on the interview answers, generate `.content-pipeline/brand-voice.md`:
- Use `references/brand-voice-template.md` as the structure
- Fill in with user's actual vocabulary, tone preferences, audience
- Include user's prohibited phrases
- Include examples in user's language

If the user provided an existing brand voice file path, read it and merge with the template structure.

### Step 5: Generate Platform Guides

For each enabled platform, generate a guide in `.content-pipeline/`:
- `telegram-style.md` (from `references/telegram-style-template.md`)
- `linkedin-style.md` (from `references/linkedin-style-template.md`)

Adapt to user's language, tone, and URL patterns.

### Step 6: Confirm Setup

Show the user:
- Created directory structure
- Config summary
- "Setup complete. Run the skill again to generate content."

---

## Reference Files

Read these BEFORE executing phases that need them:

- **Writing rules**: `references/writing-guide.md` - for Phase 4 Writer
- **Deaify rules**: `references/deaify-rules.md` - for Phase 5 Critics + Rewriter
- **Blog format**: `references/blog-format.md` - for Phase 4 Writer
- **Platform adapters**: `references/platform-adapters.md` - for Phase 4 Writer
- **Negative patterns**: project's negative patterns file (from config.paths) - for Phase 4 + Phase 5 (ALWAYS read)
- **Brand voice**: project's brand voice file (from config.paths) - ALWAYS read
- **Platform guides**: project's platform guide files - for platform adapters

## Phase 1: ANALYZE

**Skip if `--external`.**

### Step 1: Read Config

Read `.content-pipeline/config.json` to get paths, platforms, audience, language.

### Step 2: Filter (orchestrator, NOT subagent)

The orchestrator MUST pre-filter session IDs before launching the subagent:

1. Read the session tracker file (from config.paths.session_tracker)
2. Collect ALL `session_ids` from every entry in `sessions[]` array (regardless of status)
3. List `.jsonl` files in the Claude Code project sessions directory
4. Compute diff: new_ids = jsonl_files - tracked_ids
5. If no new sessions found - skip to Phase 2 (show "No new sessions" message)

**The subagent must NOT read the tracker or compute diffs itself. The orchestrator passes only the list of new session file paths.**

### Step 3: Analyze (subagent)

Use Agent tool (subagent_type: "general-purpose"):

Provide the subagent with the EXACT list of new session file paths from Step 2.

Prompt the subagent to:
1. Read ONLY the provided session log files (NOT all .jsonl files)
2. For each new session extract: what was done, tools used, outcome, problems
3. Group related sessions by topic
4. For each topic write expanded description (3-4 sentences): what was done, most interesting finding, potential angle, target audience

Output: numbered list of themes with descriptions.

## Phase 2: QUESTIONS

Interactive phase. Theme selection happens IN CHAT (not AskUserQuestion) because AskUserQuestion only fits 4 options and we often have more themes.

**Step 1:** Show ALL discovered themes in chat as a numbered list with expanded descriptions. Make sure ALL themes are visible - do NOT truncate or omit any.

**Step 2:** Ask the user IN CHAT (plain text): "Which themes to generate? Type numbers. For the rest - skip/inbox."

Wait for the user to reply with their choices. The user will type theme numbers and dispositions for the rest.

**Step 3:** If the user didn't specify disposition for some themes, ask IN CHAT about those remaining themes (generate / skip / save to inbox).

Every session MUST get a resolution. No unprocessed sessions.

**Step 4:** For selected themes, use AskUserQuestion (this fits fine - only 3-4 options per question):
1. Angle: show angles from `config.angles` (these were tailored during onboarding to the user's role and domain). If config has more than 4 angles, show the most relevant ones for this specific theme + "other" option
2. Audience: use segments from `config.audience.segments`
3. Key takeaway (one sentence)

## Phase 3: RESEARCH

Use Agent tool (subagent_type: "general-purpose"):

**For search: use Exa MCP first (preferred), fall back to WebSearch if unavailable.**

In the subagent prompt explicitly instruct to:
1. Call `ToolSearch` with query `"exa"` to load Exa MCP tools
2. Use `mcp__exa__web_search_exa` for searching sources
3. Fall back to `WebSearch`/`WebFetch` only if Exa MCP is not available

Tasks:
1. Find 3-5 relevant sources per topic
2. Verify tool versions mentioned
3. Find similar practices/cases

Output: source list (URL + title + 1-sentence description) + key facts.

## Phase 4: DRAFT

Use Agent tool (subagent_type: "general-purpose"):

Instruct subagent to read: project's brand voice file, `references/writing-guide.md`, `references/blog-format.md`, `references/platform-adapters.md`, project's negative patterns file.

Also read project's platform style guides for each enabled platform.

Provide: topic, angle (with label from config.angles), audience (from config), takeaway, sources from Phase 3, raw session data, project language (from config), author role + domain + unique perspective (from config) - so the writer can frame content from the right professional viewpoint.

Write versions for each enabled platform:
1. **Blog** (600-1200 words) with frontmatter + Sources section
2. **Telegram** (1000-2000 chars) - if enabled in config
3. **LinkedIn** (1000-2000 chars) - if enabled in config

Critical rules: short dash (-) not long (em-dash), first person, specific tool names, min 2 personal elements.

**SEO length checklist (mandatory):**
- **title:** 45-60 characters. Keep room for site suffix if your site adds one.
- **description:** 110-160 characters. Shorter than 110 = poor OG previews. Longer than 160 = truncated in Google SERP.
- Count characters BEFORE saving. If title > 60 or description < 110 - rewrite.

## Phase 5: DEAIFY

### Step 1: Launch 4 critics IN PARALLEL

Read `references/deaify-rules.md` and use prompts from it.

Launch 4 Agent tools simultaneously (subagent_type: "general-purpose"):

- **Critic A** (Generic Detector): cliches, no-specifics sentences, template transitions
- **Critic B** (Rhythm Analyzer): monotone rhythm, same-length sentences, low burstiness
- **Critic C** (Brand Voice): brand voice compliance, add human markers (numbers, trade-offs, uncertainty)
- **Critic D** (Fact Checker): verify claims via Exa MCP, flag OUTDATED/INCORRECT/UNSOURCED. In the subagent prompt explicitly instruct to call `ToolSearch` with query `"exa"` to load Exa MCP tools, then use `mcp__exa__web_search_exa`. Fall back to `WebSearch` if unavailable.

### Step 2: Rewriter

Collect all 4 critic outputs. Use Agent tool (subagent_type: "general-purpose"):

Provide original drafts + all 4 critic reports. Hard rules:
1. Length <= original
2. Delete generic phrases (don't rephrase)
3. Min 2 personal elements
4. Sentence length variation: 3-25+ words
5. Fix all OUTDATED/INCORRECT
6. Update Sources section
7. Short dash (-) everywhere

## Phase 6: SAVE

### Save files

Read paths from config. Determine slug from title (lowercase, hyphens, English).

Save to configured directories:
- Blog -> `{config.paths.posts_in_progress}/YYYY-MM-DD_topic/blog.md`
- Telegram -> `{config.paths.posts_in_progress}/YYYY-MM-DD_topic/telegram.md`
- LinkedIn -> `{config.paths.posts_in_progress}/YYYY-MM-DD_topic/linkedin.md`
- Inbox items -> `{config.paths.ideas_inbox}/topic-name/idea.md`

### Update tracker

If session tracking is enabled, read the tracker JSON and add entries:
- Processed: `"status": "processed"` with `"generated"` paths
- Skipped: `"status": "skipped"`
- Inbox: `"status": "saved_to_inbox"` with `"inbox_path"`

Update `last_scan` to current datetime.

### Move inbox idea to processed

If the content was generated from an inbox idea:
1. After saving all files, move the source idea folder from `config.paths.ideas_inbox` to `config.paths.ideas_processed`
2. Show message: "Idea moved from inbox to processed"

### Show summary

List created files, counts (processed/skipped/inbox), remind about draft->published flow.
