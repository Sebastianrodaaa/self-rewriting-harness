from __future__ import annotations

import argparse

from critic import CriticMode
from runtime.backends.base import get_backend
from runtime.evolve import run_all_conditions, run_evolution
from runtime.runner import evaluate_tasks
from runtime.tasks import load_tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="Self-rewriting harness CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    ev = sub.add_parser("evolve", help="Run evolution loop")
    ev.add_argument("--generations", type=int, default=8)
    ev.add_argument(
        "--mode",
        choices=[m.value for m in CriticMode],
        default=CriticMode.GATED.value,
    )
    ev.add_argument("--all", action="store_true", help="Run frozen, gated, and ungated")

    ev_plot = sub.add_parser("eval", help="Evaluate current harness once")
    ev_plot.add_argument("--split", choices=["train", "heldout", "both"], default="both")

    args = parser.parse_args()

    if args.cmd == "evolve":
        if args.all:
            paths = run_all_conditions(generations=args.generations)
            for name, path in paths.items():
                print(f"{name}: {path}")
            return
        run_evolution(generations=args.generations, mode=CriticMode(args.mode))
        return

    if args.cmd == "eval":
        backend = get_backend()
        tasks = load_tasks()
        splits = ["train", "heldout"] if args.split == "both" else [args.split]
        result = evaluate_tasks(tasks, backend, splits=splits)
        print(result.to_summary())


if __name__ == "__main__":
    main()
