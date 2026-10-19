import json
import sys
from collections import OrderedDict
from pathlib import Path

from week18.cases import CASES
from week18.pipeline import run, stub_generate

REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"
GUARD_ORDER = ["pii_input", "prompt_injection", "sensitive_topic", "schema", "groundedness", "sensitive_output"]


def case_generator(case):
    """Per-case generator: return the case's canned response, so output guards test the case, not the stub.
    Cases with response=None (input-only cases) fall back to the deterministic stub."""
    if case["response"] is None:
        return stub_generate
    canned = case["response"]
    return lambda query, references: canned


def evaluate_case(case):
    try:
        result = run(case["query"], case_generator(case), case["references"])
    except Exception as exc: 
        return {"id": case["id"], "guard": case["guard"], "expected_flagged": case["expect_flagged"],
                "expected_action": case["expect_action"], "actual_flagged": None,
                "actual_action": f"CRASH {type(exc).__name__}: {exc}", "reached": False,
                "passed": False, "outcome": "crash", "detail": "", "trace": [], "answer": ""}
    finding = next((f for f in result.findings if f.guard == case["guard"]), None)
    reached = finding is not None
    flagged = bool(finding.flagged) if reached else False
    exp = case["expect_flagged"]
    if not reached:
        outcome = "not_reached"
    elif exp and flagged:
        outcome = "TP"
    elif exp and not flagged:
        outcome = "FN"
    elif not exp and flagged:
        outcome = "FP"
    else:
        outcome = "TN"
    passed = reached and flagged == exp and result.action == case["expect_action"]
    return {"id": case["id"], "guard": case["guard"], "expected_flagged": exp,
            "expected_action": case["expect_action"], "actual_flagged": flagged if reached else None,
            "actual_action": result.action, "reached": reached, "passed": passed, "outcome": outcome,
            "detail": finding.detail if reached else "guard never ran (pipeline stopped earlier)",
            "trace": result.trace, "answer": result.answer,
            "query": case["query"], "references": case["references"]}


def _div(a, b):
    return a / b if b else None


def metrics(rows):
    out = OrderedDict()
    for guard in GUARD_ORDER:
        sub = [r for r in rows if r["guard"] == guard]
        tp = sum(r["outcome"] == "TP" for r in sub)
        fp = sum(r["outcome"] == "FP" for r in sub)
        fn = sum(r["outcome"] == "FN" for r in sub)
        tn = sum(r["outcome"] == "TN" for r in sub)
        nr = sum(r["outcome"] in ("not_reached", "crash") for r in sub)
        p, rc = _div(tp, tp + fp), _div(tp, tp + fn)
        f1 = _div(2 * p * rc, p + rc) if p is not None and rc is not None and (p + rc) else None
        out[guard] = {"n": len(sub), "TP": tp, "FP": fp, "FN": fn, "TN": tn, "not_reached": nr,
                      "precision": p, "recall": rc, "f1": f1,
                      "case_pass": sum(r["passed"] for r in sub)}
    return out


def fmt(x):
    return "n/a" if x is None else f"{x:.2f}"


def render_markdown(rows, m):
    total = len(rows)
    passed = sum(r["passed"] for r in rows)
    L = ["# Week 18 evaluation report", "",
         f"**{passed}/{total} cases passed** (a case passes only if the guard's flag AND the final pipeline "
         "action both match the expectation).", "",
         "## Per-guard metrics", "",
         "| Guard | Cases | TP | FP | FN | TN | Precision | Recall | F1 | Cases passed |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for g, v in m.items():
        L.append(f"| {g} | {v['n']} | {v['TP']} | {v['FP']} | {v['FN']} | {v['TN']} | {fmt(v['precision'])} | "
                 f"{fmt(v['recall'])} | {fmt(v['f1'])} | {v['case_pass']}/{v['n']} |")
    tp = sum(v["TP"] for v in m.values()); fp = sum(v["FP"] for v in m.values())
    fn = sum(v["FN"] for v in m.values())
    p, rc = _div(tp, tp + fp), _div(tp, tp + fn)
    f1 = _div(2 * p * rc, p + rc) if p and rc else None
    L += ["", f"**Micro-average:** precision {fmt(p)}, recall {fmt(rc)}, F1 {fmt(f1)} "
              f"(TP={tp}, FP={fp}, FN={fn}).", "",
          "## Every test case", "",
          "| # | Case | Guard | Expected flag / action | Actual flag / action | Outcome | Result |",
          "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        L.append(f"| {i} | {r['id']} | {r['guard']} | {r['expected_flagged']} / {r['expected_action']} | "
                 f"{r['actual_flagged']} / {r['actual_action']} | {r['outcome']} | "
                 f"{'PASS' if r['passed'] else 'FAIL'} |")
    fails = [r for r in rows if not r["passed"]]
    L += ["", "## Failing cases", ""]
    if not fails:
        L.append("None.")
    for r in fails:
        L += [f"### {r['id']} ({r['outcome']})",
              f"- Query: `{r.get('query', '')}`",
              f"- Expected: flagged={r['expected_flagged']}, action={r['expected_action']}",
              f"- Actual: flagged={r['actual_flagged']}, action={r['actual_action']}",
              f"- Guard detail: {r['detail']}", f"- Trace: {r['trace']}", ""]
    return "\n".join(L) + "\n"


def main():
    rows = [evaluate_case(c) for c in CASES]
    m = metrics(rows)
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "results.json").write_text(
        json.dumps({"cases": rows, "metrics": m}, indent=2, ensure_ascii=False), encoding="utf-8")
    md = render_markdown(rows, m)
    (REPORT_DIR / "evaluation_report.md").write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    return 0 if all(r["passed"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
