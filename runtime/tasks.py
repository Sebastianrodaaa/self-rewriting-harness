from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

Split = Literal["train", "heldout"]


@dataclass(frozen=True)
class Task:
    id: str
    split: Split
    prompt: str
    expected: str
    mock_tokens: list[str]
    tags: list[str]
    path: Path


def load_tasks(root: Path | None = None) -> list[Task]:
    root = root or Path(__file__).resolve().parents[1] / "tasks"
    tasks: list[Task] = []
    for split in ("train", "heldout"):
        split_dir = root / split
        if not split_dir.is_dir():
            continue
        for path in sorted(split_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text())
            tasks.append(
                Task(
                    id=data["id"],
                    split=data["split"],
                    prompt=data["prompt"].strip(),
                    expected=data["expected"].strip(),
                    mock_tokens=list(data.get("mock_tokens") or []),
                    tags=list(data.get("tags") or []),
                    path=path,
                )
            )
    return tasks


def tasks_by_split(tasks: list[Task]) -> dict[Split, list[Task]]:
    out: dict[Split, list[Task]] = {"train": [], "heldout": []}
    for t in tasks:
        out[t.split].append(t)
    return out
