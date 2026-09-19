# Week 16 - Evaluation Results

Agentic feature: iterative re-retrieval + grounded verification (single-agent loop).
Test queries: 7

| ID | Kind | Iters | Tools called | Tool OK | Completed | Failure | Agent tok | Agent $ | Base tok |
|---|---|---|---|---|---|---|---|---|---|
| kb_direct | kb | 2 | search_knowledge_base,finish | yes | yes | - | 3055 | $0.00110 | 923 |
| kb_reword | kb | 2 | search_knowledge_base,finish | yes | yes | - | 3153 | $0.00094 | 830 |
| math | tool | 2 | calculator,finish | yes | yes | - | 961 | $0.00034 | 558 |
| weather | tool | 2 | get_weather,finish | yes | yes | - | 976 | $0.00034 | 595 |
| refuse | refuse | 5 | search_knowledge_base,search_knowledge_base,search_knowledge_base,finish | yes | yes | - | 2348 | $0.00082 | 319 |
| fail_inject | refuse | 5 | search_knowledge_base,finish,finish | yes | yes | - | 3602 | $0.00177 | n/a |
| fail_malformed | refuse | 5 | search_knowledge_base,finish,search_knowledge_base,finish,search_knowledge_base | yes | yes | - | 3790 | $0.00147 | n/a |

## Aggregate metrics

- Task completion rate: 7/7 (100%)
- Avg trajectory length: 3.3 iterations
- Total tokens (agent, all 7 cases): 17885  ($0.0068 at gemini-3.1-flash-lite rates, $0.25/1M in, $1.5/1M out)
- Failure log: none - both injected failures were recognized and safely refused, not fabricated

## Cost accounting vs W15 baseline

Compared on the 5 cases a single-pass W15 pipeline can also run (the 2 injected-failure cases have no baseline).

- Agent: 10493 tokens, $0.0035
- W15 single-pass baseline: 3225 tokens, $0.0011
- Overhead: 7268 tokens, $0.0024 (3.3x tokens) - the price of iterative re-retrieval plus a verification pass per query.
