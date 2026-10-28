"""Render a terminal-style demo GIF from a short gated evolution run (MOCK)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def run_demo_log() -> list[str]:
    env = {**os.environ, "SRH_BACKEND": "mock", "PYTHONUNBUFFERED": "1"}
    env.pop("SRH_PROPOSER_NOISE", None)
    root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        "-c",
        """
from pathlib import Path
from critic import CriticMode
from runtime.backends.base import get_backend
from runtime.evolve import run_evolution
from runtime.harness_loader import load_harness
from runtime.runner import evaluate_tasks
from runtime.tasks import load_tasks
from proposer import Proposer
from critic import Critic

work = Path('results/.work/demo_gif')
import shutil
seed = Path('harness')
if work.exists():
    shutil.rmtree(work)
shutil.copytree(seed, work, ignore=shutil.ignore_patterns('.git'))

backend = get_backend()
tasks = load_tasks()
proposer = Proposer(work, backend)
critic = Critic(harness_root=work, tasks=tasks, backend=backend, mode=CriticMode.GATED)

print('=== self-rewriting-harness demo (MOCK backend) ===')
for gen in range(6):
    ev = evaluate_tasks(tasks, backend, harness=load_harness(work))
    fail = [f for f in ev.failures if f.split=='train'] or [f for f in ev.failures if f.split=='heldout']
    if not fail:
        print(f'gen {gen}: train={ev.split_scores.get(\"train\",0):.2f} heldout={ev.split_scores.get(\"heldout\",0):.2f} (done)')
        break
    edit = proposer.propose(fail[0], gen)
    before = critic.evaluate_heldout()
    decision = critic.review(edit, gen)
    ev2 = evaluate_tasks(tasks, backend, harness=load_harness(work))
    status = 'ACCEPT' if decision.accepted else 'ROLLBACK'
    print(f'gen {gen}: propose {edit.summary!r} -> {status} heldout {before:.2f}->{decision.heldout_after:.2f}')
    print(f'         scores train={ev2.split_scores.get(\"train\",0):.2f} heldout={ev2.split_scores.get(\"heldout\",0):.2f}')
print('=== end demo ===')
""",
    ]
    proc = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, check=False)
    lines = (proc.stdout + proc.stderr).splitlines()
    return lines or ["(no output)"]


def render_gif(lines: list[str], out: Path, fps: int = 2) -> None:
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    width, height = 900, 520
    bg = (12, 16, 24)
    fg = (210, 230, 210)
    accent = (120, 200, 255)

    frames: list[Image.Image] = []
    visible: list[str] = []
    for line in lines:
        visible.append(line)
        if len(visible) > 22:
            visible = visible[-22:]
        img = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(img)
        draw.text((12, 8), "self-rewriting-harness — terminal demo [MOCK]", fill=accent, font=font)
        y = 36
        for row in visible:
            color = fg
            if "ACCEPT" in row:
                color = (130, 255, 160)
            if "ROLLBACK" in row:
                color = (255, 140, 130)
            draw.text((12, y), row[:105], fill=color, font=font)
            y += 20
        frames.append(img)

    out.parent.mkdir(parents=True, exist_ok=True)
    duration = int(1000 / fps)
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=True,
    )


def main() -> None:
    lines = run_demo_log()
    out = Path(__file__).resolve().parents[1] / "docs" / "demo.gif"
    render_gif(lines, out)
    print(out)


if __name__ == "__main__":
    main()
