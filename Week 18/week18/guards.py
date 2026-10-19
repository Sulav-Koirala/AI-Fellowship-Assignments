import re
from dataclasses import dataclass, field

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
PHONE_INTL = re.compile(r"\+\d{1,3}[\s.-]?(?:\d[\s.-]?){6,14}\d")
PHONE_GENERIC = re.compile(r"(?<![\w.])\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?![\w.])")
PHONE_LOCAL = re.compile(r"\b9\d{9}\b")

INJECTION_PATTERNS = [
    (r"\bignore\s+(?:all\s+|any\s+)?(?:previous|prior|above)\s+instructions?\b", 0.9),
    (r"\bdisregard\s+(?:all\s+|any\s+)?(?:previous|prior|above)\s+", 0.9),
    (r"\b(reveal|show|print|repeat)\b.{0,40}\b(system\s+prompt|instructions?|configuration)\b", 0.8),
    (r"\byou\s+are\s+now\b|\bact\s+as\s+(?:a\s+|an\s+)?(?:dan|developer\s+mode|unrestricted)", 0.7),
    (r"\b(bypass|disable|turn\s+off)\b.{0,30}\b(guardrails?|filters?|restrictions?|safety)\b", 0.8),
    (r"\b(jailbreak|prompt\s+injection|developer\s+mode)\b", 0.6),
    (r"\bpretend\s+(?:you|that)\b.{0,40}\b(no|without)\b.{0,20}\b(restrictions?|rules?|guidelines?)\b", 0.7),
]
INJECTION_THRESHOLD = 0.55

SENSITIVE_TOPICS = {
    "self_harm": (r"\b(kill\s+(?:myself|yourself)|suicide|self[- ]harm|end\s+my\s+life)\b", "block"),
    "violence": (r"\b(how\s+to\s+(?:kill|murder|attack)\b|make\s+a\s+bomb|build\s+a\s+weapon)", "block"),
    "medical": (r"\b(diagnos\w*|symptoms?\b|dosage|prescrib\w*|treatment\s+for)\b", "restrict"),
    "legal": (r"\b(legal\s+advice|lawsuit|liable|sue\b|contract\s+law)\b", "restrict"),
    "financial": (r"\b(invest\w*\s+advice|should\s+i\s+(?:buy|sell)\s+stock|guaranteed\s+returns?)\b", "restrict"),
}

SECRETS = [
    (re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"), "api_key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws_key"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{20,}"), "bearer_token"),
    (re.compile(r"(?i)\bpassword\s*[:=]\s*\S+"), "password"),
]

REQUIRED = {"answer": str, "confidence": (int, float), "citations": list}
MAX_ANSWER = 4000
STOPWORDS = set(
    "a an the is are was were be been being of in on at to for from by with and or but if then than that this "
    "these those it its as into over under which who whom whose what when where how do does did done has have "
    "had can could should would may might will shall you your we our they their i my".split()
)


@dataclass
class Finding:
    guard: str
    flagged: bool
    action: str = "allow"
    matched: list = field(default_factory=list)
    score: float = 0.0
    detail: str = ""


def _luhn(digits):
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def detect_pii(text):
    spans = []

    def add(kind, m):
        if not any(s <= m.start() and m.end() <= e for _, _, s, e in spans):
            spans.append((kind, m.group(), m.start(), m.end()))

    for m in EMAIL.finditer(text):
        add("email", m)
    for m in SSN.finditer(text):
        add("ssn", m)
    for m in CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn(digits):
            add("card", m)
    for pattern in (PHONE_INTL, PHONE_GENERIC, PHONE_LOCAL):
        for m in pattern.finditer(text):
            add("phone", m)
    kinds = sorted({k for k, *_ in spans})
    return Finding("pii_input", bool(spans), "redact" if spans else "allow",
                   [v for _, v, *_ in spans], 1.0 if spans else 0.0, ", ".join(kinds) or "none")


