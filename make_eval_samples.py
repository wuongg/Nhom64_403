from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from app.kb import load_from_raw_folder, retrieve
from app.role_llm import decide_role_with_llm
from app.role_tree import decide_role


def _extract_reference_from_kb_text(kb_text: str) -> str:
    marker = "Trả lời:"
    i = kb_text.find(marker)
    if i < 0:
        return kb_text.strip()
    return kb_text[i + len(marker) :].strip()


def main() -> int:
    parser = argparse.ArgumentParser(prog="make-eval-samples")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=str(Path(__file__).resolve().parent / "raw"),
        help="Path to raw/ markdown KB folder",
    )
    parser.add_argument("--k", type=int, default=5, help="Top-k KB chunks to retrieve")
    parser.add_argument("--n", type=int, default=20, help="Number of samples to generate")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--role-mode",
        type=str,
        choices=["rule", "llm"],
        default="rule",
        help="Role decision mode for evaluation queries",
    )
    parser.add_argument("--role-model", type=str, default="gpt-4.1-mini")
    parser.add_argument("--out", type=str, default="ragas_dataset_20.json", help="Output JSON path")
    args = parser.parse_args()

    entries = load_from_raw_folder(args.raw_dir)
    if not entries:
        raise SystemExit(f"No KB entries found under raw dir: {args.raw_dir}")

    rnd = random.Random(args.seed)
    pool = [e for e in entries if e.question.strip()]
    rnd.shuffle(pool)
    picked = pool[: min(args.n, len(pool))]

    samples: list[dict] = []
    for e in picked:
        query = e.question.strip()

        if args.role_mode == "llm":
            decision = decide_role_with_llm(query, model=args.role_model)
        else:
            decision = decide_role(query)

        hits = retrieve(entries, query, role=decision.role, k=args.k)
        retrieved_contexts = [h.text for h in hits]
        reference = _extract_reference_from_kb_text(e.text)

        samples.append(
            {
                "user_input": query,
                "retrieved_contexts": retrieved_contexts,
                "reference": reference,
                "meta": {
                    "role": decision.role,
                    "safety": decision.safety,
                    "reason": decision.reason,
                },
            }
        )

    out_obj = {
        "config": {
            "raw_dir": args.raw_dir,
            "k": args.k,
            "n": len(samples),
            "seed": args.seed,
            "role_mode": args.role_mode,
        },
        "samples": samples,
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

