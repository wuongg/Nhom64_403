from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from dotenv import load_dotenv

from app.kb import load_from_raw_folder, retrieve
from app.llm import chat_openai
from app.prompting import build_prompt
from app.role_llm import decide_role_with_llm
from app.role_tree import decide_role


def _extract_reference_from_kb_text(kb_text: str) -> str:
    """
    kb_text comes from kb_raw.load_raw_folder(), formatted like:
      Đối tượng: ...
      Chủ đề: ...
      Câu hỏi: ...
      Trả lời: <answer>
    """
    marker = "Trả lời:"
    i = kb_text.find(marker)
    if i < 0:
        return kb_text.strip()
    return kb_text[i + len(marker) :].strip()


def main() -> int:
    load_dotenv(override=False)

    parser = argparse.ArgumentParser(prog="eval-ragas")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=str(Path(__file__).resolve().parent / "raw"),
        help="Path to raw/ markdown KB folder",
    )
    parser.add_argument("--k", type=int, default=5, help="Top-k KB chunks to retrieve")
    parser.add_argument("--n", type=int, default=30, help="Number of queries to evaluate (sampled)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--role-mode",
        type=str,
        choices=["rule", "llm"],
        default="rule",
        help="Role decision mode for evaluation queries",
    )
    parser.add_argument("--answer-model", type=str, default="gpt-4.1-mini")
    parser.add_argument("--evaluator-model", type=str, default="gpt-4.1-mini")
    parser.add_argument("--out", type=str, default="ragas_results.json", help="Output JSON path")
    args = parser.parse_args()

    entries = load_from_raw_folder(args.raw_dir)
    if not entries:
        raise SystemExit(f"No KB entries found under raw dir: {args.raw_dir}")

    rnd = random.Random(args.seed)
    pool = [e for e in entries if e.question.strip()]
    rnd.shuffle(pool)
    picked = pool[: min(args.n, len(pool))]

    # Build the evaluation dataset expected by ragas (per their guide).
    dataset: list[dict] = []
    for e in picked:
        query = e.question.strip()

        if args.role_mode == "llm":
            decision = decide_role_with_llm(query, model=args.answer_model)
        else:
            decision = decide_role(query)

        hits = retrieve(entries, query, role=decision.role, k=args.k)
        prompt = build_prompt(decision, query, hits)

        response = chat_openai(prompt.system, prompt.user, model=args.answer_model)
        retrieved_contexts = [h.text for h in hits]
        reference = _extract_reference_from_kb_text(e.text)

        dataset.append(
            {
                "user_input": query,
                "retrieved_contexts": retrieved_contexts,
                "response": response,
                "reference": reference,
                "meta": {
                    "role": decision.role,
                    "safety": decision.safety,
                    "reason": decision.reason,
                },
            }
        )

    # Ragas evaluation (based on their get-started guide):
    # https://docs.ragas.io/en/stable/getstarted/rag_eval/
    from ragas import EvaluationDataset, evaluate
    from ragas.metrics import (
        AnswerRelevancy,
        ContextPrecision,
        Faithfulness,
        FactualCorrectness,
        LLMContextRecall,
        ResponseRelevancy,
    )
    from ragas.llms import llm_factory
    from openai import OpenAI

    # Prefer ragas-native OpenAI adapter (more stable than langchain wrapper).
    evaluator_llm = llm_factory(args.evaluator_model, client=OpenAI())
    evaluation_dataset = EvaluationDataset.from_list(
        [
            {
                "user_input": d["user_input"],
                "retrieved_contexts": d["retrieved_contexts"],
                "response": d["response"],
                "reference": d["reference"],
            }
            for d in dataset
        ]
    )

    result = evaluate(
        dataset=evaluation_dataset,
        metrics=[
            LLMContextRecall(),
            ContextPrecision(),
            Faithfulness(),
            FactualCorrectness(),
            AnswerRelevancy(),
            ResponseRelevancy(),
        ],
        llm=evaluator_llm,
    )

    # `result` API differs slightly across ragas versions.
    # Convert to a simple dict of aggregate metrics + keep per-sample scores when available.
    try:
        df = result.to_pandas()  # type: ignore[attr-defined]
        base_cols = {"user_input", "retrieved_contexts", "response", "reference"}
        metric_cols = [c for c in df.columns if c not in base_cols]
        metrics = {c: float(df[c].mean()) for c in metric_cols}
        per_sample_scores = df[metric_cols].to_dict(orient="records") if metric_cols else []
    except Exception:
        metrics = {"raw": repr(result)}
        per_sample_scores = []

    if per_sample_scores:
        for i, s in enumerate(per_sample_scores):
            dataset[i]["scores"] = s

    out_obj = {
        "config": {
            "raw_dir": args.raw_dir,
            "k": args.k,
            "n": len(dataset),
            "seed": args.seed,
            "role_mode": args.role_mode,
            "answer_model": args.answer_model,
            "evaluator_model": args.evaluator_model,
        },
        "metrics": metrics,
        "samples": dataset,
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out_obj["metrics"], ensure_ascii=False, indent=2))
    print(f"\nSaved: {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

