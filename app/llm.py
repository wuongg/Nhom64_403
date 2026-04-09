from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from typing import Any, AsyncIterator

from dotenv import load_dotenv


@dataclass(frozen=True)
class ChatUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class ChatResult:
    text: str
    model: str
    latency_ms: float
    usage: ChatUsage
    cost_usd_estimate: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "latency_ms": round(self.latency_ms, 2),
            "usage": asdict(self.usage),
            "cost_usd_estimate": None
            if self.cost_usd_estimate is None
            else round(self.cost_usd_estimate, 8),
        }


_MODEL_PRICING_PER_1M: dict[str, tuple[float, float]] = {
    # Source: OpenAI API model/pricing docs as of 2026-04-09.
    # Values are (input_usd_per_1m_tokens, output_usd_per_1m_tokens).
    "gpt-4.1": (3.00, 12.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-4o-mini": (0.15, 0.60),
}


def has_openai_key() -> bool:
    load_dotenv(override=False)
    return bool(os.getenv("OPENAI_API_KEY"))


def _normalize_usage(usage: Any) -> ChatUsage:
    if usage is None:
        return ChatUsage(input_tokens=0, output_tokens=0, total_tokens=0)

    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    if prompt_tokens is not None or completion_tokens is not None:
        return ChatUsage(
            input_tokens=int(prompt_tokens or 0),
            output_tokens=int(completion_tokens or 0),
            total_tokens=int(total_tokens or 0),
        )

    input_tokens = getattr(usage, "input_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)
    return ChatUsage(
        input_tokens=int(input_tokens or 0),
        output_tokens=int(output_tokens or 0),
        total_tokens=int(total_tokens or 0),
    )


def _resolve_pricing(model: str) -> tuple[float, float] | None:
    env_in = os.getenv("OPENAI_PRICE_INPUT_PER_1M")
    env_out = os.getenv("OPENAI_PRICE_OUTPUT_PER_1M")
    if env_in and env_out:
        try:
            return float(env_in), float(env_out)
        except ValueError:
            pass
    return _MODEL_PRICING_PER_1M.get(model)


def _estimate_cost_usd(model: str, usage: ChatUsage) -> float | None:
    pricing = _resolve_pricing(model)
    if pricing is None:
        return None
    price_in_per_1m, price_out_per_1m = pricing
    return (
        usage.input_tokens * (price_in_per_1m / 1_000_000.0)
        + usage.output_tokens * (price_out_per_1m / 1_000_000.0)
    )


def chat_openai_with_metrics(
    system: str,
    user: str,
    model: str = "gpt-4o-mini",
    timeout: float = 30.0,
    api_key: str | None = None,
    base_url: str | None = None,
) -> ChatResult:
    """
    Requires:
      - OPENAI_API_KEY env var (or passed api_key)
      - openai>=1.x installed (see requirements.txt)
    """
    from openai import OpenAI  # type: ignore

    load_dotenv(override=False)
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"), base_url=base_url)
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        timeout=timeout,
    )
    latency_ms = (time.perf_counter() - t0) * 1000.0
    usage = _normalize_usage(getattr(resp, "usage", None))
    return ChatResult(
        text=resp.choices[0].message.content or "",
        model=model,
        latency_ms=latency_ms,
        usage=usage,
        cost_usd_estimate=_estimate_cost_usd(model, usage),
    )


def chat_openai(system: str, user: str, model: str = "gpt-4o-mini") -> str:
    return chat_openai_with_metrics(system, user, model=model).text


async def chat_openai_stream_async(
    system: str,
    user: str,
    model: str = "gpt-4o-mini",
    timeout: float = 30.0,
    api_key: str | None = None,
    base_url: str | None = None,
) -> AsyncIterator[str | ChatResult]:
    """
    Async generator for streaming OpenAI responses.
    Yields str chunks while tokens arrive, then yields a final ChatResult
    with full metrics (latency, usage, cost).

    Requires OPENAI_API_KEY env var and openai>=1.26 for stream_options usage.
    """
    from openai import AsyncOpenAI  # type: ignore

    load_dotenv(override=False)
    client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"), base_url=base_url)
    t0 = time.perf_counter()

    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        stream=True,
        stream_options={"include_usage": True},
        timeout=timeout,
    )

    collected: list[str] = []
    usage_obj = None

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            collected.append(text)
            yield text
        # usage arrives on the final empty chunk when include_usage=True
        if getattr(chunk, "usage", None) is not None:
            usage_obj = chunk.usage

    latency_ms = (time.perf_counter() - t0) * 1000.0
    usage = _normalize_usage(usage_obj)
    yield ChatResult(
        text="".join(collected),
        model=model,
        latency_ms=latency_ms,
        usage=usage,
        cost_usd_estimate=_estimate_cost_usd(model, usage),
    )

