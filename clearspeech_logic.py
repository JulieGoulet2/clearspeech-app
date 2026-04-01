"""
Backend for ClearSpeech: OpenAI calls and parsing of model replies.

Expects OPENAI_API_KEY in the environment.
"""
from __future__ import annotations
import json
import re


import os
from difflib import SequenceMatcher

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


def _dominant_language_code(text: str, fallback: str) -> str:
    """
    Rough en/de/fr detection from user text so replies follow the *message*
    language, not the UI language.
    """
    if fallback not in ("en", "de", "fr"):
        fallback = "en"
    if not text.strip():
        return fallback

    t = f" {text.lower()} "
    # Do NOT use German "die" / "bin" as cues: they match English "die" / "bin" (noun).
    de = len(re.findall(r"[äöüß]", text))
    de += sum(
        1
        for w in (
            "ich",
            "nicht",
            "der",
            "und",
            "morgen",
            "kann",
            "kommen",
            "vielleicht",
            "arzt",
            "habe",
            "heute",
            "auch",
            "schon",
            "noch",
            "gibt",
            "meinst",
            "warum",
            "sie",
            "mir",
            "dir",
            "euch",
            "dass",
            "können",
            "müssen",
        )
        if re.search(rf"\b{re.escape(w)}\b", t)
    )

    fr = len(re.findall(r"[éèêëàâùûîïôçœæ]", text, re.IGNORECASE))
    fr += sum(
        1
        for w in (
            "je",
            "pas",
            "demain",
            "vous",
            "avec",
            "pour",
            "dans",
            "suis",
            "peux",
            "être",
            "comment",
            "pourquoi",
            "chez",
            "rendez-vous",
            "peut-être",
        )
        if re.search(rf"\b{re.escape(w)}\b", t)
    )

    en = sum(
        1
        for w in (
            "the",
            "a",
            "i",
            "you",
            "we",
            "they",
            "is",
            "am",
            "are",
            "were",
            "can't",
            "cannot",
            "don't",
            "not",
            "tomorrow",
            "yesterday",
            "want",
            "what",
            "when",
            "where",
            "why",
            "how",
            "going",
            "have",
            "has",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "doctor",
            "problem",
            "this",
            "that",
            "with",
            "from",
            "here",
            "there",
            "please",
            "thanks",
            "hello",
            "know",
            "like",
            "just",
            "very",
            "because",
            "about",
        )
        if re.search(rf"\b{re.escape(w)}\b", t)
    )

    scores = {"en": en, "de": de, "fr": fr}
    max_score = max(scores.values())
    if max_score == 0:
        return fallback

    tied = [code for code, s in scores.items() if s == max_score]
    if len(tied) == 1:
        return tied[0]
    # Ties: prefer English for ambiguous Latin text, then UI language if in the tie.
    if "en" in tied:
        return "en"
    if fallback in tied:
        return fallback
    return tied[0]


def _parse_option_lines(raw: str) -> list[str]:
    """Split model output into lines; strip leading bullets/numbers only (keep sentence punctuation)."""
    lines: list[str] = []
    for raw_line in raw.splitlines():
        if not raw_line.strip():
            continue
        line = raw_line.lstrip()
        if line.startswith("-") or line.startswith("•"):
            line = line[1:].lstrip()
        idx = 0
        while idx < len(line) and line[idx].isdigit():
            idx += 1
        if idx > 0 and idx < len(line) and line[idx] in ".)":
            line = line[idx + 1 :].lstrip()
        lines.append(line)
    return lines


def _too_similar(a: str, b: str) -> bool:
    """True if two option lines are duplicates or near-paraphrases."""
    a_norm = a.strip().lower()
    b_norm = b.strip().lower()
    if a_norm == b_norm:
        return True
    if len(a_norm) < 6 or len(b_norm) < 6:
        return False
    return SequenceMatcher(None, a_norm, b_norm).ratio() > 0.92


