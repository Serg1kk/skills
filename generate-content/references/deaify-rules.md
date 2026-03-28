# Deaify Rules - Content Pipeline

Rules for 4 critics (Phase 5) and the Rewriter. Each critic receives text and returns a list of issues with quotes.

---

## Critic A: Generic Detector

Task: find AI-typical markers.

Look for:
- Cliches: "it's important to understand", "it should be noted", "in conclusion", "leverage", "facilitate", "it's not X - it's Y"
- Sentences without specific names/numbers/dates
- Abstract statements without examples
- Template transitions: "Let's consider", "Let's move on to", "It's worth noting"
- Em-dash instead of short dash (- vs -)

Output: numbered list `[LINE N]: "quote" -> PROBLEM: description`

## Critic B: Rhythm Analyzer

Task: find monotonous rhythm (AI marker).

Look for:
- 3+ consecutive sentences of similar length (+-5 words)
- Paragraphs where all sentences start the same way
- Burstiness ratio: shortest / longest sentence. Norm: < 0.3 (should have variation from 3 to 25+ words)
- Uniform paragraph structure (all paragraphs have 3 sentences)

EXCEPTION: numbered lists/steps should NOT be flagged.

Output: specific places where variation is needed. Format: `[PARAGRAPH N]: problem description`

## Critic C: Brand Voice + Specificity

Task: check compliance with brand voice guide and add humanity.

Check:
- No lecturing? ("You should", "It's important to understand")
- No cliches? ("Top 10 ways", "AI is changing the world")
- First person? ("I built", not "It was done")
- Short punchy sentences?
- Specific tool names? ("Claude Code" not "AI")

Add humanity (reverse AI detection):
- Where to add specific numbers? ("3 hours", "9 attempts")
- Where to add personal experience? ("I tried and...")
- Where to add trade-off? ("Chose X because Y, although Z")
- Where to add uncertainty? ("not sure yet")

Output: 5-7 specific suggestions WHAT and WHERE to change.

## Critic D: Fact Checker (+ Exa)

Task: verify facts via Exa MCP (or WebSearch as fallback).

**Search tool:** Prefer Exa MCP. Call `ToolSearch` with query `"exa"` to load tools, then use `mcp__exa__web_search_exa`. Fall back to `WebSearch`/`WebFetch` if Exa is not available.

Extract verifiable claims:
- Software/model versions
- Dates and timelines
- Statistics, percentages
- Company/product names

Verify:
- AI models older than 6 months -> `[OUTDATED]`
- Statistics without source -> `[UNSOURCED]`
- Incorrect claim -> `[INCORRECT]` + correct version

If new sources found - add to the list.

Output: `[CLAIM]: "quote" -> [STATUS]: OK / OUTDATED / INCORRECT / UNSOURCED`

---

## Rewriter - Hard Rules

The Rewriter receives original text + all 4 critic reports. Rules:

1. **Length <= original.** Don't inflate the text.
2. **Generic phrases - DELETE.** Don't rephrase - delete.
3. **Minimum 2 personal elements** (numbers from experience, trade-off, mistake, uncertainty).
4. **Sentence length variation:** from 3 words to 25+.
5. **Brand voice compliance.**
6. **All [OUTDATED] and [INCORRECT] - fix** using Critic D data.
7. **Sources section - update** if Critic D found new ones.
8. **Short dash (-)** everywhere. Replace em-dash.
