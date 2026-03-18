# 7-Layer Prompt Anatomy — Production Insights

> Source: Build Your Fish (buildyourfish.com). 150+ versions, thousands of real interactions.

## Key Insight: Identity First (Primacy Effect)

The first ~200 tokens of your prompt set the framework for everything that follows. Both GPT and Claude weight these tokens heavily.

**"You are a 63-year-old tradie with 40 years' experience" shapes every response.**

Put rules first and identity second? The AI follows rules mechanically.
Put identity first and rules second? The AI inhabits the character and applies rules naturally.

**Lesson for agent building:** The `<description>YOU ARE...</description>` section in EAP should be the FIRST thing the model sees. Make it specific, vivid, and authoritative.

## The 7 Layers

### 1. Identity (First ~200 tokens — CRITICAL)
- Who the agent IS, not what it does
- Specific character, not generic role
- Motivation and worldview
- "You're not programming a robot. You're casting a role."

### 2. Context
- What situation the agent operates in
- What it knows about the world
- Domain knowledge and background

### 3. Rules
- Behavioral guidelines
- Decision-making criteria
- Priority ordering when rules conflict

### 4. Format
- Output structure requirements
- Response length expectations
- Formatting conventions

### 5. Examples
- Desired behavior demonstrations
- Edge case handling
- Error response patterns

### 6. Guardrails
- What NOT to do (aligns with EAP `<restrictions>`)
- Safety boundaries
- Escalation triggers

### 7. Closing
- Final reinforcement of key behaviors
- Recency effect — last instructions get extra weight

## Production Lessons

### The V31 Massacre
"We stripped a production prompt from 450 lines to 180. Removed the personality, the backstory. Accuracy dropped from 78% to 9% in one day. The AI still followed rules. It just had no idea WHY the rules existed."

**Lesson:** Every line in a prompt should exist because something went wrong without it.

### Attention Patterns
- **Primacy effect:** First ~200 tokens weighted most heavily
- **Recency effect:** Last instructions get extra weight
- **Middle sag:** Instructions in the middle get least attention
- **Implication:** Put critical rules at the START and END. Put nice-to-haves in the middle.

## How to Apply in EAP Framework

1. `<description>` — Make it the strongest, most specific section. Not "You are a helpful assistant" but "You are a senior diagnostician with 20 years in emergency medicine who..."
2. `<instructions>` — Number 1 should be input validation (critical). Put most important rules first.
3. `<restrictions>` — Place near the end for recency effect reinforcement
4. `<examples>` — Last section, reinforces the "closing" layer
