# Ai-doc

Court document field extraction with a local LLM, plus a Next.js UI.

Extracts 8 fields (`applicant_name`, `case_number`, `respondent_name`,
`lawyer_name`, `court_name`, `case_type`, `filing_date`, `address`) from
court DOCX files using an Ollama model, normalizes/validates them,
evaluates against ground-truth labels, and stores results in MongoDB.

## Structure

```
api/       FastAPI backend wrapping the pipeline in src/
src/       Python pipeline (reader, normalize, validate, database)
data/      Synthetic court document dataset (documents, labels, output)
web/       Next.js UI (JavaScript, Tailwind)
```

## Setup

```bash
# Python backend deps
python3 -m venv .venv
.venv/bin/pip install -r src/requirements.txt

# Frontend deps
cd web && npm install && cd ..
```

Configure:

- `src/.env` — `MONGODB_URI=...` (MongoDB Atlas connection string)
- `api/.env` — `OLLAMA_MODEL=qwen3:8b` (your preferred model)

### Model modes

The API auto-resolves which model to use on every request:

| Situation | Behavior |
|-----------|----------|
| Configured model installed | Uses it — fully local, nothing leaves your machine |
| Configured model missing, others installed | Falls back to an installed model (may be cloud) |
| Nothing installed / Ollama down | Clear error telling you what to run |

The Extract page shows a chip with the current mode (`local ·` green /
`cloud ·` amber), and every extraction response includes `model_used`.

To go fully local (when you can download ~5 GB):

```bash
bash scripts/pull_model.sh   # pulls OLLAMA_MODEL from api/.env
```

Then restart the API server.

## Run

Terminal 1 — API on port 8000:

```bash
.venv/bin/uvicorn api.main:app --port 8000
```

Terminal 2 — UI on port 3000 (proxies /api to :8000):

```bash
cd web && npm run dev
```

Open http://localhost:3000

- **Extract** — pick a dataset document or upload a .docx, view extracted
  fields, validation warnings, and ground-truth comparison.
- **Evaluate** — batch-run all documents, per-field accuracy vs labels.
- **History** — records saved in MongoDB (`ai_doc.court_cases`).

## API

| Endpoint | Description |
|----------|-------------|
| `GET  /api/health` | Model + DB availability |
| `GET  /api/documents` | List dataset documents |
| `GET  /api/documents/{name}/label` | Ground truth JSON |
| `POST /api/extract` | Extract from dataset doc (`{"filename": "court_001"}`) |
| `POST /api/extract/upload` | Extract from uploaded .docx (multipart) |
| `POST /api/evaluate/{name}` | Extract + compare against label |
| `GET  /api/cases` | Saved records from MongoDB |

Legacy CLI evaluation still works: `.venv/bin/python src/evaluate.py`
