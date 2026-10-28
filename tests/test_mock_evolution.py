import json
from pathlib import Path

import pytest

from critic import CriticMode
from runtime.evolve import run_all_conditions, run_evolution


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parents[1]


def test_mock_gated_improves_heldout(repo_root, monkeypatch):
    monkeypatch.setenv("SRH_BACKEND", "mock")
    monkeypatch.delenv("SRH_PROPOSER_NOISE", raising=False)
    out = repo_root / "results" / "test_evolution_gated.json"
    history = run_evolution(generations=10, mode=CriticMode.GATED, results_path=out)
    assert out.is_file()
    data = json.loads(out.read_text())
    assert data["backend"] == "MOCK"
    final_held = history[-1].heldout_score
    assert final_held > history[0].heldout_score


def test_mock_all_conditions(repo_root, monkeypatch):
    monkeypatch.setenv("SRH_BACKEND", "mock")
    monkeypatch.delenv("SRH_PROPOSER_NOISE", raising=False)
    paths = run_all_conditions(generations=6)
    gated = json.loads(paths["gated"].read_text())
    frozen = json.loads(paths["frozen"].read_text())
    ungated = json.loads(paths["ungated"].read_text())
    assert gated["backend"] == "MOCK"
    g_final = gated["generations"][-1]["heldout_score"]
    f_final = frozen["generations"][-1]["heldout_score"]
    u_final = ungated["generations"][-1]["heldout_score"]
    assert g_final >= f_final
    assert g_final >= u_final
