# Cross-Model Stability — Prompts That Work Everywhere

> How to write prompts that work on GPT, Claude, Gemini without major changes.

## The Problem

Over 60% of prompts fail when moved between models (Stanford HAI research). A prompt optimized for GPT-4 may produce garbage on Claude, and vice versa.

## Core Principles

### 1. Avoid Model-Specific Idioms

**Don't:**
- "Take a deep breath and think step by step" (GPT-specific, does nothing on Claude)
- "Use your training data to..." (implementation detail, not portable)
- "You are ChatGPT/Claude/Gemini" (ties prompt to specific model)

**Do:**
- "Analyze the input following these steps: 1... 2... 3..."
- "Based on the information provided, determine..."
- "You are [role description]" (model-agnostic identity)

### 2. Structure Over Style

Models agree on structure more than prose. Use:
- **Numbered lists** for sequential instructions
- **XML/JSON** for data boundaries
- **Explicit labels** for sections (INSTRUCTIONS, EXAMPLES, RESTRICTIONS)

Claude prefers XML tags. GPT prefers markdown headers. **Both understand numbered lists.** When in doubt, use numbered lists.

### 3. Explicit Over Implicit

What works on GPT-4 implicitly may need to be explicit on smaller models:
- "Return JSON only" → "Return ONLY a valid JSON object. Do not include any text, markdown, or explanations before or after the JSON."
- "Be concise" → "Limit your response to a maximum of 3 sentences."

### 4. Example-Driven Over Rule-Driven

All models improve with examples. When cross-model stability matters:
- Provide 3+ few-shot examples
- Include edge cases in examples
- Show the exact output format in examples (not just describe it)

## Testing Protocol

When building a prompt that must work across models:

1. **Write for the weakest model first** — if it works on mini/haiku, it works everywhere
2. **Test on 3 models minimum** — GPT-4o-mini, Claude Haiku, Gemini Flash
3. **Check these failure modes:**
   - Does it return valid JSON on all models?
   - Does it follow the output format consistently?
   - Does it handle edge cases the same way?
   - Does it respect language rules?
4. **Document model-specific tweaks** in model-recommendations artifact

## JSON Schema Compatibility

| Feature | GPT | Claude | Gemini |
|---------|-----|--------|--------|
| `response_format: json_object` | Yes | Yes | Yes (via config) |
| JSON Schema in API | Yes | Yes | Buggy (use prompt-based) |
| Follows schema from prompt | Good | Excellent | Good |
| Handles nested objects | Good | Good | Sometimes flattens |

**Recommendation:** Always include JSON schema BOTH in the prompt text AND in API parameters. Belt and suspenders.

## How to Apply in EAP Framework

1. Write `<description>` without model-specific language
2. Use numbered `<instructions>` (universally understood)
3. In `<examples>`, show exact output format (not just describe it)
4. In `{agent}-model-recommendations.md`, document any model-specific tweaks needed
5. Test on 3 models before declaring "production ready"
