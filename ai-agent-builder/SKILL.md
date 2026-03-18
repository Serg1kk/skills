---
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
---

# AI Agent Builder

Build production-ready AI agents and assistants through guided brainstorming. Uses the Elite Agent Prompt framework as core, enhanced with production techniques.

## Quick Reference

| Resource | When to read |
|----------|-------------|
| `references/elite-agent-prompt.txt` | Step 3 — always read before building prompt |
| `references/elite-agent-readme.md` | Step 3 — framework usage instructions |
| `references/techniques/7-layer-prompt-anatomy.md` | When building production agents |
| `references/techniques/anthropic-best-practices.md` | When targeting Claude models |
| `references/techniques/production-patterns.md` | When agent has tools or runs in pipeline |
| `references/techniques/cross-model-stability.md` | When prompt must work across models |
| `references/examples/support-bot-example.md` | Example: assistant without tools |
| `references/examples/code-review-agent-example.md` | Example: agent with tools |

---

## Step 0: Initialization

### Determine mode

1. If user provided existing artifact files/folder → **Update** mode
2. If user asks a question about a prompt → **Help** mode
3. Otherwise → **Create** mode (default)

If unclear, ask:
> What are we doing? (A) Creating a new agent from scratch, (B) Updating an existing one, (C) Need help with a specific prompt question

### Load project config

Search for `ai-agent-config.md` in the project root (Glob `**/ai-agent-config.md`).
- Found → read it, use as additional context (default path, conventions, existing agents)
- Not found → standard pipeline, no project-specific behavior

### Mode-specific behavior

**Create:** Follow Steps 1-6 fully.

**Update:**
1. Read all existing artifacts the user pointed to
2. Ask: "What are we changing?" — suggest options: Input, Prompt, Output, Model recommendations
3. Focus on the specific artifact, apply changes, show diff
4. Skip steps that aren't affected

**Help:**
1. Read existing files if provided
2. Answer the specific question
3. If changes needed, offer: "Want me to update the file?" → switch to Update

---

## Step 1: DISCOVERY

Ask the user about the agent. One question at a time.

**First question:**
> What agent/assistant are we building? What task does it solve?

**Then classify the agent type** (suggest to user):
- **Assistant** — no tools, responds based on input (chatbot, Q&A, summarizer)
- **Agent** — with tools (reads files, calls APIs, executes actions)
- **Pipeline step** — part of a processing chain (e.g., step between transcription and storage)
- **Classifier** — categorizes input into predefined types
- **Extractor** — pulls structured data from unstructured input

The agent type influences which techniques to apply later.

---

## Step 2: BRAINSTORM INPUT

Brainstorm what data the agent receives. Ask one question at a time.

**Start with:**
> What data comes as input to this agent? (format: JSON, plain text, SRT, CSV, etc.)

**Then iteratively clarify:**
- What fields/structure does the input have?
- Are there optional vs required fields?
- Is there existing/historical data the agent should reference? (e.g., existing tags, categories)
- What are the constraints? (min/max size, encoding, language)
- Where does the data come from? (API, user input, previous pipeline step)

**For each question:**
- Offer 2-3 variants with trade-offs when applicable
- Explain pros/cons of each variant
- Let the user choose, ask follow-ups

**Lock the input spec:**
Show the user a summary of the agreed input specification. Get explicit confirmation before moving on.

---

## Step 3: BRAINSTORM PROMPT

**Read `references/elite-agent-prompt.txt` before this step.** This is the core framework.

### 3.1 Gather information (EAP framework requirement — MANDATORY)

Ask 3-5 questions. One at a time. These are required by the framework:

1. **Goals:** What specific results should the agent produce? What does "good output" look like?
2. **Audience:** Who consumes the output? (humans, another system, API consumer)
3. **Constraints:** Speed requirements? Cost limits? Specific model? Token budget?
4. **Edge cases:** What weird inputs might come? How should the agent handle them?
5. **Language:** What language should the output be in? Technical terms — translate or keep original?

Use information already gathered in Steps 1-2. Don't re-ask what's known.

### 3.2 Build the prompt

Construct the XML-structured prompt following EAP:

```xml
<prompt>
<title># [AGENT ROLE NAME]</title>
<description>YOU ARE [expert positioning]...</description>
<instructions>
## INSTRUCTIONS
1. [Input validation — always first]
2. [Core processing steps]
3. [Output formatting — always last]
</instructions>
<chain_of_thoughts>
## CHAIN OF THOUGHTS
1. [Step 1 with sub-steps]
   1.1. [Sub-step]
...
</chain_of_thoughts>
<restrictions>
## WHAT NOT TO DO
- NEVER [specific restriction with reason]
...
</restrictions>
<examples>
## FEW-SHOT EXAMPLES

Desired Example 1: [title]
Input: [realistic input]
Output: [correct output]
Why: [brief explanation]

Desired Example 2: [different scenario]
...

Undesired Example 1: [title]
Input: [input]
Output: [wrong output]
Why this is wrong: [explanation]
</examples>
</prompt>
```

