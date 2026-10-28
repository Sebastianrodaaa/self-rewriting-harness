from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from proposer import HarnessEdit, apply_edit
from runtime.backends.base import ModelBackend
from runtime.git_harness import (
    commit_harness,
    log_acceptance,
    log_rejection,
    rollback_harness,
)
from runtime.harness_loader import load_harness
from runtime.runner import evaluate_tasks
from runtime.tasks import Task, load_tasks


class CriticMode(str, Enum):
    GATED = "gated"
    UNGATED = "ungated"
    FROZEN = "frozen"


@dataclass
class CriticDecision:
    accepted: bool
    heldout_before: float
    heldout_after: float
    commit: str | None
    reason: str


class Critic:
    def __init__(
        self,
        *,
        harness_root: Path | None = None,
        tasks: list[Task] | None = None,
        backend: ModelBackend,
        mode: CriticMode = CriticMode.GATED,
        log_path: Path | None = None,
    ) -> None:
        self.harness_root = harness_root or Path(__file__).resolve().parent / "harness"
        self.tasks = tasks or load_tasks()
        self.backend = backend
        self.mode = mode
        self.log_path = log_path or self.harness_root / "revision_log.jsonl"

    def evaluate_heldout(self) -> float:
        result = evaluate_tasks(
            self.tasks,
            self.backend,
            harness=load_harness(self.harness_root),
            splits=["heldout"],
        )
        return result.split_scores.get("heldout", 0.0)

    def review(self, edit: HarnessEdit, generation: int) -> CriticDecision:
        if self.mode == CriticMode.FROZEN:
            return CriticDecision(
                accepted=False,
                heldout_before=self.evaluate_heldout(),
                heldout_after=self.evaluate_heldout(),
                commit=None,
                reason="frozen baseline — edits disabled",
            )

        before = self.evaluate_heldout()
        apply_edit(self.harness_root, edit)
        after = self.evaluate_heldout()

        if self.mode == CriticMode.UNGATED:
            commit = commit_harness(self.harness_root, f"gen {generation}: {edit.summary} (ungated)")
            log_acceptance(
                self.log_path,
                generation=generation,
                edit_summary=edit.summary,
                commit=commit or "noop",
                heldout_score=after,
            )
            return CriticDecision(
                accepted=True,
                heldout_before=before,
                heldout_after=after,
                commit=commit,
                reason="ungated accept",
            )

        # Gated: accept only if held-out does not regress
        if after + 1e-9 >= before:
            commit = commit_harness(self.harness_root, f"gen {generation}: {edit.summary}")
            log_acceptance(
                self.log_path,
                generation=generation,
                edit_summary=edit.summary,
                commit=commit or "noop",
                heldout_score=after,
            )
            return CriticDecision(
                accepted=True,
                heldout_before=before,
                heldout_after=after,
                commit=commit,
                reason="held-out improved or tied",
            )

        rollback_harness(self.harness_root)
        log_rejection(
            self.log_path,
            generation=generation,
            edit_summary=edit.summary,
            heldout_before=before,
            heldout_after=after,
            reason="held-out regression",
        )
        return CriticDecision(
            accepted=False,
            heldout_before=before,
            heldout_after=after,
            commit=None,
            reason="held-out regression — rolled back",
        )
