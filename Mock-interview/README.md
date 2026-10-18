# Interview Mock AI

A full-stack mock interview platform: upload a resume + job description + company
name, get back a tailored set of questions (essay / code / verbal), answer them
live on camera with proctoring, and get a scored report at the end.

## Architecture

```
React (Vite)  --->  FastAPI backend  --->  Resume Parser (pdfplumber/docx)
                          |            --->  RAG (rag_service + grounding_service) --- knowledge notes, JD, resume, question bank
                          |                          |
                          |            --->  LLM Engine (Ollama/Llama 3 locally, or OpenAI - questions, scoring, report)
                          |
                     Interview Engine (routers/interview_routes.py)
                          |
                text answers ---- audio answers -> Whisper STT (local or OpenAI) -> transcript
                          |
                    AI Evaluation (per answer) -> Feedback
                          |
                       MySQL     --->  Dashboard + PDF report
```

This maps directly onto the diagram you sketched: the "Text Phase 1 / Voice Phase 2"
split is handled per-question (each question is tagged `essay`, `code`, or `verbal`
and the frontend swaps the input widget accordingly) rather than as two separate
interview modes - that way a single interview can mix all three, which is closer to
how a real interview panel works.

## Project layout

```
backend/
  main.py            FastAPI app, CORS, table creation on startup
  models.py           SQLAlchemy tables: User, Interview, Question, Answer, ProctoringEvent
  schemas.py           Pydantic request/response models
  auth.py               JWT auth (register/login)
  routers/              auth_routes, interview_routes, proctoring_routes, report_routes
  services/              resume_parser, llm_service, stt_service, rag_service, vector_store,
                         grounding_service, pdf_service, question_bank_service, dsa_service
  data/question_bank.json   example "previous years' questions" seed, per company
  data/dsa_questions.json   the fixed DSA list every coding question is picked from
  data/knowledge/        reference notes (OOP, DBMS, OS, networks, DSA, ML, ...) that answers are checked against
  data/chroma/           ChromaDB's folder (created automatically when embeddings are on; safe to delete)
frontend/
  src/pages/            Login, Register, SetupInterview, InterviewRoom, Report, Dashboard
  src/components/        CameraProctor, CodeEditor, VoiceRecorder, QuestionCard, Timer, Navbar
```

## Quick start

**Prerequisites:** Python 3.10+, Node 18+, a running MySQL instance (8.0+), and a model
for the AI parts - either **Ollama running on your own PC (free, no key)** or an OpenAI
API key with credit. See "Running the AI locally" below; the steps in section 2 assume Ollama.

### 1. Database

```bash
mysql -u root -p -e "CREATE DATABASE interview_mock_db;"
```

If `DATABASE_URL` in your `.env` uses a different user/password than `root`/`root`,
update it to match - see `backend/.env.example`. If you hit an auth error mentioning
`caching_sha2_password` right after installing MySQL 8, it means the client library
resolved but your user's auth plugin needs resetting:
`ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root';`

### 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-local.txt   # only for local speech-to-text (STT_PROVIDER=local)

cp .env.example .env            # Windows: copy .env.example .env
# edit .env: set DATABASE_URL (if different) and JWT_SECRET_KEY

python3 init_db.py              # creates tables
python3 check_llm.py --stt      # confirms the model + speech-to-text work (see below)
python3 check_rag.py            # confirms retrieval works - needs no model (see "Stopping hallucinations")
uvicorn main:app --reload --port 8000
```

The first lines uvicorn prints say which model backend and database it picked up
(`[startup] Model backend: ...`) - if something is misconfigured, look there first.

Visit `http://localhost:8000` - you should see `{"status": "ok", ...}`. Interactive
API docs are at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env            # default already points at localhost:8000
npm run dev
```

Visit `http://localhost:5173`, register an account, and start an interview.

## Running the AI locally (Ollama + Llama 3)

Question generation, answer scoring and the final report all go through
`services/llm_service.py`, which can talk to either backend. Switch with one line in
`backend/.env`:

