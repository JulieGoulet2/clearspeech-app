# ClearSpeech

ClearSpeech is a simple AI communication assistant designed for people with **language or communication difficulties** (e.g. aphasia, non-native speakers, cognitive load).

It helps users turn short, unclear, or incomplete input into a **clear, correct sentence**, with minimal effort.

---
## 💡 Why this project

This project was built to explore how AI can support people with communication difficulties (including aphasia).

It focuses on:
- reducing cognitive load
- clarifying ambiguous input
- enabling simple interaction (Yes/No flow)

The goal is to create an accessible AI assistant that helps users express themselves clearly in everyday situations.

---
## 🚀 What it does

- Accepts short or imperfect input (e.g. "doctor tomorrow", "i want become beer")
- Suggests a **clear rewritten sentence**
- Asks a simple confirmation: *"Is this what you mean?"*
- If not correct → asks one clarification → proposes again
- Final result is easy to **copy and reuse**
- Includes unit tests for reliability and accessibility use cases

---

## 🌍 Supported languages

- English  
- German  
- French  

The system:
- detects the **dominant language of the input**
- always replies in that language
- avoids mixing languages

---

## 🧠 Key design principles

- Low cognitive load (simple sentences, one question at a time)
- Accessible interaction (Yes / No flow)
- No need for perfect grammar
- Handles:
  - incomplete input
  - ambiguity
  - false friends / literal translations
  - mixed-language sentences

---

## 🧪 Current version

**Version: 2.6 (testing phase)**

Recent improvements:
- better language detection
- fixed confirmation sentence consistency
- improved handling of ambiguity and idioms
- copy-to-clipboard for final text

---

## 🔮 Roadmap

- **3.0** → Text-to-speech (read output aloud)
- **4.0** → Speech-to-text (voice input)
- UI redesign (mobile + accessibility focus)

---

## 🛠️ Tech stack

- Python
- Streamlit
- OpenAI API (`gpt-4.1-mini`)

---

## ⚙️ Setup

## 🧪 Testing

This project includes unit tests to ensure reliability and correctness of the AI behavior.

### What is tested

- Core logic functions (language handling, confirmation, clarification)
- Model interaction (using mocked responses — no real API calls)
- App smoke test (basic startup without crash)

### How tests work

Tests use `pytest` and `monkeypatch` to simulate the AI model.

This means:
- Tests are fast
- Tests are free (no API cost)
- Tests are stable and reproducible

### Run tests

From the project root:

```bash
python -m pytest -q
```

### Requirements

- Python 3.10+
- OpenAI API key

### Installation

```bash
git clone https://github.com/JulieGoulet2/clearspeech-app.git
cd clearspeech-app

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

