"""
Backend for ClearSpeech: OpenAI calls and parsing of model replies.

Expects OPENAI_API_KEY in the environment (e.g. a project `.env` file; see README).
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Create the OpenAI client once and reuse it."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


SYSTEM_PROMPT = """
You are an AI communication assistant for people with communication difficulties.

Input may be in English, German, or French.

Main goal:
Help the user express their intended meaning clearly.

Language:
- Detect the language from the full input, not only the first word.
- If the input mixes languages, choose the dominant language.
- Reply entirely in that one language.
- Never switch language during the interaction.
- The proposed sentence, confirmation question, and clarification question must all be in the same language.

Meaning:
- Preserve the user's intended meaning.
- Do not invent missing details.
- If there is more than one reasonable meaning, ask a clarification question instead of guessing.
- If confidence is low, ask a clarification question first.

Uncertainty:
- Keep uncertainty words such as maybe, perhaps, vielleicht, peut-être.

Missing context:
- If a sentence is incomplete, try to infer the most common real-world meaning.
- Prefer realistic everyday interpretations.
- But if more than one interpretation is reasonable, ask a clarification question instead of guessing.

Idioms and false friends:
- Watch for figurative language, false friends, and literal translations.
- If unsure, ask for clarification instead of rewriting literally.

Confirmation sentences:
- English: Is this what you mean?
- German: Ist das, was du meinst?
- French: Est-ce que c’est ce que tu veux dire?
- Always use exactly these sentences.

Output:
- If meaning is clear enough:
  line 1 = rewritten sentence
  line 2 = exact confirmation sentence in the same language
- If meaning is unclear:
  line 1 = short clarification question
  line 2 = empty
- No extra explanation.
""".strip()


def _call_model(user_input: str) -> str:
    """Send one user string to the model; return raw text or an error prefix."""
    try:
        response = get_client().responses.create(
            model="gpt-4.1-mini",
            instructions=SYSTEM_PROMPT,
            input=user_input,
            temperature=0.1,
        )
        return response.output_text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


def propose_rewrite_and_question(text: str, lang: str) -> tuple[str, str]:
    """
    First turn: model returns line 1 = rewrite or clarification question,
    line 2 = confirmation question (or empty if clarification-first).
    """
    raw = _call_model(text)

    if raw.startswith("ERROR:"):
        return raw, clarification_question_for_user(lang)

    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    if len(lines) >= 2:
        return lines[0], lines[1]

    if len(lines) == 1:
        # If the model returned only one line, assume it is a proposal
        # and use a fixed confirmation fallback.
        return lines[0], confirmation_question_for_user(lang)

    return "", confirmation_question_for_user(lang)


def propose_rewrite_after_clarification(
    original_text: str, clarification: str, lang: str
) -> tuple[str, str]:
    """Second turn after the user answered the clarification prompt."""
    prompt = f"""Original message:
{original_text}

User clarification:
{clarification}

Now provide:
line 1 = clearer rewritten sentence
line 2 = exact confirmation sentence in the same language
"""

    raw = _call_model(prompt)

    if raw.startswith("ERROR:"):
        return raw, clarification_question_for_user(lang)

    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    if len(lines) >= 2:
        return lines[0], lines[1]

    if len(lines) == 1:
        return lines[0], confirmation_question_for_user(lang)

    return "", confirmation_question_for_user(lang)


def clarification_question_for_user(lang: str) -> str:
    """Shown in the UI when the user clicks No."""
    questions = {
        "en": "What do you mean exactly?",
        "de": "Was meinst du genau?",
        "fr": "Qu’est-ce que tu veux dire exactement ?",
    }
    return questions.get(lang, questions["en"])


def confirmation_question_for_user(lang: str) -> str:
    """Fixed fallback confirmation sentence."""
    questions = {
        "en": "Is this what you mean?",
        "de": "Ist das, was du meinst?",
        "fr": "Est-ce que c’est ce que tu veux dire?",
    }
    return questions.get(lang, questions["en"])


def language_name(code: str) -> str:
    """Display names for the language dropdown in the Streamlit UI."""
    names = {
        "en": "English",
        "de": "Deutsch",
        "fr": "Français",
    }
    return names.get(code, code)