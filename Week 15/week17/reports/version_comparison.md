# Track B - Prompt Version Regression (Evidently LLM-as-judge)

Judge: `gemini-3.1-flash-lite` via the Gemini OpenAI-compatible endpoint, scored with Evidently's CorrectnessLLMEval (vs golden reference) and DeclineLLMEval (refusal appropriateness).
v1, v2, v3 tie at 80% on this 5-case set, so pass rate alone does not separate them; cheapest of the tie is **v1**. See the README for the cost/robustness read.

| Version | pct_tests_passed | Passed | Tokens | What changed |
|---|---|---|---|---|
| v1 | 80% | 4/5 | 6731 | terse baseline: no grounding/refusal rule, no reword-and-retry, k=2, hot |
| v2 | 80% | 4/5 | 9350 | adds grounding + refusal discipline + reword-and-retry, k=4 |
| v3 | 80% | 4/5 | 10514 | v2 + explicit verification discipline (current agent prompt), k=6 |
