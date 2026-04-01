"""
Tests for the model-facing functions in clearspeech_logic.py.

Important:
- These tests do NOT call the real OpenAI API.
- We replace `_call_model()` with fake functions using monkeypatch.
- This keeps tests fast, free, and stable.
"""

import importlib.util
from pathlib import Path

# --- Load clearspeech_logic.py manually from the project root ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGIC_PATH = PROJECT_ROOT / "clearspeech_logic.py"

spec = importlib.util.spec_from_file_location("clearspeech_logic", LOGIC_PATH)
assert spec is not None and spec.loader is not None, (
    f"Could not load module from {LOGIC_PATH}"
)

logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logic)


# -------------------- TESTS --------------------

def test_propose_rewrite_and_question_two_lines(monkeypatch):
    """
    If the model returns 2 lines, the function should split them into:
    - proposal
    - confirmation question
    """

    def fake_call_model(_prompt: str) -> str:
        return "Je ne peux pas venir demain.\nEst-ce que c’est ce que tu veux dire?"

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    proposal, question = logic.propose_rewrite_and_question(
        "je pas venir demain",
        "fr",
    )

    assert proposal == "Je ne peux pas venir demain."
    assert question == "Est-ce que c’est ce que tu veux dire?"


def test_propose_rewrite_and_question_one_line_fallback(monkeypatch):
    """
    If the model returns only one line, the app should add the fixed
    confirmation question automatically.
    """

    def fake_call_model(_prompt: str) -> str:
        return "Ich komme morgen später."

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    proposal, question = logic.propose_rewrite_and_question(
        "morgen später",
        "de",
    )

    assert proposal == "Ich komme morgen später."
    assert question == "Ist das, was du meinst?"


def test_propose_rewrite_and_question_error_fallback(monkeypatch):
    """
    If the model layer returns an ERROR string, the function should pass the
    error back and fall back to the clarification question for the UI language.
    """

    def fake_call_model(_prompt: str) -> str:
        return "ERROR: network problem"

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    proposal, question = logic.propose_rewrite_and_question(
        "test",
        "en",
    )

    assert proposal == "ERROR: network problem"
    assert question == "What do you mean exactly?"


def test_propose_rewrite_after_clarification_two_lines(monkeypatch):
    """
    After clarification, the function should return the new proposal and the
    confirmation question.
    """

    def fake_call_model(_prompt: str) -> str:
        return "I cannot come tomorrow because I have a doctor appointment.\nIs this what you mean?"

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    proposal, question = logic.propose_rewrite_after_clarification(
        "doctor tomorrow",
        "I mean I have a doctor appointment",
        "en",
    )

    assert proposal == "I cannot come tomorrow because I have a doctor appointment."
    assert question == "Is this what you mean?"


def test_propose_three_options_returns_three_distinct_lines(monkeypatch):
    """
    The 3-option feature should return 3 different options.
    """

    def fake_call_model(_prompt: str) -> str:
        return (
            "I went there yesterday and had a problem.\n"
            "I may go there tomorrow and expect a problem.\n"
            "There was a problem there yesterday."
        )

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    options = logic.propose_three_options("I go there yesterday maybe problem", "en")

    assert len(options) == 3
    assert options[0] == "I went there yesterday and had a problem."
    assert options[1] == "I may go there tomorrow and expect a problem."
    assert options[2] == "There was a problem there yesterday."


def test_propose_three_options_deduplicates(monkeypatch):
    """
    If the model repeats the same line, the function should remove duplicates.
    """

    def fake_call_model(_prompt: str) -> str:
        return (
            "Je peux venir demain.\n"
            "Je peux venir demain.\n"
            "Je viendrai peut-être demain.\n"
            "Il est possible que je vienne demain."
        )

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    options = logic.propose_three_options("je come tomorrow maybe", "fr")

    assert "Je peux venir demain." in options
    assert len(options) <= 3


def test_propose_three_options_error(monkeypatch):
    """
    If the model call fails, the function should return a one-item list with the
    error message.
    """

    def fake_call_model(_prompt: str) -> str:
        return "ERROR: api down"

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    options = logic.propose_three_options("test", "en")

    assert options == ["ERROR: api down"]