def redact_hits(text, hits):
    """Accepts plain strings (from detect_pii) or (kind, value) pairs (from detect_sensitive_output)."""
    values = [h[1] if isinstance(h, tuple) else h for h in hits]
    out = text
    for value in sorted(values, key=len, reverse=True):
        out = out.replace(value, "[REDACTED]")
    return out


def detect_injection(text):
    low = text.lower()
    score, matched = 0.0, []
    for pattern, weight in INJECTION_PATTERNS:
        if re.search(pattern, low):
            matched.append(pattern)
            score = max(score, weight)
    flagged = score >= INJECTION_THRESHOLD
    return Finding("prompt_injection", flagged, "block" if flagged else "allow",
                   matched, round(score, 2), f"score={score:.2f} threshold={INJECTION_THRESHOLD}")


def classify_topic(text):
    low = text.lower()
    hits = {name: action for name, (pattern, action) in SENSITIVE_TOPICS.items() if re.search(pattern, low)}
    if not hits:
        return Finding("sensitive_topic", False, "allow", [], 0.0, "none")
    action = "block" if "block" in hits.values() else "restrict"
    return Finding("sensitive_topic", True, action, sorted(hits), 1.0, ", ".join(sorted(hits)))


def validate_schema(response):
    if not isinstance(response, dict):
        return Finding("schema", True, "reject", [], 1.0, f"response is {type(response).__name__}, not an object")
    errors = []
    for name, kind in REQUIRED.items():
        if name not in response:
            errors.append(f"missing {name}")
        elif not isinstance(response[name], kind):
            errors.append(f"{name} is {type(response[name]).__name__}")
    answer = response.get("answer")
    if isinstance(answer, str) and not 0 < len(answer.strip()) <= MAX_ANSWER:
        errors.append(f"answer length {len(answer)} outside 1..{MAX_ANSWER}")
    conf = response.get("confidence")
    if isinstance(conf, (int, float)) and not 0.0 <= float(conf) <= 1.0:
        errors.append(f"confidence {conf} outside 0..1")
    cites = response.get("citations")
    if isinstance(cites, list) and not all(isinstance(c, str) and c.strip() for c in cites):
        errors.append("citations must be non-empty strings")
    return Finding("schema", bool(errors), "reject" if errors else "allow", errors,
                   1.0 if errors else 0.0, "; ".join(errors) or "valid")


def _terms(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS and len(w) > 1]


def _numbers(text):
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def _claims(answer):
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+|\n+", answer) if p.strip()]


def check_groundedness(answer, references, threshold=0.45):
    if not references:
        return Finding("groundedness", False, "allow", [], 0.0, "no reference supplied")
    ref_text = " ".join(references)
    ref_terms, ref_nums = set(_terms(ref_text)), _numbers(ref_text)
    claims = _claims(answer)
    unsupported, details = [], []
    for claim in claims:
        terms = set(_terms(claim))
        missing = _numbers(claim) - ref_nums
        coverage = len(terms & ref_terms) / len(terms) if terms else 1.0
        bad = []
        if coverage < threshold:
            bad.append(f"coverage {coverage:.2f} < {threshold}")
        if missing:
            bad.append(f"numbers not in reference: {sorted(missing)}")
        if bad:
            unsupported.append(claim)
            details.append("; ".join(bad))
    return Finding("groundedness", bool(unsupported), "regenerate" if unsupported else "allow",
                   unsupported, round(len(unsupported) / max(1, len(claims)), 2),
                   " | ".join(details) or "all claims supported")


def detect_sensitive_output(text):
    pii = detect_pii(text)
    hits = list(pii.matched)
    for pattern, kind in SECRETS:
        hits.extend(m.group() for m in pattern.finditer(text))
        if pattern.search(text):
            hits[-1] = (kind, hits[-1]) if not isinstance(hits[-1], tuple) else hits[-1]
    clean = []
    for h in hits:
        clean.append(h if isinstance(h, tuple) else ("secret", h))
    return Finding("sensitive_output", bool(clean), "redact" if clean else "allow",
                   clean, 1.0 if clean else 0.0, f"{len(clean)} sensitive span(s)")
