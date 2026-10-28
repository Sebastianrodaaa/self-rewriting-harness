from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class FailureTrace:
    task_id: str
    split: str
    prompt: str
    response: str
    expected: str
    reason: str
    mock_tokens: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TaskRunRecord:
    task_id: str
    split: str
    passed: bool
    response: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