def _option_meanings_too_close(a: str, b: str) -> bool:
    """
    Stricter than _too_similar: catches paraphrases that keep the same meaning
    (same sentence scaffold, small edits). Used only for the 3-option list.
    """
    a_norm = a.strip().lower()
    b_norm = b.strip().lower()
    if a_norm == b_norm:
        return True
    if len(a_norm) < 8 or len(b_norm) < 8:
        return False
    full = SequenceMatcher(None, a_norm, b_norm).ratio()
    if full > 0.74:
        return True
    # Same long opening = same reading, even if the ending differs slightly.
    n = min(len(a_norm), len(b_norm), 100)
    if n >= 40:
        pre = SequenceMatcher(None, a_norm[:n], b_norm[:n]).ratio()
        if pre > 0.88:
            return True
    return False


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
    reply_lang = _dominant_language_code(text, lang)
    target_language = {"en": "English", "de": "German", "fr": "French"}[reply_lang]

    category_prompt = f"""The user interface language code is {lang} (fallback only).
The user MESSAGE is written mainly in {target_language} (code {reply_lang}).

User input:
{text}

Language rules:
- Use ONLY the message language ({target_language}), not the UI language, for any user-facing sentence.
- JSON category strings may be short English nouns (location, time, …) or the same language as the message.

Task:
Identify 3 DIFFERENT plausible ambiguity categories in this message.
Each category must support a genuinely different interpretation of the user’s words (not the same guess rephrased).

Possible categories include:
- location
- understanding
- decision
- time
- person
- action
- reason
- other

Rules:
- Choose categories that reflect genuinely different possible meanings.
- Do not repeat the same category.
- Output ONLY a JSON array of 3 short strings.
- Example:
["location", "understanding", "decision"]
"""

    raw_categories = _call_model(category_prompt)
    if raw_categories.startswith("ERROR:"):
        return [raw_categories]

    try:
        categories = json.loads(raw_categories)
        if not isinstance(categories, list):
            raise ValueError("Not a list")
        categories = [str(c).strip().lower() for c in categories if str(c).strip()]
    except Exception:
        categories = []

    if len(categories) < 3:
        categories = ["location", "understanding", "decision"]

    # keep unique categories only
    deduped_categories = []
    for cat in categories:
        if cat not in deduped_categories:
            deduped_categories.append(cat)
    categories = deduped_categories[:3]

    def _clean_line(line: str) -> str:
        line = line.strip()
        line = re.sub(r"^[-•]\s*", "", line)
        line = re.sub(r"^\d+[.)]\s*", "", line)
        return line.strip()

    options: list[str] = []

    for cat in categories:
        option_prompt = f"""The user wrote in {target_language}. Every line you output MUST be in {target_language} only.
Never use English for German input, never German for French input, etc.
(UI language is irrelevant for the answer language.)

User input:
{text}

You focus on ONE ambiguity type: {cat}.
Write ONE sentence that states a plausible meaning of the user’s message mainly under this type.

CRITICAL — meaning must be DISTINCT from other types:
- Do NOT paraphrase the same idea with small word changes (same situation, same conclusion).
- Do NOT reuse the same sentence opening or scaffold as you would for another ambiguity; vary the structure.
- If two sentences would still be true for the same real-world situation, they are NOT distinct enough — choose a different hypothesis.
- Example of BAD: three sentences that all say “you have not decided where the choir rehearses” with only connector or word-order changes.
- Example of GOOD: one sentence about WHERE, one about WHETHER you understood a message, one about WHICH event was meant — three different questions answered.

Rules:
- Exactly ONE short sentence in {target_language}.
- No other language. No explanation. No numbering.
"""

        raw_option = _call_model(option_prompt)
        if raw_option.startswith("ERROR:"):
            continue

        first_nonempty = ""
        for raw_line in raw_option.splitlines():
            cleaned = _clean_line(raw_line)
            if cleaned:
                first_nonempty = cleaned
                break

        if not first_nonempty:
            continue

        if any(_option_meanings_too_close(first_nonempty, existing) for existing in options):
            continue

        options.append(first_nonempty)

    if len(options) < 3:
        retry_prompt = f"""The user wrote in {target_language}. All sentences MUST be in {target_language} only.

User input:
{text}

The previous answers were too similar in wording or in meaning.

Produce exactly 3 short sentences that describe THREE DIFFERENT possible intentions or situations.
They must not be paraphrases of each other. Different uncertainty dimensions, for example:
- where / when / who / what event / whether something was understood / what was decided

Rules:
- Same core situation restated three ways is FORBIDDEN.
- Each line must answer a different “what might the user mean?” question.
- Output exactly 3 lines in {target_language}.
- No numbering. No explanations.
"""

        retry_raw = _call_model(retry_prompt)
        if not retry_raw.startswith("ERROR:"):
            retry_lines = []
            for raw_line in retry_raw.splitlines():
                cleaned = _clean_line(raw_line)
                if cleaned:
                    retry_lines.append(cleaned)

            for line in retry_lines:
                if any(_option_meanings_too_close(line, existing) for existing in options):
                    continue
                options.append(line)
                if len(options) == 3:
                    break

    # Token-overlap was too aggressive for German/French (shared function words).
    # Still ensure exactly 3 choices: ask for one more distinct line at a time.
    for _ in range(6):
        if len(options) >= 3:
            break
        already = "\n".join(f"- {o}" for o in options) if options else "(none yet)"
        fill_prompt = f"""The user wrote in {target_language}.

User input:
{text}

These interpretations are already proposed:
{already}

Write exactly ONE more short sentence in {target_language} only.
It must express a different possible meaning than any line above — not a paraphrase and not the same sentence with small edits.
Do not copy the opening words of the lines above; use a different angle (e.g. time vs place vs misunderstanding).
One line. No numbering. No explanation."""
        raw_fill = _call_model(fill_prompt)
        if raw_fill.startswith("ERROR:"):
            break
        first_fill = ""
        for raw_line in raw_fill.splitlines():
            cleaned = _clean_line(raw_line)
            if cleaned:
                first_fill = cleaned
                break
        if not first_fill:
            continue
        if any(_option_meanings_too_close(first_fill, existing) for existing in options):
            continue
        options.append(first_fill)

    return options[:3]


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