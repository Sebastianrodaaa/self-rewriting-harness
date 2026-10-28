from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from runtime.backends.base import ModelBackend, get_backend
from runtime.harness_loader import load_harness
from runtime.traces import FailureTrace


@dataclass
class HarnessEdit:
    summary: str
    system_prompt_append: str = ""
    skill_id: str | None = None
    skill_append: str = ""
    noise_token: str | None = None


class Proposer:
    """Proposes minimal harness edits from failure traces."""

    def __init__(self, harness_root: Path | None = None, backend: ModelBackend | None = None) -> None:
        self.harness_root = harness_root or Path(__file__).resolve().parent / "harness"
        self.backend = backend or get_backend()

    def propose(self, failure: FailureTrace, generation: int) -> HarnessEdit:
        if self.backend.label == "MOCK":
            return self._propose_mock(failure, generation)
        return self._propose_llm(failure)

    def _propose_mock(self, failure: FailureTrace, generation: int) -> HarnessEdit:
        token = failure.mock_tokens[0] if failure.mock_tokens else f"TOKEN_{failure.task_id.upper()}"
        bundle = load_harness(self.harness_root)
        append = ""
        if failure.split == "train" and token not in bundle.combined_text():
            append = f"\n# mock harness token for {failure.task_id}\n{token}\n"

        # Ungated ablation path adds a held-out-breaking noise token on odd generations.
        noise = None
        if os.environ.get("SRH_PROPOSER_NOISE") == "1" and generation % 2 == 1:
            noise = "TOKEN_HELDOUT_BREAKER"

        # When train tokens are present, propose general held-out tokens via skill patch.
        skill_id = None
        skill_append = ""
        if not append and failure.split in ("train", "heldout"):
            heldout_map = {
                "TOKEN_HELDOUT_MATH": ("tdd", "\n<!-- enables held-out math tasks -->\nTOKEN_HELDOUT_MATH\n"),
                "TOKEN_HELDOUT_ENCODING": (
                    "error-handling",
                    "\n<!-- encoding -->\nTOKEN_HELDOUT_ENCODING\n",
                ),
                "TOKEN_HELDOUT_LOGIC": (
                    "research",
                    "\n<!-- logic -->\nTOKEN_HELDOUT_LOGIC\n",
                ),
                "TOKEN_HELDOUT_REGEX": (
                    "code-review",
                    "\n<!-- regex -->\nTOKEN_HELDOUT_REGEX\n",
                ),
            }
            for tok, (sid, frag) in heldout_map.items():
                if tok not in bundle.combined_text():
                    if failure.split == "heldout" and tok not in failure.mock_tokens:
                        continue
                    skill_id = sid
                    skill_append = frag
                    break
            if failure.split == "heldout" and not skill_id:
                missing = [t for t in failure.mock_tokens if t not in bundle.combined_text()]
                if missing:
                    append = f"\n# held-out token for {failure.task_id}\n{missing[0]}\n"

        summary = f"Add token for {failure.task_id}"
        if skill_id:
            summary = f"Patch skill {skill_id} with held-out token"
        if noise:
            summary += " (+ noise ablation)"

        return HarnessEdit(
            summary=summary,
            system_prompt_append=append,
            skill_id=skill_id,
            skill_append=skill_append,
            noise_token=noise,
        )

    def _propose_llm(self, failure: FailureTrace) -> HarnessEdit:
        system = (
            "You propose minimal edits to an agent harness (system prompt + skills) "
            "to fix the failure. Respond with JSON: "
            '{"summary":"...", "system_prompt_append":"...", "skill_id":null|"name", "skill_append":"..."}'
        )
        user = (
            f"Task id: {failure.task_id}\n"
            f"Expected: {failure.expected}\n"
            f"Got: {failure.response}\n"
            f"Reason: {failure.reason}\n"
            f"Prompt excerpt:\n{failure.prompt[:500]}\n"
        )
        raw = self.backend.complete(system, user, failure.task_id, [])
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return HarnessEdit(
                summary="fallback append",
                system_prompt_append=f"\n# fix {failure.task_id}\nHint: {failure.expected}\n",
            )
        import json

        data = json.loads(m.group(0))
        return HarnessEdit(
            summary=str(data.get("summary", "llm edit")),
            system_prompt_append=str(data.get("system_prompt_append") or ""),
            skill_id=data.get("skill_id"),
            skill_append=str(data.get("skill_append") or ""),
        )


def apply_edit(harness_root: Path, edit: HarnessEdit) -> None:
    sys_path = harness_root / "SYSTEM_PROMPT.md"
    text = sys_path.read_text()
    if edit.system_prompt_append and edit.system_prompt_append.strip() not in text:
        sys_path.write_text(text.rstrip() + edit.system_prompt_append)

    if edit.noise_token and edit.noise_token not in text:
        sys_path.write_text(sys_path.read_text().rstrip() + f"\n{edit.noise_token}\n")

    if edit.skill_id and edit.skill_append:
        skill_path = harness_root / "skills" / edit.skill_id / "SKILL.md"
        if skill_path.is_file():
            st = skill_path.read_text()
            if edit.skill_append.strip() not in st:
                skill_path.write_text(st.rstrip() + edit.skill_append)
