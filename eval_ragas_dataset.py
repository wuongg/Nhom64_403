from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class UsageTracker:
    def __init__(self) -> None:
        self.requests: int = 0
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.total_tokens: int = 0

    def add_usage(self, usage: dict[str, Any]) -> None:
        """
        Supports both:
        - OpenAI chat.completions style: {"prompt_tokens":..,"completion_tokens":..,"total_tokens":..}
        - OpenAI responses style: {"input_tokens":..,"output_tokens":..,"total_tokens":..}
        """
        self.requests += 1

        if "prompt_tokens" in usage or "completion_tokens" in usage:
            self.input_tokens += int(usage.get("prompt_tokens") or 0)
            self.output_tokens += int(usage.get("completion_tokens") or 0)
            self.total_tokens += int(usage.get("total_tokens") or 0)
            return

        self.input_tokens += int(usage.get("input_tokens") or 0)
        self.output_tokens += int(usage.get("output_tokens") or 0)
        self.total_tokens += int(usage.get("total_tokens") or 0)


def main() -> int:
    load_dotenv(override=False)

    parser = argparse.ArgumentParser(prog="eval-ragas-dataset")
    parser.add_argument(
        "--dataset",
        type=str,
        default="ragas_dataset_20.json",
        help="Path to dataset JSON created by make_eval_samples.py",
    )
    parser.add_argument("--evaluator-model", type=str, default="gpt-4o-mini")
    parser.add_argument("--out", type=str, default="ragas_eval_20.json", help="Output JSON path")
    parser.add_argument(
        "--price-in-per-1m",
        type=float,
        default=0.0,
        help="Optional: input token price per 1M tokens (USD). If 0, cost is not computed.",
    )
    parser.add_argument(
        "--price-out-per-1m",
        type=float,
        default=0.0,
        help="Optional: output token price per 1M tokens (USD). If 0, cost is not computed.",
    )
    parser.add_argument("--timeout", type=int, default=90, help="Per-request timeout seconds")
    parser.add_argument("--max-retries", type=int, default=2, help="Max retries for failed requests")
    parser.add_argument("--max-workers", type=int, default=8, help="Parallel workers for evaluation")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="If >0, only evaluate first N samples (quick smoke test)",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    obj = json.loads(dataset_path.read_text(encoding="utf-8"))
    samples = obj.get("samples", [])
    if not isinstance(samples, list) or not samples:
        raise SystemExit("Dataset has no samples[].")
    if int(args.limit) > 0:
        samples = samples[: int(args.limit)]

    # Ragas evaluation:
    from ragas import EvaluationDataset, evaluate
    from ragas.llms import llm_factory
    from ragas.metrics import (
        Faithfulness,
        FactualCorrectness,
        LLMContextRecall,
    )
    from ragas.run_config import RunConfig
    from openai import OpenAI
    import httpx

    tracker = UsageTracker()

    def _on_response(resp: httpx.Response) -> None:
        # Best-effort: only inspect OpenAI JSON responses.
        try:
            if resp.status_code < 200 or resp.status_code >= 300:
                return
            ctype = resp.headers.get("content-type", "")
            if "application/json" not in ctype:
                return
            data = resp.json()
            usage = data.get("usage")
            if isinstance(usage, dict):
                tracker.add_usage(usage)
        except Exception:
            # Never fail evaluation due to tracking.
            return

    http_client = httpx.Client(event_hooks={"response": [_on_response]})

    evaluation_dataset = EvaluationDataset.from_list(
        [
            {
                "user_input": s["user_input"],
                "retrieved_contexts": s["retrieved_contexts"],
                # If dataset doesn't have model outputs yet, use reference as a placeholder
                # so we can test the evaluation pipeline end-to-end.
                "response": s.get("response") or s["reference"],
                "reference": s["reference"],
            }
            for s in samples
        ]
    )

    evaluator_llm = llm_factory(args.evaluator_model, client=OpenAI(http_client=http_client))

    # Keep metrics that don't require embeddings to avoid dependency/version issues.
    metrics = [LLMContextRecall(), Faithfulness(), FactualCorrectness()]

    t0 = time.perf_counter()
    run_config = RunConfig(
        timeout=int(args.timeout),
        max_retries=int(args.max_retries),
        max_workers=int(args.max_workers),
    )
    result = evaluate(
        dataset=evaluation_dataset,
        metrics=metrics,
        llm=evaluator_llm,
        run_config=run_config,
        raise_exceptions=True,
        show_progress=True,
    )
    t1 = time.perf_counter()

    try:
        df = result.to_pandas()  # type: ignore[attr-defined]
        base_cols = {"user_input", "retrieved_contexts", "response", "reference"}
        metric_cols = [c for c in df.columns if c not in base_cols]
        agg = {c: float(df[c].mean()) for c in metric_cols}
        per_sample_scores = df[metric_cols].to_dict(orient="records") if metric_cols else []
    except Exception:
        agg = {"raw": repr(result)}
        per_sample_scores = []

    out_obj = {
        "dataset": str(dataset_path),
        "evaluator_model": args.evaluator_model,
        "metrics": agg,
        "per_sample_scores": per_sample_scores,
        "runtime": {
            "seconds_total": float(t1 - t0),
            "samples": int(len(samples)),
            "seconds_per_sample": float((t1 - t0) / max(1, len(samples))),
            "samples_per_second": float(len(samples) / max(1e-9, (t1 - t0))),
        },
        "usage": {
            "requests_tracked": tracker.requests,
            "input_tokens": tracker.input_tokens,
            "output_tokens": tracker.output_tokens,
            "total_tokens": tracker.total_tokens,
        },
    }

    if args.price_in_per_1m > 0 and args.price_out_per_1m > 0:
        out_obj["cost_usd_estimate"] = {
            "input": float(tracker.input_tokens * (args.price_in_per_1m / 1_000_000.0)),
            "output": float(tracker.output_tokens * (args.price_out_per_1m / 1_000_000.0)),
            "total": float(
                tracker.input_tokens * (args.price_in_per_1m / 1_000_000.0)
                + tracker.output_tokens * (args.price_out_per_1m / 1_000_000.0)
            ),
            "price_in_per_1m": float(args.price_in_per_1m),
            "price_out_per_1m": float(args.price_out_per_1m),
        }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out_obj["metrics"], ensure_ascii=False, indent=2))
    print(f"\nSaved: {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

