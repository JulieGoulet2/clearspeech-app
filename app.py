import html
import streamlit as st
import streamlit.components.v1 as components
import clearspeech_logic as logic

# --------- STATES ---------
PHASE_COMPOSE = "compose"
PHASE_CONFIRM = "confirm"
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
    if "clarification" not in st.session_state:
        st.session_state.clarification = ""


def reset():
    current_lang = st.session_state.get("lang", "en")
    st.session_state.clear()
    init_session()
    st.session_state.lang = current_lang


def copy_button(text: str, label: str):
    safe_text = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
        .replace("</", "<\\/")
    )
    safe_label = html.escape(label)

    components.html(
        f"""
        <button onclick="navigator.clipboard.writeText(`{safe_text}`)"
        style="
            background-color:#2e7d32;
            color:white;
            padding:10px 16px;
            border:none;
            border-radius:8px;
            font-size:16px;
            cursor:pointer;
        ">
            {safe_label}
        </button>
        """,
        height=60,
    )


def ui_text(lang):
    strings = {
        "en": {
            "title": "ClearSpeech",
            "caption": "AI communication assistant",
            "language_selector": "Language / Langue / Sprache",
            "intro1": "Write a short message, even if it is incomplete.",
            "intro2": "I will suggest a clearer version and ask if this is what you mean.",
            "example_input_label": "Example input",
            "example_input": "I not can come tomorrow doctor",
            "example_sentence_label": "Suggested sentence",
            "example_sentence": "I cannot come tomorrow because I have a doctor appointment.",
            "example_question": "Is this what you mean?",
            "instructions_title": "ℹ️ How this app works",
            "your_message": "Your message",
            "placeholder": "Write your message here...",
            "get_clearer": "Get clearer version",
            "proposed_version": "Proposed version",
            "suggested_sentence": "Suggested sentence",
            "yes": "Yes",
            "no": "No",
            "start_over": "Start over",
            "clarify_title": "What do you mean exactly?",
            "your_answer": "Your answer",
            "update": "Update",
            "final_text": "Final text",
            "new_message": "New message",
            "copy": "📋 Copy",
        },
        "fr": {
            "title": "ClearSpeech",
            "caption": "Assistant IA de communication",
            "language_selector": "Language / Langue / Sprache",
            "intro1": "Écris un message court, même s’il est incomplet.",
            "intro2": "Je vais proposer une version plus claire et te demander si c’est bien ce que tu veux dire.",
            "example_input_label": "Exemple d’entrée",
            "example_input": "je pas venir demain docteur",
            "example_sentence_label": "Phrase proposée",
            "example_sentence": "Je ne peux pas venir demain parce que j’ai un rendez-vous chez le médecin.",
            "example_question": "Est-ce que c’est ce que tu veux dire ?",
            "instructions_title": "ℹ️ Comment fonctionne l'application",
            "your_message": "Ton message",
            "placeholder": "Écris ton message ici...",
            "get_clearer": "Obtenir une version plus claire",
            "proposed_version": "Version proposée",
            "suggested_sentence": "Phrase proposée",
            "yes": "Oui",
            "no": "Non",
            "start_over": "Recommencer",
            "clarify_title": "Qu’est-ce que tu veux dire exactement ?",
            "your_answer": "Ta réponse",
            "update": "Mettre à jour",
            "final_text": "Texte final",
            "new_message": "Nouveau message",
            "copy": "📋 Copier",
        },
        "de": {
            "title": "ClearSpeech",
            "caption": "KI-Kommunikationsassistent",
            "language_selector": "Language / Langue / Sprache",
            "intro1": "Schreibe eine kurze Nachricht, auch wenn sie unvollständig ist.",
            "intro2": "Ich schlage eine klarere Version vor und frage dich, ob das ist, was du meinst.",
            "example_input_label": "Beispieleingabe",
            "example_input": "morgen vielleicht nicht kommen Arzt",
            "example_sentence_label": "Vorgeschlagener Satz",
            "example_sentence": "Ich kann morgen vielleicht nicht kommen, weil ich einen Arzttermin habe.",
            "example_question": "Ist das, was du meinst?",
            "instructions_title": "ℹ️ Wie die App funktioniert",
            "your_message": "Deine Nachricht",
            "placeholder": "Schreibe hier deine Nachricht...",
            "get_clearer": "Klarere Version erzeugen",
            "proposed_version": "Vorgeschlagene Version",
            "suggested_sentence": "Vorgeschlagener Satz",
            "yes": "Ja",
            "no": "Nein",
            "start_over": "Neu anfangen",
            "clarify_title": "Was meinst du genau?",
            "your_answer": "Deine Antwort",
            "update": "Aktualisieren",
            "final_text": "Finaler Text",
            "new_message": "Neue Nachricht",
            "copy": "📋 Kopieren",
        },
    }
    return strings[lang]


