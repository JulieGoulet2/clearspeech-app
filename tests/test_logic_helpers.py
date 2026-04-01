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


def test_dominant_language_english_not_mistaken_for_german():
    """German cues must not use English homographs (die, bin) or tie-break to de."""
    assert (
        logic._dominant_language_code("I might die tomorrow and put it in the bin.", "de")
        == "en"
    )
    assert (
        logic._dominant_language_code("The doctor said tomorrow.", "de") == "en"
    )
    assert logic._dominant_language_code("Ich kann morgen nicht zum Arzt.", "en") == "de"


def test_option_meanings_too_close_detects_paraphrase_and_same_scaffold():
    """Paraphrases and same long opening must not count as 3 distinct meanings."""
    a = (
        "Ich habe noch nicht entschieden, wo dein Chor probt, weil ich nicht gut gelesen habe."
    )
    b = (
        "Ich habe noch nicht entschieden, wo dein Chor probt, ich habe nicht gut gelesen."
    )
    c = "Ich habe noch nicht entschieden, wo deine Chorprobe ist."
    assert logic._option_meanings_too_close(a, b)
    assert logic._option_meanings_too_close(a, c)
    assert not logic._option_meanings_too_close(
        "Der Termin ist morgen um acht.",
        "Sie wollten wissen, ob der Zug pünktlich ist.",
    )


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

    # Category call, then one response per option; retry may run if lines look too similar.
    multiline = (
        "I went there yesterday and had a problem.\n"
        "I may go there tomorrow and expect a problem.\n"
        "There was a problem there yesterday."
    )
    responses = iter(
        [
            '["location", "time", "understanding"]',
            "Alpha: only the first line matters for this test.",
            "Bravo: distinct tokens reduce overlap with other options.",
            "Charlie: third option must not dedupe against the first two.",
        ]
    )

    def fake_call_model(_prompt: str) -> str:
        try:
            return next(responses)
        except StopIteration:
            return multiline

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    options = logic.propose_three_options("I go there yesterday maybe problem", "en")

    assert len(options) == 3
    assert options[0] == "Alpha: only the first line matters for this test."
    assert options[1] == "Bravo: distinct tokens reduce overlap with other options."
    assert options[2] == "Charlie: third option must not dedupe against the first two."


def test_propose_three_options_deduplicates(monkeypatch):
    """
    If the model repeats the same line, the function should remove duplicates.
    """

    multiline = (
        "Je peux venir demain.\n"
        "Je peux venir demain.\n"
        "Je viendrai peut-être demain.\n"
        "Il est possible que je vienne demain."
    )
    call_idx = [0]

    def fake_call_model(_prompt: str) -> str:
        i = call_idx[0]
        call_idx[0] += 1
        if i == 0:
            return '["location", "time", "understanding"]'
        return multiline

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    options = logic.propose_three_options("je come tomorrow maybe", "fr")

    assert "Je peux venir demain." in options
    assert len(options) <= 3


def test_propose_three_options_german_input_english_ui_uses_german(monkeypatch):
    """Reply language must follow the message, not the Streamlit UI language."""
    prompts: list[str] = []
    responses = iter(
        [
            '["location", "time", "decision"]',
            "Erster deutscher Satz.",
            "Zweiter deutscher Satz.",
            "Dritter deutscher Satz.",
        ]
    )

    def fake_call_model(prompt: str) -> str:
        prompts.append(prompt)
        try:
            return next(responses)
        except StopIteration:
            return "Ersatz."

    monkeypatch.setattr(logic, "_call_model", fake_call_model)

    logic.propose_three_options(
        "Ich kann morgen leider nicht zum Arzt.",
        "en",
    )

    option_prompts = [p for p in prompts if "User input:" in p and "JSON" not in p][:3]
    for p in option_prompts:
        assert "German" in p


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