# AI Agent Builder — Design Specification

> **Date:** 2026-03-18
> **Status:** Approved
> **Scope:** Universal Claude Code skill for building AI agents/assistants

---

## Overview

User-level Claude Code skill (`~/.claude/skills/`) that guides users through creating, updating, and refining AI agents/assistants. Uses the Elite Agent Prompt framework as core, enhanced with production techniques from other frameworks.

## Architecture

```
~/.claude/skills/ai-agent-builder/
├── SKILL.md                          ← Main skill file (~3-4k words)
└── references/
    ├── elite-agent-prompt.txt        ← Meta-prompt framework (core)
    ├── elite-agent-readme.md         ← EAP usage instructions
    ├── techniques/
    │   ├── 7-layer-prompt-anatomy.md
    │   ├── anthropic-best-practices.md
    │   ├── production-patterns.md
    │   └── cross-model-stability.md
    └── examples/
        ├── support-bot-example.md
        └── code-review-agent-example.md
```

Source repo: https://github.com/Serg1kk/skills

## Frontmatter

```yaml
name: ai-agent-builder
description: >
  Build, update, and refine AI agents and assistants using the Elite Agent Prompt
  framework. Creates complete artifact sets: system prompts (XML-structured with
  chain-of-thought, restrictions, few-shot examples), input specifications,
  JSON output schemas, model recommendations with token/cost analysis, and
  TBD decision logs. Supports agents with and without tools, pipeline steps,
  classifiers, and extractors.

  Use when: creating AI agent, building assistant, writing system prompt,
  designing AI pipeline step, configuring n8n AI node, making chatbot,
  optimizing existing prompt, updating agent artifacts, help with prompt.

  Использовать когда: создать агента, создать ассистента, сделать агента,
  сделать ассистента, настроить агента, настроить ассистента, написать промпт,
  сделать промпт, оптимизировать промпт, обновить агента, помочь с промптом,
  построить AI пайплайн.
```

## Modes

### Create (default)
Full 6-step pipeline. Result: 5 artifact files in new directory.

### Update
User points to existing artifacts. Skill reads them, asks what to change, focuses on specific artifact(s). Triggered when user provides existing files/folder.

### Help
Focused assistance without generating artifacts. Reads existing files if provided, answers specific questions. Can transition to Update if user wants changes applied.

### Auto-detection
- User provides files/folder with artifacts → Update
- User asks question about a prompt → Help
- User says "create/build/new" → Create
- Unclear → ask

## Workflow (6 Steps)

### Step 1: DISCOVERY
1. Determine mode: Create / Update / Help
2. Search for `ai-agent-config.md` in project root (Glob)
   - Found → read, use as additional context
   - Not found → standard pipeline
3. Read `references/elite-agent-prompt.txt`
4. Ask: "What agent? What task does it solve?"
   - Offer categories: Assistant (no tools), Agent (with tools), Pipeline step, Classifier, Extractor

### Step 2: BRAINSTORM INPUT
1. Ask: "What data comes as input?"
   - Suggest format options (JSON, text, SRT, CSV...) with trade-offs
2. Iteratively clarify (one question per message):
   - "Are there speakers/authors?"
   - "Are timestamps needed?"
   - "Is there existing data (tags, categories, history)?"
3. Lock input-spec (show to user, confirm)

### Step 3: BRAINSTORM PROMPT
1. Read `references/elite-agent-prompt.txt` (core framework)
2. Ask 3-5 questions per EAP framework:
   - Goals and expected results
   - Target audience (who consumes the output)
   - Constraints (speed, cost, model)
   - Edge cases
3. Build XML prompt:
   `<title>` → `<description>` → `<instructions>` → `<chain_of_thoughts>` → `<restrictions>` → `<examples>`
4. Show to user, iterate
5. Pull techniques/ as needed:
   - Agent with tools → `production-patterns.md`
   - Cross-model needed → `cross-model-stability.md`
   - Production deployment → `7-layer-prompt-anatomy.md`

### Step 4: BRAINSTORM OUTPUT
1. Ask: "What should the output be?"
   - Suggest structure (status + data + metadata)
   - Discuss error handling (error codes, messages)
   - Discuss language rules (translate vs keep original)
