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

import logic
from prompts import ui as ui_strings

# --- Flow phases (stored in st.session_state["phase"]) ---
PHASE_COMPOSE = "compose"
PHASE_CONFIRM = "confirm"
PHASE_CLARIFY = "clarify"
PHASE_FINAL = "final"


def init_session() -> None:
    """Ensure session_state keys exist so reruns stay consistent."""
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
    """Clear conversation state and return to the compose step."""
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


def main() -> None:
    # Streamlit requires this as the first st.* call in the script.
    st.set_page_config(page_title="ClearSpeech", page_icon="💬")
    init_session()

    # UI language (labels, buttons): follows this selector.
    lang = st.selectbox(
        ui_strings(st.session_state.lang)["language"],
        options=["en", "de", "fr"],
        format_func=lambda c: logic.language_name(c),
        key="lang",
    )
    t = ui_strings(lang)

    st.title(t["page_title"])
    st.caption("Version 2.0")

    # Short hints + examples (content language matches app language).
    instructions = {
        "en": {
            "intro": "Write a short message, even if it is incomplete.\nI will suggest a clearer version and ask if this is what you mean.",
            "example_input": "Example input: I not can come tomorrow doctor",
            "example_output": "Example output: I cannot come tomorrow because I have a doctor appointment.\nIs this what you mean?",
        },
        "fr": {
            "intro": "Écris un message court, même s’il est incomplet.\nJe vais proposer une version plus claire et te demander si c’est bien ce que tu veux dire.",
            "example_input": "Exemple : je pas venir demain docteur",
            "example_output": "Résultat : Je ne peux pas venir demain parce que j’ai un rendez-vous chez le médecin.\nEst-ce que c’est ce que tu veux dire ?",
        },
        "de": {
            "intro": "Schreibe eine kurze Nachricht, auch wenn sie unvollständig ist.\nIch schlage eine klarere Version vor und frage dich, ob das ist, was du meinst.",
            "example_input": "Beispiel: morgen vielleicht nicht kommen Arzt",
            "example_output": "Ergebnis: Ich kann morgen vielleicht nicht kommen, weil ich einen Arzttermin habe.\nIst das, was du meinst?",
        },
    }

    inst = instructions.get(lang, instructions["en"])
    line1, line2 = inst["intro"].split("\n")
    st.markdown(f"**{line1}**")
    st.markdown(f"**{line2}**")
    st.markdown("---")
    st.markdown(f"**{inst['example_input']}**")
    st.markdown(f"**{inst['example_output']}**")

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
        # --- Proposed message ---
        st.markdown("**Suggested message:**")
        st.code(st.session_state.proposed, language=None)

        # --- Question ---
        st.markdown("---")
        st.markdown(f"### {st.session_state.confirm_question}")

        # --- Buttons ---
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
        b1, b2 = st.columns([1, 2])
        with b1:
            if st.button(t["update_suggestion"], type="primary"):
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
            if st.button(t["cancel_start_over"]):
                reset_all()
                st.rerun()

    elif st.session_state.phase == PHASE_FINAL:
        st.success(t["final_copy"])
        st.code(st.session_state.proposed, language=None)
        st.download_button(
            label="📋 Download text",
            data=st.session_state.proposed,
            file_name="clearspeech_text.txt",
            mime="text/plain",
        )
        if st.button(t["new_message"]):
            reset_all()
            st.rerun()

    else:
        st.error(t["unknown_step"])
        if st.button(t["reset"]):
            reset_all()
            st.rerun()


if __name__ == "__main__":
    main()
