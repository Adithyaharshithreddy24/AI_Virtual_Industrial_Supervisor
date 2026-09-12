# AI Industrial Virtual Supervisor

FastAPI backend and React frontend for industrial issue reporting. Workers can submit text or voice reports. The system stores the conversation, searches manuals with RAG, gives safe troubleshooting guidance, and calls the assigned technician when operator-level resolution is not safe.

## Architecture

- `Backend/app/api/` - FastAPI routes
- `Backend/app/services/` - supervisor, audio, Sarvam, speech, and Twilio services
- `Backend/app/rag/` - manual ingestion and retrieval
- `Backend/app/repositories/` - MongoDB persistence
- `Frontend/src/` - React worker and manager dashboards

## Requirements

- Python 3.11+
- Node.js and npm
- FFmpeg for audio conversion
- MongoDB Atlas or a reachable MongoDB instance
- Ollama for the local LLM path, or a Google Gemini API key
- Sarvam API key for transcription, translation, and speech
- Twilio account for technician calls

On macOS:

```bash
brew install ffmpeg ollama
```

## Backend setup

From the repository root:

```bash
cd Backend
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

This project also works with `uv` when the virtual environment does not include pip:

```bash
uv pip install --python .venv/bin/python -r requirements.txt
```

## Ollama setup

Start Ollama in another terminal:

```bash
ollama serve
```

Pull the local tool-capable model:

```bash
ollama pull qwen3:4b
```

The working local configuration is:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b
```

`gemma3:1b` is available for simple local generation, but it does not support the tools required by RAG and technician escalation. Use `qwen3:4b` for the complete supervisor flow.

To use Gemini instead:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.6-flash
GOOGLE_API_KEY=your_google_api_key
```

## Environment configuration

Create the environment file:

```bash
cp .env.example .env
```

Set these values in `Backend/.env`:

```env
PORT=8000
MONGODB_URI=your_mongodb_uri
MONGODB_DATABASE=ai_industrial_supervisor
SARVAM_API_KEY=your_sarvam_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=your_twilio_number
PUBLIC_BACKEND_URL=https://your-public-https-url
```

Do not commit `.env` or API keys.

## Twilio Trial mode

Trial accounts can call only verified destination numbers. Configure:

```env
TWILIO_TRIAL_MODE=true
TWILIO_TRIAL_VERIFIED_NUMBER=+917815805576
TWILIO_CALL_URL=
```

Leave `TWILIO_CALL_URL` empty to use the project's localized TwiML endpoint. The backend sends the assigned technician's message and language through the public URL. Verify the destination number in the Twilio Console before testing.

`PUBLIC_BACKEND_URL` must be reachable from Twilio. For local development, run:

```bash
ngrok http 8000
```

Copy the HTTPS forwarding URL into `PUBLIC_BACKEND_URL` and keep ngrok running.

## Add manuals

Put PDF manuals in:

```text
Backend/data/pdfs/
```

Ingest them after the backend environment is configured:

```bash
cd Backend
.venv/bin/python -c "from app.rag.ingestion import run_ingestion; print(run_ingestion())"
```

## Run the backend

```bash
cd Backend
.venv/bin/python run.py
```

The API runs at `http://localhost:8000`. OpenAPI documentation is available at:

```text
http://localhost:8000/docs
```

## Run the frontend

In a second terminal:

```bash
cd Frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and uses:

```env
VITE_BACKEND_URL=http://localhost:8000
```

## Main workflow

1. A manager creates worker and technician accounts and selects a language for each account.
2. A manager creates a machine and assigns a technician.
3. A worker selects a machine and reports an issue by text or voice.
4. Voice input is converted and translated by Sarvam.
5. The supervisor searches manuals when needed and returns safe operator-level guidance.
6. Unsafe or unresolved issues call the technician assigned to that machine, using the technician's language.
7. The issue, decision, call information, and full conversation are stored in MongoDB.
8. Workers can reopen issue history and play supervisor replies with the speaker control.

## Useful endpoints

```text
GET  /api/v1/
GET  /api/v1/health
POST /api/v1/auth/login
POST /api/v1/issues/analyze
POST /api/v1/voice/analyze
GET  /api/v1/voice/synthesize?text=...&language_code=hi-IN
POST /api/v1/manuals/ingest
POST /api/v1/technicians/call
GET  /api/v1/telephony/twiml
POST /api/v1/telephony/status
```

## Validation

Backend syntax check:

```bash
cd Backend
.venv/bin/python -m compileall -q app
```

Frontend production build:

```bash
cd Frontend
npm run build
```

Never test technician escalation with an unverified or production number. A supervisor escalation can create a real phone call.
