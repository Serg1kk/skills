# Production Patterns — Hardening AI Agents

> Patterns that work in automated pipelines, not just in chat.

## Pattern 1: Input Validation First

Every production agent must validate input before processing.

```
INSTRUCTION 1: INPUT VALIDATION
- If [field] is empty/missing AND [field] is empty/gibberish → return error status
- If format is invalid → return processing_error
- If valid → proceed to step 2
```

**Why:** In automated pipelines, garbage input is common. Without validation, the agent hallucinates output from bad data — and downstream systems trust it.

## Pattern 2: Structured Status Object

Every response includes a machine-readable status:

```json
{
  "status": {
    "code": "success | error_type_1 | error_type_2",
    "ok": true,
    "message": "Human-readable description (required for errors)"
  },
  "data": { ... }
}
```

**Why:** Downstream systems need to branch on success/failure without parsing natural language.

## Pattern 3: Deterministic Error Codes

Define a finite set of error codes. Don't let the model invent new ones.

```
VALID CODES:
- "success" — processed normally
- "insufficient_content" — input too short or empty
- "invalid_format" — input doesn't match expected structure
- "processing_error" — catch-all for unexpected failures
```

**Why:** If the model can invent error codes, every pipeline run might return something different.

## Pattern 4: Language Handling Rules

For multilingual agents, be explicit:

```
LANGUAGE RULES:
- Output text: in the language specified by languageIsoCode
- Technical terms (API, SaaS, CRM): KEEP ORIGINAL, never translate
- Brand names (Google Ads, Salesforce): KEEP ORIGINAL
- Acronyms: KEEP ORIGINAL
- General concepts: translate to target language
```

**Why:** Without explicit rules, models translate inconsistently — sometimes keeping "API", sometimes writing "интерфейс программирования".

## Pattern 5: Confidence Scoring

When classification or extraction is involved:

```
CONFIDENCE LEVELS:
- "high" (>0.8): Direct match, explicit in content
- "medium" (0.5-0.8): Inferred from context, related content
- "low" (<0.5): Weak signal, speculative
```

**Why:** Downstream systems can filter by confidence. Low-confidence results can be flagged for human review.

## Pattern 6: Output-Only Enforcement

```
INSTRUCTION: Return ONLY valid JSON. No markdown, no explanations, no text outside the JSON structure.
```

**Why:** In pipelines, any text outside JSON breaks the parser. This is the #1 production failure mode.

## Pattern 7: Fallback Strategy

For agents with tools:

```
TOOL USAGE:
1. Try primary tool first
2. If tool returns error → retry once with modified parameters
3. If still fails → return result WITHOUT tool data, mark as "partial"
4. NEVER block on a failed tool call
```

**Why:** In production, external APIs fail. The agent must degrade gracefully.

## How to Apply in EAP Framework

1. **Input validation** → First instruction in `<instructions>`
2. **Status object** → Define in JSON Schema artifact, reference in prompt
3. **Error codes** → Enumerate in `<instructions>`, include error examples in `<examples>`
4. **Language rules** → Add as instruction if multilingual
5. **Output-only** → Add to `<restrictions>`: "NEVER output anything except valid JSON"
6. **Fallbacks** → Add to `<instructions>` for agents with tools
