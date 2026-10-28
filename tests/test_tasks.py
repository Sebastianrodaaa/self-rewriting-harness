from pathlib import Path

from runtime.tasks import load_tasks


def test_task_counts():
    tasks = load_tasks(Path(__file__).resolve().parents[1] / "tasks")
    train = [t for t in tasks if t.split == "train"]
    held = [t for t in tasks if t.split == "heldout"]
    assert len(train) >= 5
    assert len(held) >= 5


def test_skill_library_size():
    skills = Path(__file__).resolve().parents[1] / "harness" / "skills"
    dirs = [p for p in skills.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()]
    assert len(dirs) >= 50
