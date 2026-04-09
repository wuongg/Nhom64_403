from __future__ import annotations

import os


def has_openai_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def chat_openai(system: str, user: str, model: str = "gpt-4.1-mini") -> str:
    """
    Requires:
      - OPENAI_API_KEY env var
      - openai>=1.x installed (see requirements.txt)
    """
    from openai import OpenAI  # type: ignore

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""

