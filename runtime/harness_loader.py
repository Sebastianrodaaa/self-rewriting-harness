from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class HarnessBundle:
    root: Path
    system_prompt: str
    checks_yaml: str
    skill_text: str

    def combined_text(self) -> str:
        return f"{self.system_prompt}\n{self.checks_yaml}\n{self.skill_text}"

    def skill_ids(self) -> list[str]:
        skills_dir = self.root / "skills"
        if not skills_dir.is_dir():
            return []
        return sorted(
            p.name
            for p in skills_dir.iterdir()
            if p.is_dir() and (p / "SKILL.md").is_file()
        )


def load_harness(root: Path | None = None) -> HarnessBundle:
    root = root or Path(__file__).resolve().parents[1] / "harness"
    system_path = root / "SYSTEM_PROMPT.md"
    checks_path = root / "checks.yaml"
    system_prompt = system_path.read_text() if system_path.is_file() else ""
    checks_yaml = checks_path.read_text() if checks_path.is_file() else ""

    chunks: list[str] = []
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(skills_dir.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if skill_dir.is_dir() and skill_md.is_file():
                chunks.append(skill_md.read_text())

    return HarnessBundle(
        root=root,
        system_prompt=system_prompt,
        checks_yaml=checks_yaml,
        skill_text="\n\n".join(chunks),
    )
