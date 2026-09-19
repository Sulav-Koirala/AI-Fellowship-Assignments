# Skill: verify_answer

## Purpose
Check whether a draft answer is fully supported by the evidence gathered in the
ledger, before it is returned to the user.

## When to load
Only at the verification step of the agent loop, once a draft answer exists. It
is not needed while evidence is still being gathered, so its full instructions
stay out of the context window until that point.

## Procedure
1. List every factual claim the draft answer makes.
2. For each claim, look for a supporting passage in the evidence ledger.
3. Decide the verdict:
   - OK - every claim is backed by the ledger, or the draft correctly states that
     the knowledge base does not contain the answer.
   - INSUFFICIENT - a claim is unsupported, the ledger is empty or garbled, or the
     answer leans on outside knowledge.
4. If INSUFFICIENT, give a one-line reason naming what is missing so the agent
   knows what to search for next.

## Output
Return ONLY a JSON object: {"verdict": "OK" | "INSUFFICIENT", "reason": string}
