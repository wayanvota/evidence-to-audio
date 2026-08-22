from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Protocol

from .config import ProviderSettings


class ProviderError(RuntimeError):
    """Raised when a model provider cannot return a usable response."""


class TextProvider(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class OpenAICompatibleProvider:
    """Minimal client for OpenAI-compatible chat-completions endpoints."""

    def __init__(self, settings: ProviderSettings):
        self.settings = settings

    def complete(self, system: str, user: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.settings.api_key_env:
            key = os.getenv(self.settings.api_key_env, "")
            if not key:
                raise ProviderError(
                    f"Environment variable {self.settings.api_key_env} is required "
                    f"for provider {self.settings.name}"
                )
            headers["Authorization"] = f"Bearer {key}"

        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": self.settings.max_output_tokens,
        }
        request = urllib.request.Request(
            f"{self.settings.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise ProviderError(f"Provider returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ProviderError(f"Provider request failed: {exc}") from exc

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Provider response did not contain message text") from exc
        if isinstance(content, list):
            content = "\n".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        text = str(content).strip()
        if not text:
            raise ProviderError("Provider returned empty text")
        return text


def build_provider(settings: ProviderSettings) -> TextProvider:
    if settings.kind == "openai_compatible":
        return OpenAICompatibleProvider(settings)
    raise ProviderError(f"Unsupported provider kind: {settings.kind}")
