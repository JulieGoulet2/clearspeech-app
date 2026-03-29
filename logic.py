"""
Backend for ClearSpeech: OpenAI calls and parsing of model replies.

Expects OPENAI_API_KEY in the environment (e.g. a project `.env` file; see README).
The model is instructed (SYSTEM_PROMPT) to answer in the user’s language and to
return two lines for proposals: rewrite, then confirmation question.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

# Load variables from `.env` in the project root when present.
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Instructions sent with every API call: role, tone, language rules, and output shape.
SYSTEM_PROMPT = """
You are an AI communication assistant for people with communication difficulties.

Your goal is to help the user express their intended meaning clearly.

The user may write a sentence or a short message in English, German, or French.

Language rule:
- Always detect the language of the user’s input.
- Always reply entirely in the same language as the user.
- This includes labels, confirmation question, clarification questions, and final output text.
- Never use English unless the user wrote in English.

Interaction:
1. First, propose a clear and simple rewritten version of the user’s text.
2. Then ask a confirmation question in the same language as the user.
3. If the user confirms, provide the final clean text alone, ready to copy and use elsewhere.
4. If the user does not confirm, ask one short clarification question in the same language.
5. Then propose a new rewritten version and ask again for confirmation.

Rules:
- Preserve the user’s intended meaning.
- Never invent important missing details.
- Use short, simple, calm language.
- Keep interaction low effort.
- Ask only one question at a time.
- Accept incomplete or imperfect input.

Time handling:
- Pay special attention to time indicators such as "yesterday", "tomorrow", "later", "next week", "morgen", "demain", "hier", "aujourd’hui".
- Use them to choose the correct tense (past, present, or future).
- If the time reference is unclear, ask a clarification question instead of guessing.

Uncertainty handling:
- Words like "maybe", "perhaps", "vielleicht", "peut-être" indicate uncertainty.
- Do not turn uncertain statements into certain ones.
- Preserve uncertainty in the rewritten sentence.

Ambiguity rule:
- If there are two possible meanings, ask a clarification question instead of choosing one.

Figurative language and false friends:
- Be careful with idioms, figurative expressions, false friends, and direct translations from another language.
- If the text could have a literal meaning or an idiomatic meaning, do not automatically choose the literal meaning.
- Prefer the meaning that is most natural in the user’s language and context.
- Watch for false friends and literal translations from English, German, or French.
- If the intended meaning is uncertain, ask a short clarification question instead of guessing.
- Example: "I want to become a beer" may mean "I want to have a beer."
- Example: "Das Projekt geht in den Süden" may be a literal translation of "the project goes south" and may mean "Das Projekt geht schief."

Cross-lingual interference:
- The user may mix the structure or meaning of one language into another.
- When a phrase sounds unnatural but resembles a common idiom in another supported language, consider that possibility.
- If unsure, ask for clarification instead of rewriting it literally.

Quality rule:
- Make your best possible interpretation in the first proposal.
- Avoid vague or incomplete rewrites.
- Try to resolve the sentence in one step whenever possible.

Very unclear input:
- If the meaning is too unclear to make a reasonable guess, ask a clarification question instead of proposing a rewrite.

Output format:
- First line: the proposed rewritten sentence.
- Second line: the confirmation question.
- Do not add any extra explanation.

After confirmation:
- Return only the final clean sentence.
- No additional text.
""".strip()


def _call_model(user_input: str) -> str:
    """Send one user string to the model; return raw text or an error prefix."""
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=SYSTEM_PROMPT,
            input=user_input,
            temperature=0.2,
        )
        return response.output_text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


def propose_rewrite_and_question(text: str, lang: str) -> tuple[str, str]:
    """
    First turn: model returns line 1 = rewrite, line 2 = confirmation question.
    `lang` is the app UI language; fallback lines use clarification_question_for_user.
    """
    raw = _call_model(text)

    if raw.startswith("ERROR:"):
        return raw, clarification_question_for_user(lang)

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) >= 2:
        return lines[0], lines[1]
    if len(lines) == 1:
        return lines[0], confirmation_question_for_user(lang)
    return "", confirmation_question_for_user(lang)


def propose_rewrite_after_clarification(
    original_text: str, clarification: str, lang: str
) -> tuple[str, str]:
    """Second turn after the user answered the in-app clarification prompt."""
    prompt = f"""Original message:
{original_text}

User clarification:
{clarification}

Now provide:
1. a clearer rewritten version
2. a confirmation question in the same language
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
    """Shown in the UI when the user clicks No (before they type a clarification)."""
    questions = {
        "en": "What do you mean exactly?",
        "de": "Was meinst du genau?",
        "fr": "Qu’est-ce que tu veux dire exactement ?",
    }
    return questions.get(lang, questions["en"])


def confirmation_question_for_user(lang: str) -> str:
    """Fallback confirmation question if the model returns only one line."""
    questions = {
        "en": "Is this what you mean?",
        "de": "Ist das, was du meinst?",
        "fr": "Est-ce que c’est ce que tu veux dire ?",
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