### 3.3 Apply techniques (contextual)

Based on agent type, pull relevant techniques:

| Agent type | Read | Key takeaway |
|-----------|------|-------------|
| Any | `7-layer-prompt-anatomy.md` | Identity first (primacy effect), first ~200 tokens set the framework |
| Agent with tools | `production-patterns.md` | Input validation, error recovery, tool fallbacks |
| Must work on GPT + Claude + Gemini | `cross-model-stability.md` | Avoid model-specific idioms |
| Targeting Claude specifically | `anthropic-best-practices.md` | XML tag patterns, thinking blocks |

### 3.4 Review with user

Show the complete prompt. Ask:
> Here's the prompt. What do you think? Anything to change?

Iterate until approved.

---

## Step 4: BRAINSTORM OUTPUT

Design what the agent returns. Ask one question at a time.

**Start with:**
> What should the agent output? Let me suggest a structure:
>
> ```json
> {
>   "status": { "code": "success", "ok": true, "message": "" },
>   "data": { ... },
>   "metadata": { ... }
> }
> ```
> Does this pattern work, or do you need something different?

**Then clarify:**
- What fields in the data section?
- What error codes are needed? (suggest based on input validation from Step 2)
- Language rules for output text? (translate vs keep original for technical terms)
- Confidence scores needed?

**Build the JSON Schema:**
- All required/optional fields with types
- Enums for status codes
- String length constraints
- Array min/max items
- Include success AND error examples

**Show to user with examples** — both successful output and error output. Get confirmation.

---

## Step 5: GENERATE ARTIFACTS

Create 5 files in the chosen directory.

### Ask for output path

> Where should I save the artifacts? Suggestions:
> - `ai-agents/{agent-name}/` (default)
> - [path from ai-agent-config.md if exists]
> - [other path if user provided context]

### Files to create

**1. `{agent}-agent-prompts.txt`**

```
================================================================================
USER MESSAGE
================================================================================

{{ $json.variableName }}


================================================================================
SYSTEM MESSAGE
================================================================================

<prompt>
...the XML prompt from Step 3...
</prompt>
```

User message on top (n8n convention). System message below with full XML prompt.

**2. `{agent}-agent-input-spec.md`**

From Step 2: variable name, format, structure with examples, constraints, data source.

**3. `{agent}-agent-json-schema.json`**

From Step 4: formal JSON Schema with all fields, types, constraints, examples.

**4. `{agent}-agent-model-recommendations.md`**

Calculate based on the prompt and input:
- Token estimation table (by typical input sizes)
- Model comparison table (context window, input/output price, quality, speed)
- Cost per request for top 3-5 models
- Temperature recommendations (production vs testing vs creative)
- Final recommendations: MVP / Production / Premium tiers

**5. `{agent}-agent-tbd-items.md`**

Collect from the brainstorming process:
- Open questions that came up but weren't resolved
- Decisions made (with date and rationale)
- Alternative approaches discussed but rejected (with reasons)
- Future enhancements (phased: Phase 2, Phase 3)

---

## Step 6: REVIEW & ITERATE

Show summary of all created artifacts:

> Created 5 artifacts in `{path}`:
> 1. `{agent}-agent-prompts.txt` — System + User prompt
> 2. `{agent}-agent-input-spec.md` — Input: {brief description}
> 3. `{agent}-agent-json-schema.json` — Output: {brief description}
> 4. `{agent}-agent-model-recommendations.md` — Recommended: {model} at ${cost}/request
> 5. `{agent}-agent-tbd-items.md` — {N} open questions, {N} decisions
>
> Everything look good? What to change?

Iterate on specific files until the user is satisfied.

---

## Critical Rules

1. **One question at a time** — never overwhelm with multiple questions in one message
2. **Offer variants with trade-offs** — don't just ask, suggest 2-3 options when applicable
3. **EAP framework is mandatory** — always read `elite-agent-prompt.txt` before building prompts
4. **5 artifacts always** — never skip any of the 5 files in Create mode
5. **User language** — respond in the language the user writes in
6. **Confirm before moving on** — lock each step before proceeding to the next
7. **Progressive disclosure** — read technique files only when relevant, not all at once
8. **Input validation first** — every agent prompt starts with input validation in instructions
9. **Examples required** — every prompt includes at least 2 desired + 1 undesired example
10. **Never invent constraints** — if unsure about a requirement, ask the user
