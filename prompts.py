"""
Prompt templates for the communication assistant.

These strings are not sent to an API yet — they document what the real
integration will use. Replace or load from here when you wire up the model.
"""

# --- Shared instructions (future system / developer messages) ---

SYSTEM_INTENT = (
    "You help users rewrite short messages so they are clear, polite, and direct. "
    "You respond in the same language as the user's text unless asked otherwise."
)

# --- Per-step outlines (fill with your real prompts later) ---

REWRITE_USER_TEMPLATE = """Original message:
{original}

Target language for the reply: {language_name}

Return:
1) A clearer rewritten version (plain text only).
2) One short confirmation question asking if this matches what the user meant.
"""

CLARIFICATION_USER_TEMPLATE = """Original message:
{original}

User's clarification (answer to your question):
{clarification}

Target language: {language_name}

Return:
1) An updated rewritten version incorporating the clarification.
2) One short confirmation question in the same language.
"""

# --- Labels for UI / future structured outputs ---

LANGUAGE_NAMES = {
    "en": "English",
    "de": "German",
    "fr": "French",
}

# Streamlit UI copy — switch with the language selector (en / de / fr).
UI_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "ClearSpeech",
        "caption": "Prototype — placeholder logic (no API yet)",
        "language": "Language",
        "your_message": "Your message",
        "message_placeholder": "Type a short message in English, German, or French…",
        "get_clearer": "Get a clearer version",
        "warn_empty_message": "Please enter some text.",
        "proposed_version": "Proposed version",
        "yes": "Yes",
        "no": "No",
        "start_over": "Start over",
        "quick_clarification": "Quick clarification",
        "your_answer": "Your answer",
        "update_suggestion": "Update suggestion",
        "warn_empty_answer": "Please add a short answer.",
        "cancel_start_over": "Cancel and start over",
        "final_copy": "Final text — copy below",
        "new_message": "New message",
        "unknown_step": "Unknown step — use Start over or reload.",
        "reset": "Reset",
    },
    "de": {
        "page_title": "ClearSpeech",
        "caption": "Prototyp — Platzhalter-Logik (noch keine API)",
        "language": "Sprache",
        "your_message": "Ihre Nachricht",
        "message_placeholder": "Kurzen Text auf Deutsch, Englisch oder Französisch eingeben …",
        "get_clearer": "Klarere Version vorschlagen",
        "warn_empty_message": "Bitte Text eingeben.",
        "proposed_version": "Vorschlag",
        "yes": "Ja",
        "no": "Nein",
        "start_over": "Neu beginnen",
        "quick_clarification": "Kurze Rückfrage",
        "your_answer": "Ihre Antwort",
        "update_suggestion": "Vorschlag aktualisieren",
        "warn_empty_answer": "Bitte kurz antworten.",
        "cancel_start_over": "Abbrechen und neu beginnen",
        "final_copy": "Finaler Text — unten kopieren",
        "new_message": "Neue Nachricht",
        "unknown_step": "Unbekannter Schritt — Neu beginnen oder Seite neu laden.",
        "reset": "Zurücksetzen",
    },
    "fr": {
        "page_title": "ClearSpeech",
        "caption": "Prototype — logique fictive (pas d’API pour l’instant)",
        "language": "Langue",
        "your_message": "Votre message",
        "message_placeholder": "Saisissez un court texte en français, anglais ou allemand…",
        "get_clearer": "Obtenir une version plus claire",
        "warn_empty_message": "Veuillez saisir du texte.",
        "proposed_version": "Version proposée",
        "yes": "Oui",
        "no": "Non",
        "start_over": "Recommencer",
        "quick_clarification": "Précision rapide",
        "your_answer": "Votre réponse",
        "update_suggestion": "Mettre à jour la proposition",
        "warn_empty_answer": "Veuillez ajouter une courte réponse.",
        "cancel_start_over": "Annuler et recommencer",
        "final_copy": "Texte final — copier ci-dessous",
        "new_message": "Nouveau message",
        "unknown_step": "Étape inconnue — recommencez ou rechargez la page.",
        "reset": "Réinitialiser",
    },
}


def ui(lang: str) -> dict[str, str]:
    """Localized UI strings for the selected language code."""
    return UI_LABELS.get(lang, UI_LABELS["en"])