```dotenv
LLM_PROVIDER=ollama      # Llama 3 on your own PC - free, no key
# LLM_PROVIDER=openai    # OpenAI API - needs OPENAI_API_KEY and prepaid credit
```

The frontend doesn't change at all.

**Setup (Windows / macOS / Linux):**

1. Install Ollama from https://ollama.com/download and let it start (on Windows it runs
   in the system tray; otherwise run `ollama serve`).
2. Download a model once:
   ```bash
   ollama pull llama3.1        # 8B, ~4.9 GB download, wants ~8 GB free RAM - best quality here
   ollama pull llama3.2        # 3B, ~2 GB - use this if llama3.1 is too slow or your PC has 8 GB RAM
   ```
   If you pick `llama3.2`, set `OLLAMA_MODEL=llama3.2` in `.env`.
3. Run `python check_llm.py` from `backend/`. It should print `OK - model replied ...`.
   The first call is slow because Ollama is loading the model into memory.

**Speech-to-text for verbal answers** works the same way: `STT_PROVIDER=local` uses
faster-whisper on your CPU (free; install it with `pip install -r requirements-local.txt`;
Windows wheels exist for Python 3.10-3.13). The first run downloads the model
(`WHISPER_MODEL_SIZE=base` is ~150 MB), so run `python check_llm.py --stt` once up
front instead of waiting during your first verbal answer. It also decodes a short test
sound, which catches an incompatible `av` package (the audio decoder faster-whisper uses): `av` 19
breaks it with `open() got an unexpected keyword argument 'metadata_errors'`, so
`requirements-local.txt` keeps `av` between 13 and 18. Set `STT_PROVIDER=openai` to
use hosted Whisper instead.

**Honest expectations for a local model:**

- Speed: on a CPU-only laptop, expect roughly 10-60 seconds to generate the question
  set and several seconds to score each answer. A GPU makes it much faster. Don't
  start a real interview before `check_llm.py` has succeeded once, so the model is
  already downloaded and warm (`OLLAMA_KEEP_ALIVE` keeps it loaded for 30 min).
- Quality: an 8B model writes decent questions but scores more loosely and is less
  consistent than GPT-4-class models. Treat the scores as practice feedback, not a
  precise grade. Small models sometimes return messy JSON; the backend cleans up the
  common cases and retries once. If a model's output is still unusable, question
  generation falls back to the seed question bank, and scoring shows a clear error
  rather than inventing a score.
- Errors are readable: Ollama not running, model not pulled, timeout, or no OpenAI
  credit all come back as a message in the UI telling you what to do next.

Useful `.env` knobs: `OLLAMA_MODEL`, `OLLAMA_NUM_CTX` (4096 is enough), `OLLAMA_TIMEOUT`
(raise it on a slow CPU), `OLLAMA_KEEP_ALIVE`, `OLLAMA_BASE_URL` (if Ollama runs on
another machine), `WHISPER_MODEL_SIZE` (`tiny`/`base`/`small`), `WHISPER_LANGUAGE`.

## Stopping hallucinations (RAG)

A model left alone will happily invent things: a project you never built, a "fact" about
the company, or a confident verdict on whether your answer is technically right. The app
now looks things up first and only lets the model rely on what it found.

**Questions** (`grounding_service.plan_questions`)
- The job description, resume and question bank are split into numbered excerpts
  (`[J1]`, `[R2]`, `[B3]`). The model may only ask about things that appear in them, and
  must say which excerpt each question came from.
- That claim is then *checked*, not trusted: a citation is accepted only if the excerpt
  exists and shares a real term with the question; otherwise the best-matching excerpt is
  found by search; if nothing supports the question it is labelled "General question - no
  source matched". Long resumes/JDs keep their most relevant parts instead of being cut off.
- Every question shows where it came from, with a "Why this question" snippet.
- If the model's output is unusable, the interview falls back to the question bank itself.

