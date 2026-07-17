"""Async HTTP client for the internal AI gateway (Anthropic Messages API compatible)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Raised when the AI gateway returns an error or times out."""


class LLMClient:
    """Thin wrapper around httpx.AsyncClient for the internal Anthropic-compatible gateway.

    Request format (Anthropic Messages API):
        POST {url}
        Headers: x-api-key, anthropic-version, content-type
        Body:   { model, messages: [{role, content}], max_tokens, temperature }

    Response:
        { content: [{type, text}], ... }
    """

    def __init__(self) -> None:
        self._url = settings.ai_gateway_url
        self._api_key = settings.api_key
        self._model = settings.model
        self._max_tokens = settings.max_tokens
        self._temperature = settings.temperature
        self._timeout = settings.request_timeout
        self._max_retries = settings.max_retries

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
        )

    async def chat(
        self,
        messages: list[dict],
        *,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
    ) -> str:
        """Send a chat request and return the response text.

        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            max_tokens: Override default max_tokens
            temperature: Override default temperature
            system: Optional system prompt (Anthropic system parameter)

        Returns:
            The text content from the first content block.

        Raises:
            LLMClientError: On gateway error, timeout, or empty response.
        """
        body: dict = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens or self._max_tokens,
            "temperature": temperature if temperature is not None else self._temperature,
        }
        if system:
            body["system"] = system

        last_exc: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 2):  # initial + retries
            try:
                response = await self._client.post(self._url, json=body)
                response.raise_for_status()
                data = response.json()

                content_blocks = data.get("content", [])
                if not content_blocks:
                    raise LLMClientError("Empty content in AI gateway response")

                text_parts = [
                    block["text"]
                    for block in content_blocks
                    if block.get("type") == "text" and block.get("text")
                ]
                if not text_parts:
                    raise LLMClientError("No text block found in AI gateway response")

                return text_parts[0]

            except httpx.TimeoutException as exc:
                last_exc = LLMClientError(f"Request timed out after {self._timeout}s")
                logger.warning("LLM request timeout (attempt %d/%d)", attempt, self._max_retries + 1)
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                body_text = exc.response.text[:500]
                last_exc = LLMClientError(f"Gateway returned HTTP {status}: {body_text}")
                logger.warning("LLM HTTP error (attempt %d/%d): %s", attempt, self._max_retries + 1, status)
                # Don't retry 4xx client errors (except 429)
                if 400 <= status < 500 and status != 429:
                    break
            except (httpx.RequestError, json.JSONDecodeError) as exc:
                last_exc = LLMClientError(str(exc))
                logger.warning("LLM request error (attempt %d/%d): %s", attempt, self._max_retries + 1, exc)

            if attempt <= self._max_retries:
                # Exponential backoff
                await asyncio.sleep(1.5 ** attempt)

        raise last_exc or LLMClientError("Unexpected error calling AI gateway")

    async def close(self) -> None:
        await self._client.aclose()


# Module-level singleton
_client_instance: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Return the singleton LLM client."""
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance


async def close_llm_client() -> None:
    """Clean shutdown of the singleton client."""
    global _client_instance
    if _client_instance is not None:
        await _client_instance.close()
        _client_instance = None