def render_instructions(lang):
    if lang == "fr":
        with st.expander("ℹ️ Comment fonctionne l'application"):
            st.markdown("""
### Ce que fait cette application

Cette application vous aide à transformer un message court ou incomplet en une phrase claire.

Vous pouvez écrire avec des erreurs ou seulement quelques mots.

---

### Comment l'utiliser

#### Étape 1 — Écrire un message
Écrivez un message court.

#### Étape 2 — Première proposition
L'application propose une phrase et demande si c'est correct.

- ✅ Oui → texte final
- ❌ Non → clarification
- Recommencer → repartir du début

#### Étape 3 — Clarification
Vous pouvez expliquer un peu plus votre intention.

#### Étape 4 — Texte final
Vous obtenez une phrase claire à copier.

---

### Remarques

- Les phrases incomplètes sont acceptées
- Vous n’avez pas besoin d’écrire parfaitement
- L’application essaie de comprendre votre intention
- Les réponses sont générées avec le modèle **GPT-4.1 mini** d’OpenAI

---

Contact : **drjuliegoulet@gmail.com**
""")

    elif lang == "de":
        with st.expander("ℹ️ Wie die App funktioniert"):
            st.markdown("""
### Was diese App macht

Diese App hilft dir, eine kurze oder unklare Nachricht in einen klaren Satz umzuwandeln.

Du kannst Fehler machen oder nur wenige Wörter schreiben.

---

### Nutzung

#### Schritt 1 — Nachricht schreiben
Schreibe eine kurze Nachricht.

#### Schritt 2 — Erster Vorschlag
Die App macht einen Vorschlag und fragt, ob das richtig ist.

- ✅ Ja → finaler Text
- ❌ Nein → klären
- Neu anfangen → von vorne beginnen

#### Schritt 3 — Klärung
Du kannst deine Bedeutung genauer erklären.

#### Schritt 4 — Finaler Text
Du bekommst einen klaren Satz zum Kopieren.

---

### Hinweise

- Unvollständige Sätze sind in Ordnung
- Du musst nicht perfekt schreiben
- Die App versucht, deine Bedeutung zu verstehen
- Die Antworten werden mit dem Modell **GPT-4.1 mini** von OpenAI erzeugt

---

Kontakt: **drjuliegoulet@gmail.com**
""")

    else:
        with st.expander("ℹ️ How this app works"):
            st.markdown("""
### What this app does

This app helps you turn a short or incomplete message into a clear sentence.

You can write with mistakes or with only a few words.

---

### How to use it

#### Step 1 — Write your message
Write a short message.

#### Step 2 — First suggestion
The app suggests a sentence and asks if it is correct.

- ✅ Yes → final text
- ❌ No → clarification
- Start over → begin again

#### Step 3 — Clarification
You can explain your meaning a little more.

#### Step 4 — Final text
You get a clear sentence that you can copy.

---

### Notes

- Incomplete input is OK
- You do not need to write perfectly
- The app tries to understand your meaning
- Suggestions are generated using OpenAI’s **GPT-4.1 mini** model

---

Contact: **drjuliegoulet@gmail.com**
""")


def main():
    st.set_page_config(page_title="ClearSpeech", page_icon="💬")
    init_session()

    lang = st.selectbox(
        "Language / Langue / Sprache",
        options=["en", "fr", "de"],
        format_func=lambda x: logic.language_name(x),
        key="lang",
    )
    render_instructions(lang)
    t = ui_text(lang)

    st.title(t["title"])
    st.caption(t["caption"])
    st.caption("Version 2.7")

    # render_instructions(lang)

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

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button(f"✅ {t['yes']}", use_container_width=True):
                st.session_state.phase = PHASE_FINAL
                st.rerun()

        with c2:
            if st.button(f"❌ {t['no']}", use_container_width=True):
                st.session_state.phase = PHASE_CLARIFY
                st.rerun()

        with c3:
            if st.button(t["start_over"], use_container_width=True):
                reset()
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
        copy_button(st.session_state.proposed, t["copy"])

        if st.button(t["new_message"]):
            reset()
            st.rerun()


if __name__ == "__main__":
    main()