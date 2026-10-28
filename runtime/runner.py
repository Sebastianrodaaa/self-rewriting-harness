from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from runtime.backends.base import ModelBackend
from runtime.checker import check_response
from runtime.harness_loader import HarnessBundle, load_harness
from runtime.tasks import Split, Task, load_tasks
from runtime.traces import FailureTrace, TaskRunRecord


@dataclass
class EvalResult:
    backend_label: str
    records: list[TaskRunRecord]
    failures: list[FailureTrace]
    score: float
    split_scores: dict[Split, float]

    def to_summary(self) -> dict:
        return {
            "backend": self.backend_label,
            "score": self.score,
            "split_scores": self.split_scores,
            "passed": sum(1 for r in self.records if r.passed),
            "total": len(self.records),
        }


def _build_system(bundle: HarnessBundle, max_skill_chars: int = 2_000_000) -> str:
    skills = bundle.skill_text[:max_skill_chars]
    return (
        f"{bundle.system_prompt.strip()}\n\n"
        f"--- checks ---\n{bundle.checks_yaml.strip()}\n\n"
        f"--- skills (truncated) ---\n{skills}"
    )


def evaluate_tasks(
    tasks: list[Task],
    backend: ModelBackend,
    harness: HarnessBundle | None = None,
    splits: list[Split] | None = None,
) -> EvalResult:
    harness = harness or load_harness()
    system = _build_system(harness)
    splits = splits or ["train", "heldout"]
    selected = [t for t in tasks if t.split in splits]

    records: list[TaskRunRecord] = []
    failures: list[FailureTrace] = []

    for task in selected:
        response = backend.complete(system, task.prompt, task.id, task.mock_tokens)
        ok, reason = check_response(task.expected, response)
        records.append(
            TaskRunRecord(
                task_id=task.id,
                split=task.split,
                passed=ok,
                response=response,
                reason=reason,
            )
        )
        if not ok:
            failures.append(
                FailureTrace(
                    task_id=task.id,
                    split=task.split,
                    prompt=task.prompt,
                    response=response,
                    expected=task.expected,
                    reason=reason,
                    mock_tokens=task.mock_tokens,
                )
            )

    def split_score(split: Split) -> float:
        subset = [r for r in records if r.split == split]
        if not subset:
            return 0.0
        return sum(1 for r in subset if r.passed) / len(subset)

    split_scores = {s: split_score(s) for s in splits}
    overall = sum(1 for r in records if r.passed) / len(records) if records else 0.0
    return EvalResult(
        backend_label=backend.label,
        records=records,
        failures=failures,
        score=overall,
        split_scores=split_scores,
    )


def load_all_tasks(tasks_root: Path | None = None) -> list[Task]:
    return load_tasks(tasks_root)
