import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make the existing pipeline modules in src/ importable
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import database
from .pipeline import (
    DATASET_DIR,
    MODEL,
    compare_with_label,
    docx_source,
    load_label,
    model_status,
    resolve_model,
    run_extraction,
    save_output,
)


app = FastAPI(title="Ai-doc API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractRequest(BaseModel):
    filename: str


def safe_name(name: str) -> str:
    """Strip any path parts from a document name."""

    clean = Path(name).name

    if not clean or clean.startswith("."):
        raise HTTPException(status_code=400, detail="Invalid document name")

    return clean


def try_db_save(name: str, fields: dict, warnings: list) -> tuple[bool, str]:
    """Best-effort save to MongoDB. Never raises."""

    record = {
        "filename": name,
        "fields": fields,
        "warnings": warnings,
        "model": resolve_model()[0],
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        database.save_case(record)
        return True, None
    except Exception as exc:
        return False, str(exc)


def extraction_error(exc: Exception) -> HTTPException:
    """Turn pipeline exceptions into actionable 502s."""

    message = str(exc)

    if "not found" in message.lower() and "model" in message.lower():
        return HTTPException(
            status_code=502,
            detail=(
                f"{message}. The configured model is not installed — "
                f"run: ollama pull {MODEL}"
            ),
        )

    return HTTPException(status_code=502, detail=f"Extraction failed: {exc}")


def extract_and_respond(name: str, source) -> dict:
    """Shared pipeline for dataset and uploaded documents."""

    try:
        prediction, warnings = run_extraction(source)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Model returned invalid JSON: {exc}"
        )
    except Exception as exc:
        raise extraction_error(exc)

    output_path = save_output(name, prediction)

    db_saved, db_error = try_db_save(name, prediction, warnings)

    label = load_label(name)

    return {
        "filename": name,
        "model_used": resolve_model()[0],
        "fields": prediction,
        "warnings": warnings,
        "db_saved": db_saved,
        "db_error": db_error,
        "label": label,
        "output_path": output_path,
    }


@app.get("/api/health")
def health():
    """Report model and database availability."""

    status = model_status()

    db_ok = True
    db_error = None

    try:
        database.get_collection().database.client.admin.command("ping")
    except Exception as exc:
        db_ok = False
        db_error = str(exc)

    return {
        "status": "ok",
        **status,
        "db_ok": db_ok,
        "db_error": db_error,
    }


@app.get("/api/documents")
def list_documents():
    """List dataset documents with label/output availability."""

    documents_dir = DATASET_DIR / "documents"
    labels_dir = DATASET_DIR / "labels"
    output_dir = DATASET_DIR / "output"

    items = []

    for path in sorted(documents_dir.glob("*.docx")):
        name = path.stem
        items.append(
            {
                "name": name,
                "has_label": (labels_dir / f"{name}.json").exists(),
                "has_output": (output_dir / f"{name}.json").exists(),
            }
        )

    return {"documents": items}


@app.get("/api/documents/{name}/label")
def get_label(name: str):
    """Return the ground-truth label for a document."""

    label = load_label(safe_name(name))

    if label is None:
        raise HTTPException(status_code=404, detail="Label not found")

    return label


@app.post("/api/extract")
def extract(request: ExtractRequest):
    """Run the extraction pipeline on a dataset document."""

    name = safe_name(request.filename)
    source = docx_source(name=name)

    if not Path(source).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {name}"
        )

    return extract_and_respond(name, source)


@app.post("/api/extract/upload")
async def extract_upload(file: UploadFile = File(...)):
    """Run the extraction pipeline on an uploaded .docx file."""

    filename = file.filename or ""

    if not filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    name = safe_name(Path(filename).stem)

    contents = await file.read()

    return extract_and_respond(name, docx_source(file_bytes=contents))


@app.post("/api/evaluate/{name}")
def evaluate(name: str):
    """Extract one document and compare against its ground-truth label."""

    name = safe_name(name)
    source = docx_source(name=name)

    if not Path(source).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {name}"
        )

    label = load_label(name)

    if label is None:
        raise HTTPException(
            status_code=404,
            detail=f"No ground-truth label for: {name}"
        )

    try:
        prediction, warnings = run_extraction(source)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Model returned invalid JSON: {exc}"
        )
    except Exception as exc:
        raise extraction_error(exc)

    comparison = compare_with_label(prediction, label)

    db_saved, db_error = try_db_save(name, prediction, warnings)

    return {
        "filename": name,
        "model_used": resolve_model()[0],
        "prediction": prediction,
        "warnings": warnings,
        "db_saved": db_saved,
        "db_error": db_error,
        **comparison,
    }


@app.get("/api/cases")
def cases(limit: int = 100):
    """List saved cases from MongoDB. Fails soft when unreachable."""

    try:
        return {"cases": database.list_cases(limit=limit), "error": None}
    except Exception as exc:
        return {"cases": [], "error": str(exc)}