**Coding questions come only from your DSA list.** About a third of each interview (at
least one question; none if the interview has a single question) is a coding question, and
every one of them is picked word-for-word from `backend/data/dsa_questions.json` - the 75
questions in 10 topics (arrays, strings, searching and sorting, hashing and two pointers,
linked lists, stacks and queues, recursion, trees, graphs, DP and greedy). They are never
generated from your resume or the job description, the model isn't allowed to ask coding
questions, and previous-year coding questions in the question bank are not used. Each
interview gets different questions spread over different topics, and they show as "From the
DSA practice list". The resume and job description only drive the essay and spoken
questions. To change the list, edit that JSON file (keep each `number` unique) and restart.

**Answers** (`grounding_service.grade_answer`)
- The question is searched against `backend/data/knowledge`. Relevant passages (`[S1]`...)
  are given to the model as the *only* source of truth for technical correctness.
- Citations in the feedback are checked against what was actually retrieved - invented ones
  are stripped. If the model says the passages don't relate to the question, they are not
  shown as the basis for the feedback.
- If nothing relevant is found, the model is told so, must not judge technical facts, and
  the UI says "technical accuracy was not checked against a source" instead of pretending.
- The report PDF lists what each answer was checked against.

**Adding your own notes:** drop `.md`, `.txt` or `.pdf` files into `backend/data/knowledge/`
and restart. In Markdown, start each topic with a `## Heading` and keep it to a few
sentences - one section becomes one retrievable passage. The starter notes are a small
curated set, so the more you add for the company/role you're prepping, the more answers
get checked. `python check_rag.py "your question"` shows what a question retrieves.

**Search:** keyword (BM25) search works out of the box. For better matching on rephrased
questions, pull a small embedding model once - `ollama pull nomic-embed-text` - and it is
blended in automatically (`RAG_EMBEDDINGS=off` disables it). If the model isn't there,
search quietly stays keyword-only and the startup/`check_rag.py` output tells you why.
Relevance cut-offs are `RAG_MIN_COVERAGE` and `RAG_MIN_SIMILARITY` in `.env`.

**Lemmatization, not stemming.** Before matching, every word is reduced to its dictionary
base form with `simplemma`: *scheduling / scheduled / schedules -> schedule*, *queries ->
query*, *indices -> index*, *overridden -> override*. (A stemmer would chop these to
non-words like `schedul` and miss the irregular ones.) The same function runs on your
notes and on the question, so they always meet. `simplemma` is a small pure-Python
package: no model, no download. Common tech acronyms are handled by hand (`APIs -> api`,
`OOPs -> oop`, `ML`, `AWS` and `pandas` are left alone). `python check_rag.py --words
"scheduling APIs queries"` shows what any word becomes. Odd lemmas such as `spans -> spin`
are harmless because both sides use the same function.

**Where the vectors live (ChromaDB).** When embeddings are on, each knowledge passage's
text and vector are stored on disk in ChromaDB, in `backend/data/chroma/` (a `chroma.sqlite3`
file plus an index folder) - not held in memory. Passages are only embedded once: restart
the server and nothing is re-embedded; edit one note and only that passage is re-embedded;
remove a note and its vectors are deleted. Each embedding model gets its own collection, so
switching models never mixes vectors. Set `RAG_CHROMA_PATH` in `.env` to keep it elsewhere.
The folder is generated from `data/knowledge`: if you delete it (with the server stopped),
it is rebuilt on the next search. What still sits in memory is only the keyword (BM25)
index and the passage list, rebuilt from your notes in a moment on every start. The job
description and resume are split per interview and are not stored in ChromaDB.
If ChromaDB or the embedding model can't be used, search quietly stays keyword-only.

**What this does and doesn't do:**
- It reduces made-up content a lot; it can't make a small local model perfectly obedient.
  A model can still misread a passage or ignore a rule, which is why citations and question
  sources are verified in code rather than taken on trust.
- A passage is only as good as your notes. "Checked against a source" means checked against
  *that note*, not against the truth.
- Code answers aren't run, so correctness of code is judged by reading it. The model is
  told not to claim it ran or tested anything.
- The question bank is illustrative (see below), so a "From the question bank" label does
  not mean the company really asked it.

## If you're short on time

Getting every piece running (MySQL + two installs + an API key) takes real
setup time, so if you're doing this against a deadline, this is the order that
gets you to a working demo fastest:

