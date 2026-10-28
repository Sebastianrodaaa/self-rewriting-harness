from __future__ import annotations

import subprocess
from pathlib import Path

from runtime.traces import append_jsonl, utc_now_iso


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def ensure_git_repo(harness_root: Path) -> None:
    if (harness_root / ".git").is_dir():
        return
    _run(["git", "init"], harness_root)
    _run(["git", "add", "-A"], harness_root)
    _run(["git", "commit", "-m", "Initial harness seed"], harness_root)


def commit_harness(harness_root: Path, message: str) -> str | None:
    ensure_git_repo(harness_root)
    _run(["git", "add", "-A"], harness_root)
    st = _run(["git", "status", "--porcelain"], harness_root)
    if not st.stdout.strip():
        return None
    _run(["git", "commit", "-m", message], harness_root)
    rev = _run(["git", "rev-parse", "--short", "HEAD"], harness_root)
    return rev.stdout.strip()


def rollback_harness(harness_root: Path) -> None:
    _run(["git", "checkout", "--", "."], harness_root)


def log_rejection(
    log_path: Path,
    *,
    generation: int,
    edit_summary: str,
    heldout_before: float,
    heldout_after: float,
    reason: str,
) -> None:
    append_jsonl(
        log_path,
        {
            "ts": utc_now_iso(),
            "generation": generation,
            "status": "rejected",
            "edit": edit_summary,
            "heldout_before": heldout_before,
            "heldout_after": heldout_after,
            "reason": reason,
        },
    )


def log_acceptance(
    log_path: Path,
    *,
    generation: int,
    edit_summary: str,
    commit: str,
    heldout_score: float,
) -> None:
    append_jsonl(
        log_path,
        {
            "ts": utc_now_iso(),
            "generation": generation,
            "status": "accepted",
            "edit": edit_summary,
            "commit": commit,
            "heldout_score": heldout_score,
        },
    )
