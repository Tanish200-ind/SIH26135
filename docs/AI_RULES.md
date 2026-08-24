# AI_RULES.md — SIH26135 AI/LLM Assistant Rules (P2, optional)

## 1. Status

The LLM assistant is **P2 / optional**. It will only be added **after** the core system (auth, data, analytics, dashboard) is working — per the approved plan. It is not a Day 1–6 must-have.

## 2. Core rule: the LLM must never invent statistics

- **All statistics come from the application's own analytics** (`analytics/` package → DB). 
- The LLM is given **only** app-computed numbers as context (via the analytics API) and may:
  - rephrase them,
  - summarise them,
  - reason over them,
  - answer questions about them.
- The LLM **must not**:
  - generate/guess numbers, percentages, or totals,
  - claim data that is not present in the prompt context,
  - assert causal impact beyond the outcome-comparison framing in `docs/DATABASE.md`.

## 3. Guardrails in implementation

1. The system prompt explicitly states the rule above.
2. Any numeric context is passed as JSON from the analytics API; no free-typed numbers from the user are accepted as fact.
3. Response template requires the assistant to reference metrics by the same values provided; if a number is not in context, it must say so rather than guess.
4. If the LLM provider fails/returns empty, the dashboard falls back to showing the analytics numbers without the explanation (never fabricate the explanation).
5. The feature stays optional and off-by-default; the demo must work without any AI.

## 4. Why this exists at all (genuine purpose only)

The only genuine purpose: a **government decision-maker** asks a plain-language question ("Which district has the biggest skill gap?") and receives a human-readable explanation built from the app's **real computed metrics** — not from any predictive/ML model. That is the only AI included in this project.