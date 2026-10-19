import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

from week18.guards import (check_groundedness, classify_topic, detect_injection, detect_pii,
                           detect_sensitive_output, redact_hits, validate_schema)

BLOCK_INJECTION = "I can't process requests that try to change my instructions."
BLOCK_TOPIC = "I can't help with that request."
BLOCK_TOPIC_HARM = ("I can't help with this. If you're at risk of harming yourself, please contact your local "
                    "emergency services or a crisis line right now.")
FALLBACK = "I couldn't produce a reliable answer from the available information, so I won't guess."
MEDICAL_NOTE = "This is general information, not medical advice. Please consult a qualified professional."
LEGAL_NOTE = "This is general information, not legal advice. Please consult a qualified professional."
FINANCIAL_NOTE = "This is general information, not financial advice."
TOPIC_NOTES = {"medical": MEDICAL_NOTE, "legal": LEGAL_NOTE, "financial": FINANCIAL_NOTE}


@dataclass
class Result:
    query: str
    action: str
    answer: str
    findings: list = field(default_factory=list)
    trace: list = field(default_factory=list)

    def to_dict(self):
        return {"query": self.query, "action": self.action, "answer": self.answer,
                "findings": [f.__dict__ for f in self.findings], "trace": self.trace}


class AuditLog:
    def __init__(self, path=None):
        self.path = path

    def record(self, entry):
        entry = {"ts": datetime.now(timezone.utc).isoformat(), **entry}
        if self.path:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry


def _safe_answer(text, references):
    return {"answer": text, "confidence": 0.0, "citations": list(references)}


def run(query, generate, references=None, audit=None):
    references = references or []
    findings, trace = [], []

    pii = detect_pii(query)
    findings.append(pii)
    if pii.flagged:
        query = redact_hits(query, pii.matched)
        trace.append(f"pii: redacted {pii.detail}")

    injection = detect_injection(query)
    findings.append(injection)
    if injection.flagged:
        trace.append(f"injection: blocked ({injection.detail})")
        res = Result(query, "blocked_injection", BLOCK_INJECTION, findings, trace)
        if audit:
            audit.record(res.to_dict())
        return res

    topic = classify_topic(query)
    findings.append(topic)
    if topic.action == "block":
        trace.append(f"topic: blocked {topic.detail}")
        note = BLOCK_TOPIC_HARM if "self_harm" in topic.matched else BLOCK_TOPIC
        res = Result(query, "blocked_topic", note, findings, trace)
        if audit:
            audit.record(res.to_dict())
        return res

    try:
        raw = generate(query, references)
        trace.append("generate: ok")
    except Exception as exc:
        trace.append(f"generate: failed {type(exc).__name__}")
        res = Result(query, "error_fallback", FALLBACK, findings, trace)
        if audit:
            audit.record(res.to_dict())
        return res

    schema = validate_schema(raw)
    findings.append(schema)
    if schema.flagged:
        trace.append(f"schema: rejected ({schema.detail})")
        res = Result(query, "safe_fallback", FALLBACK, findings, trace)
        if audit:
            audit.record(res.to_dict())
        return res

    answer = raw["answer"]
    grounded = check_groundedness(answer, references)
    findings.append(grounded)
    if grounded.flagged:
        trace.append(f"groundedness: {grounded.detail}")
        res = Result(query, "safe_fallback", FALLBACK, findings, trace)
        if audit:
            audit.record(res.to_dict())
        return res

    leak = detect_sensitive_output(answer)
    findings.append(leak)
    if leak.flagged:
        answer = redact_hits(answer, leak.matched)
        trace.append(f"sensitive_output: redacted {leak.detail}")

    if topic.action == "restrict":
        note = next((TOPIC_NOTES[t] for t in topic.matched if t in TOPIC_NOTES), "")
        if note and note not in answer:
            answer = f"{answer}\n\n{note}"
        trace.append(f"topic: restricted {topic.detail}")

    trace.append("allow")
    res = Result(query, "allow", answer, findings, trace)
    if audit:
        audit.record(res.to_dict())
    return res


def stub_generate(query, references):
    """Deterministic stand-in for the Week 15/16 assistant, so the suite runs with no API key."""
    if not references:
        return _safe_answer("I don't have reference material for that question.", [])
    return {"answer": f"Based on the reference: {references[0]}", "confidence": 0.8, "citations": [references[0]]}