1. **Backend first, alone.** Get `uvicorn main:app` running and hit `/docs` in the
   browser - you can create a user, start an interview, and submit answers entirely
   from the Swagger UI before the frontend even exists. This proves the whole
   LLM/DB pipeline works independently of any frontend bugs.
2. **Frontend without the camera.** `CameraProctor` fails gracefully if camera
   permission is denied (it just shows an inline error and the interview still
   works) - so if `getUserMedia` misbehaves on the demo machine, the core Q&A flow
   is unaffected.
3. **Proctoring last.** It's the flashiest part but also the most dependent on
   things outside your control (camera permissions, the demo room's lighting, an
   external model CDN - see below). Get the resume-to-questions-to-report loop
   solid first, then layer this on.
4. A fresh MySQL + `.env` you configured yourself is a much safer demo than one
   you're SSH'd into last-minute - if you're tight on time, `sqlite` is a one-line
   swap in `database.py` (`DATABASE_URL=sqlite:///./dev.db`, drop `mysql-connector-python`)
   and skips the MySQL install entirely for local testing.

## Real-time, honestly

Two places where "real-time" means something slightly different than continuous
streaming, so there are no surprises during a demo or a design walkthrough:

- **Proctoring is genuinely real-time.** The camera feed is analyzed in-browser
  every second the whole time you're on the interview screen, and the warning
  appears the moment your face has been out of frame for ~3 seconds - no server
  round trip involved.
- **Voice answers are near-real-time, not streamed.** You record an answer, and
  transcription + scoring happen in one call after you stop speaking - not word-by-word
  as you talk. True streaming transcription (via a WebSocket to Whisper or a local
  streaming STT model) is a reasonable next step, but is a meaningfully bigger
  lift than this scaffold, so it's called out here rather than silently skipped.

## Proctoring models

`CameraProctor.jsx` loads its face-detection model from
`https://justadudewhohacks.github.io/face-api.js/models` (the library author's own
hosted demo weights) so there's nothing to download to get started. For an offline
or production setup, download the `tiny_face_detector` weight files into
`frontend/public/models` and change `MODEL_URL` in that file to `"/models"`.

## Expanding the question bank

`backend/data/question_bank.json` ships with a handful of illustrative example
questions per company (including Zensar, since that's what you mentioned prepping
for) - they're a style reference for the LLM prompt, not verified real leaks. Swap
in real questions you collect (GeeksforGeeks interview-experience threads, LeetCode
Discuss, Glassdoor, seniors who've interviewed there) and the generator will lean on
them more usefully. Company matching is a case-insensitive substring match on
whatever you type into the "Company" field, falling back to a `"generic"` bucket.

## What's not built

Being upfront about the edges of this scaffold:

- No password reset / email verification - register/login only.
- No retry/backoff around the model calls beyond one retry on unreadable JSON - a
  transient API error surfaces as a message to the user rather than auto-retrying.
- Audio answers are stored on disk (`backend/uploads/audio/`) but not replayed
  anywhere in the report UI beyond the in-session preview.
- No automated test suite in the repo. The Ollama/OpenAI integration and the RAG layer were
  exercised end-to-end against a mock model server (register -> interview -> answers ->
  report/PDF, plus messy-JSON, model-missing, timeout, no-credit, invented-citation,
  embedding-fallback, ChromaDB-storage/incremental-update and lemmatization cases). They
  have not been run against a real Llama 3 or a real `nomic-embed-text` here, so output
  quality - and whether the default embedding similarity cut-off (`RAG_MIN_SIMILARITY`)
  suits your model - is yours to judge. ChromaDB was only run on Linux here; I couldn't
  test a Windows install. If `pip install -r requirements.txt` fails on `chromadb`, remove
  that line and set `RAG_EMBEDDINGS=off` - keyword search still works without it.
- The code editor is a styled `<textarea>`, not a real syntax-highlighting editor -
  swap in `@monaco-editor/react` or CodeMirror if you want that; `CodeEditor.jsx`
  is a self-contained component so nothing else needs to change.
