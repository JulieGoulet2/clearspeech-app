import streamlit as st
import streamlit.components.v1 as components
import clearspeech_logic as logic

# --------- STATES ---------
PHASE_COMPOSE = "compose"
PHASE_CONFIRM = "confirm"
PHASE_OPTIONS = "options"
PHASE_CLARIFY = "clarify"
PHASE_FINAL = "final"


def init_session():
    if "phase" not in st.session_state:
        st.session_state.phase = PHASE_COMPOSE
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "original" not in st.session_state:
        st.session_state.original = ""
    if "proposed" not in st.session_state:
        st.session_state.proposed = ""
    if "question" not in st.session_state:
        st.session_state.question = ""
    if "options" not in st.session_state:
        st.session_state.options = []
    if "clarification" not in st.session_state:
        st.session_state.clarification = ""


def reset():
    current_lang = st.session_state.get("lang", "en")
    st.session_state.clear()
    init_session()
    st.session_state.lang = current_lang


def copy_button(text):
    safe_text = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
        .replace("</", "<\\/")
    )
    components.html(
        f"""
        <button onclick="navigator.clipboard.writeText(`{safe_text}`)"
        style="background-color:#2e7d32;color:white;padding:10px 16px;border:none;border-radius:8px;font-size:16px;">
        📋 Copy text
        </button>
        """,
        height=60,
    )


def ui_text(lang):
    strings = {
        "en": {
            "title": "ClearSpeech",
            "caption": "AI communication assistant",
            "language": "Language",
            "intro1": "Write a short message, even if it is incomplete.",
            "intro2": "I will suggest a clearer version and ask if this is what you mean.",
            "example_input_label": "Example input",
            "example_input": "I not can come tomorrow doctor",
            "example_sentence_label": "Suggested sentence",
            "example_sentence": "I cannot come tomorrow because I have a doctor appointment.",
            "example_question": "Is this what you mean?",
            "your_message": "Your message",
            "placeholder": "Write your message here...",
            "get_clearer": "Get clearer version",
            "proposed_version": "Proposed version",
            "suggested_sentence": "Suggested sentence",
            "yes": "Yes",
            "no": "No",
            "other_options": "Other options",
            "start_over": "Start over",
            "other_meanings": "Other possible meanings",
            "use_option": "Use option",
            "none_correct": "None of these are correct",
            "clarify_meaning": "Clarify my meaning",
            "clarify_title": "What do you mean exactly?",
            "your_answer": "Your answer",
            "update": "Update",
            "final_text": "Final text",
            "new_message": "New message",
        },
        "fr": {
            "title": "ClearSpeech",
            "caption": "Assistant IA de communication",
            "language": "Langue",
            "intro1": "Écris un message court, même s’il est incomplet.",
            "intro2": "Je vais proposer une version plus claire et te demander si c’est bien ce que tu veux dire.",
            "example_input_label": "Exemple d’entrée",
            "example_input": "je pas venir demain docteur",
            "example_sentence_label": "Phrase proposée",
            "example_sentence": "Je ne peux pas venir demain parce que j’ai un rendez-vous chez le médecin.",
            "example_question": "Est-ce que c’est ce que tu veux dire ?",
            "your_message": "Ton message",
            "placeholder": "Écris ton message ici...",
            "get_clearer": "Obtenir une version plus claire",
            "proposed_version": "Version proposée",
            "suggested_sentence": "Phrase proposée",
            "yes": "Oui",
            "no": "Non",
            "other_options": "Autres options",
            "start_over": "Recommencer",
            "other_meanings": "Autres significations possibles",
            "use_option": "Utiliser l’option",
            "none_correct": "Aucune de ces options n’est correcte",
            "clarify_meaning": "Clarifier ce que je veux dire",
            "clarify_title": "Qu’est-ce que tu veux dire exactement ?",
            "your_answer": "Ta réponse",
            "update": "Mettre à jour",
            "final_text": "Texte final",
            "new_message": "Nouveau message",
        },
        "de": {
            "title": "ClearSpeech",
            "caption": "KI-Kommunikationsassistent",
            "language": "Sprache",
            "intro1": "Schreibe eine kurze Nachricht, auch wenn sie unvollständig ist.",
            "intro2": "Ich schlage eine klarere Version vor und frage dich, ob das ist, was du meinst.",
            "example_input_label": "Beispieleingabe",
            "example_input": "morgen vielleicht nicht kommen Arzt",
            "example_sentence_label": "Vorgeschlagener Satz",
            "example_sentence": "Ich kann morgen vielleicht nicht kommen, weil ich einen Arzttermin habe.",
            "example_question": "Ist das, was du meinst?",
            "your_message": "Deine Nachricht",
            "placeholder": "Schreibe hier deine Nachricht...",
            "get_clearer": "Klarere Version erzeugen",
            "proposed_version": "Vorgeschlagene Version",
            "suggested_sentence": "Vorgeschlagener Satz",
            "yes": "Ja",
            "no": "Nein",
            "other_options": "Andere Optionen",
            "start_over": "Neu anfangen",
            "other_meanings": "Andere mögliche Bedeutungen",
            "use_option": "Option verwenden",
            "none_correct": "Keine davon ist richtig",
            "clarify_meaning": "Meine Bedeutung klarstellen",
            "clarify_title": "Was meinst du genau?",
            "your_answer": "Deine Antwort",
            "update": "Aktualisieren",
            "final_text": "Finaler Text",
            "new_message": "Neue Nachricht",
        },
    }
    return strings[lang]


