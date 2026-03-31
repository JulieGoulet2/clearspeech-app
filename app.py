"""
ClearSpeech — AI communication assistant (Streamlit UI).

User flow:
  compose → enter message and request a clearer version
  confirm → read proposal + confirmation question; Yes / No / start over
  clarify → if No: answer one question, then get an updated proposal
  final   → if Yes: show copy-ready text only

Run: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

import logic
from prompts import ui as ui_strings

PHASE_COMPOSE = "compose"
PHASE_CONFIRM = "confirm"
PHASE_CLARIFY = "clarify"
PHASE_FINAL = "final"


def init_session() -> None:
    if "phase" not in st.session_state:
        st.session_state.phase = PHASE_COMPOSE
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "original" not in st.session_state:
        st.session_state.original = ""
    if "proposed" not in st.session_state:
        st.session_state.proposed = ""
    if "confirm_question" not in st.session_state:
        st.session_state.confirm_question = ""
    if "clarify_prompt" not in st.session_state:
        st.session_state.clarify_prompt = ""
    if "clarify_answer" not in st.session_state:
        st.session_state.clarify_answer = ""


def reset_all() -> None:
    for key in (
        "phase",
        "original",
        "proposed",
        "confirm_question",
        "clarify_prompt",
        "clarify_answer",
    ):
        st.session_state.pop(key, None)
    init_session()


def render_copy_button(text: str) -> None:
    safe_text = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
        .replace("</", "<\\/")
    )

    components.html(
        f"""
        <button
            onclick="navigator.clipboard.writeText(`{safe_text}`)"
            style="
                background-color:#2e7d32;
                color:white;
                border:none;
                padding:10px 16px;
                border-radius:8px;
                font-size:16px;
                cursor:pointer;
                margin-top:8px;
                margin-bottom:8px;
            "
        >
            📋 Copy text
        </button>
        """,
        height=60,
    )


def main() -> None:
    st.set_page_config(page_title="ClearSpeech", page_icon="💬")
    init_session()

    lang = st.selectbox(
        ui_strings(st.session_state.lang)["language"],
        options=["en", "de", "fr"],
        format_func=lambda c: logic.language_name(c),
        key="lang",
    )
    t = ui_strings(lang)

    st.title(t["page_title"])
    st.caption(t["caption"])
    st.caption("Version 2.3")

    instructions = {
        "en": {
            "intro_1": "Write a short message, even if it is incomplete.",
            "intro_2": "I will suggest a clearer version and ask if this is what you mean.",
            "example_input_label": "Example input",
            "example_input": "I not can come tomorrow doctor",
            "example_sentence_label": "Example suggested sentence",
            "example_sentence": "I cannot come tomorrow because I have a doctor appointment.",
            "example_question_label": "Example question",
            "example_question": "Is this what you mean?",
        },
        "fr": {
            "intro_1": "Écris un message court, même s’il est incomplet.",
            "intro_2": "Je vais proposer une version plus claire et te demander si c’est bien ce que tu veux dire.",
            "example_input_label": "Exemple d’entrée",
            "example_input": "je pas venir demain docteur",
            "example_sentence_label": "Exemple de phrase proposée",
            "example_sentence": "Je ne peux pas venir demain parce que j’ai un rendez-vous chez le médecin.",
            "example_question_label": "Exemple de question",
            "example_question": "Est-ce que c’est ce que tu veux dire ?",
        },
        "de": {
            "intro_1": "Schreibe eine kurze Nachricht, auch wenn sie unvollständig ist.",
            "intro_2": "Ich schlage eine klarere Version vor und frage dich, ob das ist, was du meinst.",
            "example_input_label": "Beispieleingabe",
            "example_input": "morgen vielleicht nicht kommen Arzt",
            "example_sentence_label": "Beispiel für vorgeschlagenen Satz",
            "example_sentence": "Ich kann morgen vielleicht nicht kommen, weil ich einen Arzttermin habe.",
            "example_question_label": "Beispielfrage",
            "example_question": "Ist das, was du meinst?",
        },
    }

    inst = instructions.get(lang, instructions["en"])

    st.markdown(f"**{inst['intro_1']}**")
    st.markdown(inst["intro_2"])
    st.markdown("---")

    st.markdown(f"**{inst['example_input_label']}:**")
    st.write(inst["example_input"])

    st.markdown("### 💬")
    st.write(inst["example_sentence"])

    st.markdown("---")

    st.markdown("### ❓")
    st.write(inst["example_question"])

    st.markdown("---")

    if st.session_state.phase == PHASE_COMPOSE:
        text = st.text_area(
            t["your_message"],
            value=st.session_state.original,
            height=140,
            placeholder=t["message_placeholder"],
        )
        if st.button(t["get_clearer"], type="primary"):
            if not text.strip():
                st.warning(t["warn_empty_message"])
            else:
                st.session_state.original = text
                prop, q = logic.propose_rewrite_and_question(text, lang)
                st.session_state.proposed = prop
                st.session_state.confirm_question = q
                st.session_state.phase = PHASE_CONFIRM
                st.rerun()

    elif st.session_state.phase == PHASE_CONFIRM:
        st.subheader(t["proposed_version"])

        st.markdown("### 💬 Suggested sentence")
        st.write(st.session_state.proposed)

        st.markdown("---")

        st.markdown("### ❓")
        st.write(st.session_state.confirm_question)

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button(
                "✅ " + t["yes"],
                type="primary",
                use_container_width=True,
            ):
                st.session_state.phase = PHASE_FINAL
                st.rerun()

        with c2:
            if st.button(
                "❌ " + t["no"],
                use_container_width=True,
            ):
                st.session_state.clarify_prompt = logic.clarification_question_for_user(
                    lang
                )
                st.session_state.phase = PHASE_CLARIFY
                st.rerun()

        with c3:
            if st.button(
                t["start_over"],
                use_container_width=True,
            ):
                reset_all()
                st.rerun()

    elif st.session_state.phase == PHASE_CLARIFY:
        st.subheader(t["quick_clarification"])
        st.markdown(st.session_state.clarify_prompt)

        answer = st.text_area(
            t["your_answer"],
            value=st.session_state.clarify_answer,
            height=100,
            key="clarify_input",
        )

        b1, b2 = st.columns([1, 1])

        with b1:
            if st.button(
                t["update_suggestion"],
                type="primary",
                use_container_width=True,
            ):
                if not answer.strip():
                    st.warning(t["warn_empty_answer"])
                else:
                    st.session_state.clarify_answer = answer
                    prop, q = logic.propose_rewrite_after_clarification(
                        st.session_state.original, answer, lang
                    )
                    st.session_state.proposed = prop
                    st.session_state.confirm_question = q
                    st.session_state.phase = PHASE_CONFIRM
                    st.rerun()

        with b2:
            if st.button(
                t["cancel_start_over"],
                use_container_width=True,
            ):
                reset_all()
                st.rerun()

    elif st.session_state.phase == PHASE_FINAL:
        st.success(t["final_copy"])

        st.markdown("### Final text")
        st.text_area(
            label="",
            value=st.session_state.proposed,
            height=120,
            key="final_text_area",
        )

        render_copy_button(st.session_state.proposed)

        if st.button(t["new_message"], use_container_width=True):
            reset_all()
            st.rerun()

    else:
        st.error(t["unknown_step"])
        if st.button(t["reset"]):
            reset_all()
            st.rerun()


if __name__ == "__main__":
    main()