"""Tests for normalizing model output lines (list markers)."""

import importlib.util
from pathlib import Path

# --- Load clearspeech_logic.py manually (robust fix for pytest path issues) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGIC_PATH = PROJECT_ROOT / "clearspeech_logic.py"

spec = importlib.util.spec_from_file_location("clearspeech_logic", LOGIC_PATH)
assert spec is not None and spec.loader is not None, (
    f"Could not load module from {LOGIC_PATH}"
)
logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logic)

# -------------------- TESTS --------------------

def _strip_list_markers(raw: str) -> list[str]:
    # Keep sentence punctuation such as the final period.
    # Only remove common list markers at the beginning of a line.
    lines = []
    for raw_line in raw.splitlines():
        if not raw_line.strip():
            continue
        line = raw_line.lstrip()

        # Remove a leading bullet if present.
        if line.startswith("-") or line.startswith("•"):
            line = line[1:].lstrip()

        # Remove a leading numeric list marker like "1. " or "2) ".
        idx = 0
        while idx < len(line) and line[idx].isdigit():
            idx += 1
        if idx > 0 and idx < len(line) and line[idx] in ".)":
            line = line[idx + 1 :].lstrip()

        lines.append(line)
    return lines


def test_strip_list_markers_removes_bullets_and_numeric_prefixes():
    raw = "- First sentence.\n2) Second sentence."
    assert _strip_list_markers(raw) == ["First sentence.", "Second sentence."]
def test_output_language_matches_input(monkeypatch):
    """If user writes in French, output should also be French."""

    def fake_call_model(_prompt: str) -> str:
        return "Je viens demain.\nEst-ce que c’est ce que tu veux dire?"

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    proposal, question = logic.propose_rewrite_and_question(
        "je viens demain",
        "fr",
    )

    assert "Je viens" in proposal
    assert "Est-ce" in question


def test_language_hint_in_prompt(monkeypatch):
    """Make sure we send the language to the model."""

    seen = {}

    def fake_call_model(prompt: str) -> str:
        seen["prompt"] = prompt
        return "Test.\nIs this what you mean?"

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    logic.propose_rewrite_and_question("test", "en")

    assert "Language hint: en" in seen["prompt"]