def main():
    st.set_page_config(page_title="ClearSpeech", page_icon="💬")
    init_session()

    lang = st.selectbox(
        "Language / Langue / Sprache",
        options=["en", "fr", "de"],
        format_func=lambda x: logic.language_name(x),
        key="lang",
    )
    t = ui_text(lang)

    st.title(t["title"])
    st.caption(t["caption"])
    st.caption("Version 2.5")

    # ---------- FIRST PAGE EXPLANATION + EXAMPLE ----------
    st.markdown(f"**{t['intro1']}**")
    st.markdown(t["intro2"])
    st.markdown("---")

    st.markdown(f"**{t['example_input_label']}:**")
    st.write(t["example_input"])

    st.markdown(f"### 💬 {t['example_sentence_label']}")
    st.write(t["example_sentence"])

    st.markdown("---")

    st.markdown("### ❓")
    st.write(t["example_question"])

    st.markdown("---")

    # ---------- COMPOSE ----------
    if st.session_state.phase == PHASE_COMPOSE:
        text = st.text_area(
            t["your_message"],
            value=st.session_state.original,
            placeholder=t["placeholder"],
            height=140,
        )

        if st.button(t["get_clearer"]):
            if text.strip():
                st.session_state.original = text
                prop, q = logic.propose_rewrite_and_question(text, lang)
                st.session_state.proposed = prop
                st.session_state.question = q
                st.session_state.phase = PHASE_CONFIRM
                st.rerun()

    # ---------- CONFIRM ----------
    elif st.session_state.phase == PHASE_CONFIRM:
        st.subheader(t["proposed_version"])

        st.markdown(f"### 💬 {t['suggested_sentence']}")
        st.write(st.session_state.proposed)

        st.markdown("---")

        st.markdown("### ❓")
        st.write(st.session_state.question)

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if st.button(f"✅ {t['yes']}", use_container_width=True):
                st.session_state.phase = PHASE_FINAL
                st.rerun()

        with c2:
            if st.button(f"❌ {t['no']}", use_container_width=True):
                st.session_state.phase = PHASE_CLARIFY
                st.rerun()

        with c3:
            if st.button(f"🔀 {t['other_options']}", use_container_width=True):
                st.session_state.options = logic.propose_three_options(
                    st.session_state.original, lang
                )
                st.session_state.phase = PHASE_OPTIONS
                st.rerun()

        with c4:
            if st.button(t["start_over"], use_container_width=True):
                reset()
                st.rerun()

    # ---------- OPTIONS ----------
    elif st.session_state.phase == PHASE_OPTIONS:
        st.subheader(t["other_meanings"])

        for i, option in enumerate(st.session_state.options):
            st.markdown(f"### Option {i+1}")
            st.write(option)
            if st.button(f"{t['use_option']} {i+1}", key=f"opt_{i}"):
                st.session_state.proposed = option
                st.session_state.phase = PHASE_FINAL
                st.rerun()

            st.markdown("---")

        st.markdown(f"**{t['none_correct']}**")
        if st.button(f"❓ {t['clarify_meaning']}"):
            st.session_state.phase = PHASE_CLARIFY
            st.rerun()

    # ---------- CLARIFY ----------
    elif st.session_state.phase == PHASE_CLARIFY:
        st.markdown(f"### {t['clarify_title']}")
        answer = st.text_area(t["your_answer"], height=100)

        if st.button(t["update"]):
            if answer.strip():
                st.session_state.clarification = answer
                prop, q = logic.propose_rewrite_after_clarification(
                    st.session_state.original, answer, lang
                )
                st.session_state.proposed = prop
                st.session_state.question = q
                st.session_state.phase = PHASE_CONFIRM
                st.rerun()

    # ---------- FINAL ----------
    elif st.session_state.phase == PHASE_FINAL:
        st.markdown(f"### {t['final_text']}")
        st.text_area("", value=st.session_state.proposed, height=120)
        copy_button(st.session_state.proposed)

        if st.button(t["new_message"]):
            reset()
            st.rerun()


if __name__ == "__main__":
    main()