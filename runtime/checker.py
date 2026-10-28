from __future__ import annotations

import re


def extract_answer_line(text: str) -> str | None:
    for line in text.strip().splitlines():
        line = line.strip()
        if line.startswith("ANSWER:"):
            return line
    m = re.search(r"(?m)^ANSWER:\s*(.+)$", text)
    if m:
        return f"ANSWER: {m.group(1).strip()}"
    return None


def check_response(expected: str, response: str) -> tuple[bool, str]:
    got = extract_answer_line(response)
    if got is None:
        return False, "missing ANSWER: line"
    exp = expected.strip()
    if got.strip() == exp:
        return True, "ok"
    return False, f"expected {exp!r}, got {got.strip()!r}"