2. Build JSON Schema
3. Show to user with example outputs
4. Iterate

### Step 5: GENERATE ARTIFACTS
Create 5 files:
1. `{agent}-agent-prompts.txt` — User message (top) + System message (bottom, XML)
2. `{agent}-agent-input-spec.md` — Input specification
3. `{agent}-agent-json-schema.json` — Output JSON Schema
4. `{agent}-agent-model-recommendations.md` — Token estimation, model comparison, cost
5. `{agent}-agent-tbd-items.md` — Open questions, decisions, future enhancements

**Output path selection:**
- Always ask user, but suggest smart defaults:
  - `ai-agents/{agent-name}/` (if no context)
  - Path from `ai-agent-config.md` (if exists)
  - Same folder as existing artifacts (if Update mode)

### Step 6: REVIEW & ITERATE
1. Show summary of all artifacts
2. Ask: "Everything ok? What to change?"
3. Iterate on specific files

## Project-Specific Config

Skill searches for `ai-agent-config.md` in project root. Optional file containing:

```markdown
# AI Agent Config

## Default output path
ai poc/

## Project context
Project description, stack, architecture.

## Conventions
- Prompt language preferences
- JSON schema conventions
- Default model preferences
- Naming conventions

## Existing agents
- List of existing agent folders

## Shared entities
- Common data formats, shared types
```

If not found — standard pipeline, no project-specific behavior.

## Core Framework: Elite Agent Prompt

Stored in `references/elite-agent-prompt.txt`. XML-structured prompts with:

- **Title** — Agent role name
- **Description** — Expert positioning ("YOU ARE...")
- **Instructions** — Numbered step-by-step
- **Chain of Thoughts** — Logical reasoning sequence
- **Restrictions** — "What NOT to do" (NEVER...)
- **Examples** — Desired + Undesired behavior with explanations

## Supplementary Techniques (references/techniques/)

| File | Source | When to use |
|------|--------|-------------|
| `7-layer-prompt-anatomy.md` | Build Your Fish | Identity-first design, primacy effect, production hardening |
| `anthropic-best-practices.md` | Anthropic docs | XML tags for Claude, context engineering for agents |
| `production-patterns.md` | Various | Input validation, error recovery, fallback strategies |
| `cross-model-stability.md` | 4-Layer Framework | Prompts that work across GPT/Claude/Gemini |

Skill uses EAP as core. Techniques are pulled contextually — not mixed into every prompt.

## Examples (references/examples/)

| File | Type | Purpose |
|------|------|---------|
| `support-bot-example.md` | Assistant (no tools) | Shows artifact structure for simple agent |
| `code-review-agent-example.md` | Agent (with tools) | Shows artifact structure for tool-using agent |

## Artifact Format Reference

### {agent}-agent-prompts.txt
```
================================================================================
USER MESSAGE
================================================================================

{{ $json.variableName }}

================================================================================
SYSTEM MESSAGE
================================================================================

<prompt>
<title># AGENT ROLE NAME</title>
<description>YOU ARE...</description>
<instructions>## INSTRUCTIONS\n1. ...\n2. ...</instructions>
<chain_of_thoughts>## CHAIN OF THOUGHTS\n1. ...\n2. ...</chain_of_thoughts>
<restrictions>## WHAT NOT TO DO\n- NEVER...\n- NEVER...</restrictions>
<examples>## FEW-SHOT EXAMPLES\nDesired: ...\nUndesired: ...</examples>
</prompt>
```

### {agent}-agent-input-spec.md
- Variable name and format
- Data structure with examples
- Constraints (min/max, encoding, required/optional)
- Data source

### {agent}-agent-json-schema.json
- Status object (code, ok, message, detectedLanguage)
- Domain-specific output fields
- Required vs optional
- Success and error examples

### {agent}-agent-model-recommendations.md
- Token estimation table (by input size)
- Model comparison (context, price, quality, speed)
- Cost per request calculations
- Temperature recommendations
- MVP / Production / Premium tiers

### {agent}-agent-tbd-items.md
- Open questions (with options and recommendations)
- Decisions made (with date and rationale)
- Future enhancements (phased)
