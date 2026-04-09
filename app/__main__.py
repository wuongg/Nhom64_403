from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from .kb import load_from_raw_folder, retrieve
from .llm import chat_openai, has_openai_key
from .prompting import build_prompt
from .role_llm import decide_role_with_llm
from .role_tree import decide_role


def main() -> int:
    # Load .env (local dev convenience). If OPENAI_API_KEY is already set, keep it.
    load_dotenv(override=False)

    # Windows terminals can default to legacy encodings; force UTF-8 for Vietnamese text output.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(prog="xanhsm-helpcenter-ai")
    parser.add_argument("query", type=str, help="Câu hỏi người dùng")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "raw"),
        help="Đường dẫn folder raw/",
    )
    parser.add_argument("--role", type=str, choices=["user", "driver", "merchant"], default=None)
    parser.add_argument(
        "--role-mode",
        type=str,
        choices=["auto", "llm", "rule"],
        default="auto",
        help="Cách phân loại role: auto (ưu tiên LLM nếu có key) | llm | rule",
    )
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--model", type=str, default="gpt-4.1-mini")
    parser.add_argument("--show-prompt", action="store_true", help="In prompt + KB thay vì gọi LLM")
    args = parser.parse_args()

    entries = load_from_raw_folder(args.raw_dir)

    if args.role_mode == "rule":
        # Still allow rule-based mode as offline fallback
        decision = decide_role(args.query)
    elif args.role_mode == "llm":
        decision = decide_role_with_llm(args.query, model=args.model)
    else:
        if has_openai_key():
            decision = decide_role_with_llm(args.query, model=args.model)
        else:
            decision = decide_role(args.query)

    if args.role:
        decision = type(decision)(
            role=args.role,
            safety=decision.safety,
            driver_type=decision.driver_type,
            reason=f"override role={args.role}; original={decision.reason}",
        )

    hits = retrieve(entries, args.query, role=decision.role, k=args.k)
    prompt = build_prompt(decision, args.query, hits)

    print(json.dumps(prompt.debug, ensure_ascii=False, indent=2))

    if args.show_prompt or not has_openai_key():
        print("\n=== SYSTEM ===\n")
        print(prompt.system)
        print("\n=== USER ===\n")
        print(prompt.user)
        if not has_openai_key():
            print("\n[info] OPENAI_API_KEY chưa được set -> đang chạy chế độ preview prompt.")
        return 0

    answer = chat_openai(prompt.system, prompt.user, model=args.model)
    print("\n=== ANSWER ===\n")
    print(answer.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

