from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from critic import Critic, CriticMode
from proposer import Proposer
from runtime.backends.base import get_backend
from runtime.git_harness import ensure_git_repo
from runtime.harness_loader import load_harness
from runtime.runner import evaluate_tasks
from runtime.tasks import load_tasks
from runtime.traces import utc_now_iso


@dataclass
class GenerationMetrics:
    generation: int
    train_score: float
    heldout_score: float
    accepted: bool
    edit_summary: str
    backend: str


def _reset_harness(dest: Path, seed: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(seed, dest, ignore=shutil.ignore_patterns(".git"))


def run_evolution(
    *,
    generations: int = 8,
    mode: CriticMode = CriticMode.GATED,
    results_path: Path | None = None,
    seed_harness: Path | None = None,
) -> list[GenerationMetrics]:
    repo_root = Path(__file__).resolve().parents[1]
    seed = seed_harness or repo_root / "harness"
    work = repo_root / "results" / ".work" / mode.value
    _reset_harness(work, seed)
    ensure_git_repo(work)

    backend = get_backend()
    tasks = load_tasks()
    proposer = Proposer(harness_root=work, backend=backend)
    critic = Critic(harness_root=work, tasks=tasks, backend=backend, mode=mode)

    if mode == CriticMode.UNGATED:
        os.environ["SRH_PROPOSER_NOISE"] = "1"

    history: list[GenerationMetrics] = []

    for gen in range(generations):
        harness = load_harness(work)
        eval_all = evaluate_tasks(tasks, backend, harness=harness)
        train_score = eval_all.split_scores.get("train", 0.0)
        heldout_score = eval_all.split_scores.get("heldout", 0.0)

        if mode == CriticMode.FROZEN:
            history.append(
                GenerationMetrics(
                    generation=gen,
                    train_score=train_score,
                    heldout_score=heldout_score,
                    accepted=False,
                    edit_summary="(frozen)",
                    backend=backend.label,
                )
            )
            continue

        failures = [f for f in eval_all.failures if f.split == "train"]
        if not failures:
            failures = [f for f in eval_all.failures if f.split == "heldout"]
        if not failures:
            history.append(
                GenerationMetrics(
                    generation=gen,
                    train_score=train_score,
                    heldout_score=heldout_score,
                    accepted=False,
                    edit_summary="no train failures",
                    backend=backend.label,
                )
            )
            continue

        failure = failures[0]
        edit = proposer.propose(failure, gen)
        decision = critic.review(edit, gen)

        harness = load_harness(work)
        eval_after = evaluate_tasks(tasks, backend, harness=harness)
        history.append(
            GenerationMetrics(
                generation=gen,
                train_score=eval_after.split_scores.get("train", train_score),
                heldout_score=eval_after.split_scores.get("heldout", heldout_score),
                accepted=decision.accepted,
                edit_summary=edit.summary,
                backend=backend.label,
            )
        )

    out = results_path or repo_root / "results" / f"evolution_{mode.value}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    label_note = (
        "MOCK results — set SRH_BACKEND and API keys for real runs"
        if backend.label == "MOCK"
        else "live backend"
    )
    payload = {
        "backend": backend.label,
        "mode": mode.value,
        "label_note": label_note,
        "generated_at": utc_now_iso(),
        "generations": [asdict(g) for g in history],
    }
    out.write_text(json.dumps(payload, indent=2))
    return history


def run_all_conditions(generations: int = 8) -> dict[str, Path]:
    paths = {}
    for mode in (CriticMode.FROZEN, CriticMode.GATED, CriticMode.UNGATED):
        path = Path(__file__).resolve().parents[1] / "results" / f"evolution_{mode.value}.json"
        run_evolution(generations=generations, mode=mode, results_path=path)
        paths[mode.value] = path
    return paths
