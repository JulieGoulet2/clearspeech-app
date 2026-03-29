# ClearSpeech

Streamlit app that helps you rewrite short messages in **English**, **German**, or **French**, then confirm the wording with **Yes** / **No**. If you choose **No**, you answer one clarification and get a new proposal. **Yes** shows the final text in a copy-friendly block.

The assistant logic lives in `logic.py` and calls the **OpenAI API** using `OPENAI_API_KEY`.

## Requirements

- Python 3.10+ recommended  
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Setup (Mac)

```bash
cd ai-communication-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### API key

Create a file named `.env` in the project root (same folder as `app.py`):

```bash
OPENAI_API_KEY=sk-...
```

**Do not commit `.env`.** It is listed in `.gitignore` so your key stays local. If you use Git, confirm with:

```bash
git check-ignore -v .env
```

You should see `.env` matched by the `.gitignore` rule.

Optional: instead of `.env`, you can set `OPENAI_API_KEY` in your shell or use Streamlit secrets (see [Streamlit secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management)); you would then adjust how `logic.py` reads the key.

## Run

```bash
source .venv/bin/activate
streamlit run app.py
```

Open `http://localhost:8501` if the browser does not open automatically.

## Project layout

| File | Role |
|------|------|
| `app.py` | Streamlit UI, session state, and user flow (compose → confirm → clarify → final) |
| `logic.py` | OpenAI client, system prompt, and parsing of two-line model replies |
| `prompts.py` | UI strings per language and prompt templates for future use |
| `requirements.txt` | Python dependencies |
| `.env` | Your API key (local only; not tracked by git) |

## Flow

1. Pick a **UI language** (labels and buttons) and type a short message.  
2. Get a **proposed rewrite** and a **confirmation question** (model answers in the language of your message, per `logic.py` instructions).  
3. **Yes** → final text only. **No** → one clarification step → updated proposal.  
4. **Start over** / **New message** clears the conversation.

## Troubleshooting

- **`ERROR:` in the proposal area** — the API call failed; check the key, network, and model name in `logic.py`.  
- **Missing key** — ensure `.env` exists and contains `OPENAI_API_KEY`, or set the variable in your environment.
