"""
Backend for ClearSpeech: OpenAI calls and parsing of model replies.

Expects OPENAI_API_KEY in the environment.
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

Your goal is to help the user express their intended meaning clearly.

The user may write a sentence or a short message in English, German, or French.

Language rule:
- Always detect the language of the user’s input.
- Always reply entirely in the same language as the user.
- This includes labels, confirmation question, clarification questions, and final output text.
- Never use English unless the user wrote in English.

Language detection priority:
- Detect the language from the full sentence, not only the first word.
- If multiple languages are mixed, choose the dominant language of the sentence.
- The output MUST be entirely in that language.
- Never switch language during the interaction.
- The confirmation question MUST always be in the same language as the proposed sentence.

Consistency rule:
- Always use the SAME confirmation sentence in each language.
- Do not vary wording.

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

Ambiguity enforcement:
- If there is ANY ambiguity (time, meaning, subject), you MUST ask a clarification question.
- Do NOT guess.
- Never provide a final interpretation if multiple meanings are possible.

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

Mixed language handling:
- If the sentence mixes languages, detect the dominant language.
- Rewrite fully in ONE language only.
- Do not keep mixed language in output.

Missing context rule:
- If a sentence is incomplete (e.g. "doctor", "problem"), try to infer the most common real-world meaning.
- Prefer realistic everyday interpretations:
  - "doctor" → medical appointment
  - "problem" → personal or practical issue
- However:
  - If the meaning is clear and common, you may propose a rewritten sentence.
  - If there is more than one reasonable interpretation, you MUST ask a clarification question instead of guessing.
- Never invent specific details that were not implied by the user.

Quality rule:
- Make your best possible interpretation in the first proposal.
- Avoid vague or incomplete rewrites.
- Try to resolve the sentence in one step whenever possible.

Very unclear input:
- If the meaning is too unclear to make a reasonable guess, ask a clarification question instead of proposing a rewrite.
- If you are not confident (>70%) about the meaning, you MUST ask a clarification question FIRST.
- Do NOT propose a sentence in that case.

Confirmation sentences:
- English: "Is this what you mean?"
- German: "Ist das, was du meinst?"
- French: "Est-ce que c’est ce que tu veux dire?"
- ALWAYS use these exact sentences.
- Do NOT rephrase or simplify them.

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
    """First suggestion + confirmation question."""
    raw = _call_model(
        f"""Language hint: {lang}

User input:
{text}
"""
    )

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
    """Second turn after the user answered the clarification prompt."""
    prompt = f"""Language hint: {lang}

Original message:
{original_text}

User clarification:
{clarification}

Important:
- Detect the dominant language from the original message and clarification together.
- Use the language hint only as fallback.
- Reply in one language only.
- Use the exact confirmation sentence for that language.

Now provide:
1. a clearer rewritten sentence
2. the exact confirmation sentence
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


def propose_three_options(text: str, lang: str) -> list[str]:
    """
    Return 3 DISTINCT possible interpretations.
    The output language should follow the dominant language of the user input.
    The UI language is only a fallback hint.
    """
    prompt = f"""Language hint: {lang}

User input:
{text}

Language rules:
- Detect the language from the FULL user input, not only the first word.
- If the input is mainly in English, reply in English.
- If the input is mainly in French, reply in French.
- If the input is mainly in German, reply in German.
- If the input is mixed, choose the dominant language of the input.
- Use the language hint only as a fallback if the input language is unclear.
- Do NOT switch language.

Task:
Produce exactly 3 DISTINCT possible interpretations of the user's intended meaning.

Rules:
- Each option must be a short, clear sentence.
- Options must represent different meanings, not small paraphrases.
- Do not add numbering words like "Option 1".
- Do not add explanations.
- Output exactly 3 lines, one option per line.
- If fewer than 3 interpretations are plausible, still provide the best 3 distinct reasonable possibilities.
"""

    raw = _call_model(prompt)

    if raw.startswith("ERROR:"):
        return [raw]

    lines = [line.strip("-• 1234567890. \t") for line in raw.splitlines() if line.strip()]
    unique_lines: list[str] = []

    for line in lines:
        if line not in unique_lines:
            unique_lines.append(line)

    return unique_lines[:3]


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
    """Display names for the language dropdown in the UI."""
    names = {
        "en": "English",
        "de": "Deutsch",
        "fr": "Français",
    }
    return names.get(code, code)