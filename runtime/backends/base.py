from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Literal

BackendKind = Literal["mock", "openai", "anthropic"]


class ModelBackend(ABC):
    label: str

    @abstractmethod
    def complete(self, system: str, user: str, task_id: str, mock_tokens: list[str]) -> str:
        raise NotImplementedError


def get_backend(kind: str | None = None) -> ModelBackend:
    kind = (kind or os.environ.get("SRH_BACKEND", "mock")).lower()
    if kind == "mock":
        from runtime.backends.mock import MockBackend

        return MockBackend()
    if kind in ("openai", "openai_compat"):
        from runtime.backends.openai_compat import OpenAICompatBackend

        return OpenAICompatBackend()
    if kind == "anthropic":
        from runtime.backends.anthropic_backend import AnthropicBackend

        return AnthropicBackend()
    raise ValueError(f"Unknown backend: {kind}")
