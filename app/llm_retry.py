from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import AsyncIterator, Any

from .llm import ChatResult, chat_openai_with_metrics, chat_openai_stream_async
from openai import RateLimitError, APITimeoutError, APIConnectionError, InternalServerError

logger = logging.getLogger(__name__)

def is_retryable(exc: Exception) -> bool:
    """True if the exception is a transient error that should be retried."""
    if isinstance(exc, (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)):
        return True
    # Check for generic API errors with status >= 500 if available
    status_code = getattr(exc, "status_code", None)
    if status_code and isinstance(status_code, int) and status_code >= 500:
        return True
    return False

@dataclass(frozen=True, slots=True)
class RetryAttempt:
    attempt: int          # 0-indexed
    model_used: str
    error: str | None = None
    delay_before: float = 0.0

@dataclass(frozen=True, slots=True)
class LLMCallResult:
    result: ChatResult | None
    attempts: list[RetryAttempt]
    used_fallback: bool
    final_error: str | None = None

def _get_api_params(model: str, openrouter_key: str | None) -> dict[str, Any]:
    """Helper to return api_key and base_url if model is from OpenRouter."""
    # OpenRouter models often contain '/' or ':'
    if ":" in model or "/" in model:
        return {
            "api_key": openrouter_key,
            "base_url": "https://openrouter.ai/api/v1"
        }
    return {}

def chat_with_retry(
    system: str,
    user: str,
    *,
    primary_model: str,
    fallback_model: str | None = None,
    max_retries: int = 2,
    base_delay: float = 1.0,
    timeout: float = 30.0,
    openrouter_key: str | None = None,
) -> LLMCallResult:
    """Synchronous chat with retry and fallback logic."""
    attempts: list[RetryAttempt] = []
    
    for i in range(max_retries + 1):
        # Default to primary, but use fallback on last attempt if provided
        model = primary_model
        used_fallback = False
        if i == max_retries and fallback_model:
            model = fallback_model
            used_fallback = True
            
        delay = 0.0
        if i > 0:
            delay = base_delay * (2 ** (i - 1)) + random.uniform(0, 0.5)
            time.sleep(delay)
            
        api_params = _get_api_params(model, openrouter_key)
        
        try:
            result = chat_openai_with_metrics(
                system, user, model=model, timeout=timeout, **api_params
            )
            attempts.append(RetryAttempt(attempt=i, model_used=model, delay_before=delay))
            return LLMCallResult(result=result, attempts=attempts, used_fallback=used_fallback)
        except Exception as e:
            attempts.append(RetryAttempt(attempt=i, model_used=model, error=str(e), delay_before=delay))
            if not is_retryable(e) or i == max_retries:
                return LLMCallResult(result=None, attempts=attempts, used_fallback=used_fallback, final_error=str(e))
            logger.warning(f"LLM call failed (attempt {i+1}/{max_retries+1}): {e}. Retrying model {model}...")

    return LLMCallResult(result=None, attempts=attempts, used_fallback=False, final_error="Max retries reached")

async def chat_with_retry_stream(
    system: str,
    user: str,
    *,
    primary_model: str,
    fallback_model: str | None = None,
    max_retries: int = 2,
    base_delay: float = 1.0,
    timeout: float = 30.0,
    openrouter_key: str | None = None,
) -> AsyncIterator[str | ChatResult | RetryAttempt]:
    """
    Async generator for streaming chat with retry and fallback logic.
    Yields:
      - str: text chunks
      - RetryAttempt: when a retry is about to happen
      - ChatResult: the final result with metrics
    """
    attempts_count = 0
    
    while attempts_count <= max_retries:
        model = primary_model
        used_fallback = False
        if attempts_count == max_retries and fallback_model:
            model = fallback_model
            used_fallback = True
            
        if attempts_count > 0:
            delay = base_delay * (2 ** (attempts_count - 1)) + random.uniform(0, 0.5)
            # Notify caller about retry if they want to handle it
            yield RetryAttempt(attempt=attempts_count, model_used=model, delay_before=delay)
            await asyncio.sleep(delay)
            
        api_params = _get_api_params(model, openrouter_key)
        
        try:
            stream = chat_openai_stream_async(
                system, user, model=model, timeout=timeout, **api_params
            )
            async for chunk in stream:
                yield chunk
            # Success!
            return 
        except Exception as e:
            if not is_retryable(e) or attempts_count == max_retries:
                logger.error(f"Stream failed permanently: {e}")
                # We raise here to let the caller handle the final failure
                raise e
            
            attempts_count += 1
            logger.warning(f"Stream failed (attempt {attempts_count}): {e}. Retrying model {model}...")
