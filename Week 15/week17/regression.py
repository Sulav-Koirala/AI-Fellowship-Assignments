import asyncio
import json
import os

import pandas as pd
import mlflow
from evidently import Dataset, Report
from evidently.presets import TextEvals
from evidently.descriptors import CorrectnessLLMEval, DeclineLLMEval
from evidently.llm.options import OpenAIOptions

from app.config import PRIMARY
from week17.prompts import VERSIONS

import openai
from evidently.llm.utils import wrapper as _ew


async def _complete_no_seed(self, messages, seed=None):  # Gemini's OpenAI-compat endpoint 400s on the seed field Evidently sends; also back off on free-tier 429s
    msgs = [{"role": m.role, "content": m.content} for m in messages]
    for attempt in range(5):
        try:
            resp = await self.client.chat.completions.create(model=self.model, messages=msgs)
            break
        except openai.RateLimitError as e:
            if attempt == 4:
                raise _ew.LLMRateLimitError(e.message) from e
            await asyncio.sleep(25)
        except openai.APIError as e:
            raise _ew.LLMRequestError(f"Failed to call OpenAI complete API: {e.message}", original_error=e) from e
    content = resp.choices[0].message.content
    if resp.usage is None:
        return _ew.LLMResult(content, 0, 0)
    return _ew.LLMResult(content, resp.usage.prompt_tokens, resp.usage.completion_tokens)


_ew.OpenAIWrapper.complete = _complete_no_seed

HERE = os.path.dirname(__file__)
REPORTS = os.path.join(HERE, "reports")
TRACKING_URI = "sqlite:///mlflow.db"
EXPERIMENT = "assistant_prompt_regression"
CORRECT_LABELS, DECLINE_LABELS = {"CORRECT", "INCORRECT"}, {"DECLINE", "OK"}


def _cat_col(df, labels):
    for c in df.columns:
        vals = {str(v).upper() for v in df[c].dropna().unique()}
        if vals and vals <= labels:
            return c
    return None


def _passed(kind, corr, dec):
    if kind == "refuse":
        return str(dec).upper() == "DECLINE"
    return str(corr).upper() == "CORRECT"


def judge(vrows, opts, model):
    df = pd.DataFrame([{"id": r["id"], "kind": r["kind"], "query": r["query"],
                        "reference": r["reference"], "answer": r["answer"]} for r in vrows])
    return Dataset.from_pandas(df, descriptors=[
        CorrectnessLLMEval("answer", target_output="reference", provider="openai", model=model,
                           alias="correctness", include_category=True, include_reasoning=True),
        DeclineLLMEval("answer", provider="openai", model=model,
                       alias="decline", include_category=True, include_reasoning=True),
    ], options=opts)


def _export(summary):
    summary.sort(key=lambda s: (-s[1], s[3]))
    top = [s for s in summary if s[1] == summary[0][1]]
    n = summary[0][4]
    if len(top) == 1:
        rec = f"Recommended prompt: **{top[0][0]}** - highest pass rate ({top[0][1]:.0f}%)."
    else:
        cheapest = min(top, key=lambda t: t[3])[0]
        rec = (f"{', '.join(t[0] for t in top)} tie at {top[0][1]:.0f}% on this {n}-case set, so pass rate alone "
               f"does not separate them; cheapest of the tie is **{cheapest}**. See the README for the cost/robustness read.")
    lines = ["# Track B - Prompt Version Regression (Evidently LLM-as-judge)", "",
             f"Judge: `{PRIMARY['model']}` via the Gemini OpenAI-compatible endpoint, scored with Evidently's "
             f"CorrectnessLLMEval (vs golden reference) and DeclineLLMEval (refusal appropriateness).",
             rec, "",
             "| Version | pct_tests_passed | Passed | Tokens | What changed |",
             "|---|---|---|---|---|"]
    for vid, pct, npass, tok, n in summary:
        lines.append(f"| {vid} | {pct:.0f}% | {npass}/{n} | {tok} | {VERSIONS[vid]['note']} |")
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, "version_comparison.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n" + "\n".join(lines))


def main():
    opts = OpenAIOptions(api_key=PRIMARY["api_key"], api_url=PRIMARY["base_url"], rpm_limit=10)
    model = PRIMARY["model"]
    os.makedirs(REPORTS, exist_ok=True)
    rows = [json.loads(l) for l in open(os.path.join(HERE, "answers.jsonl"), encoding="utf-8")]
    by_ver = {}
    for r in rows:
        by_ver.setdefault(r["version"], []).append(r)

    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)
    summary, verdicts = [], []
    for vid, vrows in by_ver.items():
        ds = judge(vrows, opts, model)
        jdf = ds.as_dataframe()
        cc, dc = _cat_col(jdf, CORRECT_LABELS), _cat_col(jdf, DECLINE_LABELS)
        vrec = []
        for i, r in enumerate(vrows):
            corr = str(jdf[cc].iloc[i]) if cc else ""
            dec = str(jdf[dc].iloc[i]) if dc else ""
            vrec.append({"version": vid, "id": r["id"], "kind": r["kind"],
                         "correctness": corr, "decline": dec, "passed": bool(_passed(r["kind"], corr, dec))})
        passed = [v["passed"] for v in vrec]
        pct = 100.0 * sum(passed) / len(passed)
        Report([TextEvals()]).run(ds).save_html(os.path.join(REPORTS, f"regression_{vid}.html"))
        tok = sum(r["tokens"]["total"] for r in vrows)
        with mlflow.start_run(run_name=vid):
            mlflow.log_param("version", vid)
            mlflow.log_param("judge_model", model)
            mlflow.log_metrics({"pct_tests_passed": pct, "n_passed": sum(passed),
                                "n_tests": len(passed), "total_tokens": tok})
            mlflow.log_artifact(os.path.join(REPORTS, f"regression_{vid}.html"))
        summary.append((vid, pct, sum(passed), tok, len(passed)))
        verdicts.extend(vrec)
        print(f"[{vid}] pct_tests_passed={pct:.0f}% ({sum(passed)}/{len(passed)}) tokens={tok}")
        for v in vrec:
            print(f"  {v['id']:12} kind={v['kind']:7} correctness={v['correctness']:9} decline={v['decline']:7} -> {'PASS' if v['passed'] else 'FAIL'}")
    with open(os.path.join(REPORTS, "verdicts.jsonl"), "w", encoding="utf-8") as f:
        for v in verdicts:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")
    _export(summary)


if __name__ == "__main__":
    main()
