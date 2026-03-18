# AI Agent Builder

Build, update, and refine AI agents and assistants using the Elite Agent Prompt framework. Generates complete artifact sets for production-ready AI agents.

## What it does

- **Create** new AI agents/assistants from scratch with guided brainstorming
- **Update** existing agent artifacts (prompts, schemas, specs)
- **Help** with specific prompt engineering questions

## Artifacts generated

For each agent, creates 5 files:

| File | Purpose |
|------|---------|
| `{agent}-agent-prompts.txt` | System + User message (XML-structured) |
| `{agent}-agent-input-spec.md` | Input data specification |
| `{agent}-agent-json-schema.json` | Output JSON Schema |
| `{agent}-agent-model-recommendations.md` | Token estimation, model comparison, cost analysis |
| `{agent}-agent-tbd-items.md` | Open questions, decisions log, future enhancements |

## Workflow

```
1. DISCOVERY     — What agent? What task? Read project config if exists
2. INPUT         — Brainstorm input data (format, fields, trade-offs)
3. PROMPT        — Build XML prompt using Elite Agent Prompt framework
4. OUTPUT        — Design JSON Schema, error handling, status codes
5. ARTIFACTS     — Generate 5 files in chosen directory
6. REVIEW        — Iterate until approved
```

## Core framework

Uses **Elite Agent Prompt** as the foundation — XML-structured prompts with:
- Expert positioning (identity-first, primacy effect)
- Numbered instructions
- Chain of Thoughts (step-by-step reasoning)
- What Not To Do (explicit restrictions)
- Few-Shot Examples (desired + undesired behavior)

Enhanced with production techniques:
- 7-Layer Prompt Anatomy (production hardening)
- Anthropic XML best practices
- Cross-model stability patterns
- Input validation & error recovery patterns

## Agent types supported

- **Assistant** — no tools, responds based on input (chatbot, classifier, extractor)
- **Agent** — with tools (reads files, calls APIs, executes code)
- **Pipeline step** — part of a chain (e.g., transcription → tags → insights)
- **Classifier** — categorizes input into predefined types
- **Extractor** — pulls structured data from unstructured input

## Project-specific config

The skill looks for `ai-agent-config.md` in your project root. If found, it uses:
- Default output path
- Project context and conventions
- List of existing agents
- Shared entities and data formats

If not found — works with standard defaults.

## Installation

```bash
cp -r ai-agent-builder ~/.claude/skills/
```

## Trigger phrases

**English:** create agent, build assistant, write system prompt, configure AI node, make chatbot, optimize prompt, update agent, help with prompt

**Russian:** создать агента, сделать ассистента, написать промпт, настроить агента, оптимизировать промпт, обновить агента, помочь с промптом
