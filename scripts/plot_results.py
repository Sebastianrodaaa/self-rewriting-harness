from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


def load_series(path: Path) -> tuple[list[int], list[float], str]:
    data = json.loads(path.read_text())
    gens = [g["generation"] for g in data["generations"]]
    held = [g["heldout_score"] for g in data["generations"]]
    backend = data.get("backend", "?")
    data.get("label_note", "")
    label = f"{path.stem} ({backend})"
    if backend == "MOCK":
        label = f"{label} [MOCK]"
    return gens, held, label


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    results = root / "results"
    files = {
        "frozen": results / "evolution_frozen.json",
        "gated (evolved)": results / "evolution_gated.json",
        "ungated": results / "evolution_ungated.json",
    }
    plt.figure(figsize=(8, 4.5))
    for name, path in files.items():
        if not path.is_file():
            continue
        xs, ys, _ = load_series(path)
        plt.plot(xs, ys, marker="o", label=name)

    plt.xlabel("Generation")
    plt.ylabel("Held-out score")
    plt.title("Held-out score across generations")
    plt.ylim(-0.05, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()
    out = results / "heldout_generations.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out, dpi=144)
    print(out)


if __name__ == "__main__":
    main()
