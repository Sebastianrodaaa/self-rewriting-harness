from __future__ import annotations

from runtime.backends.base import ModelBackend


class MockBackend(ModelBackend):
    """Deterministic backend for CI — labeled MOCK in all outputs."""

    label = "MOCK"

    def complete(self, system: str, user: str, task_id: str, mock_tokens: list[str]) -> str:
        import re

        haystack = system
        if "TOKEN_HELDOUT_BREAKER" in haystack and any(
            t.startswith("TOKEN_HELDOUT") for t in mock_tokens
        ):
            return "ANSWER: wrong (MOCK — held-out breaker token active)"
        if all(tok in haystack for tok in mock_tokens):
            m = re.search(r"ANSWER:\s*(.+)", user)
            if m:
                return f"ANSWER: {m.group(1).strip()}"
        return "ANSWER: unknown (MOCK — harness missing required tokens)"
